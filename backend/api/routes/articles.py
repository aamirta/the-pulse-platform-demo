"""Articles / news API routes."""

from datetime import UTC, datetime
from typing import Any, cast

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from backend.api.common import apply_search_filter, or_404, split_tags
from backend.api.deps import AdminUserDep, get_db
from backend.api.limiter import limiter
from backend.core.config import settings
from backend.models import Article
from backend.schemas import (
    ArticleCreate,
    ArticleDetail,
    NewsItem,
    PaginatedResponse,
)

router = APIRouter(prefix="/articles", tags=["articles"])

# Columns a client may sort articles by.
ARTICLE_SORT_COLUMNS = {"published_at", "created_at", "title", "category", "article_id"}


# The article catalogue is categorised in French ("Actualité", "Analyse",
# "Interview"), while the UI navigates by English intent (news / blog / funding /
# event). These markers bridge the two so the Blog view has a real data source
# instead of silently showing the unfiltered news list.
ARTICLE_TYPE_MARKERS: dict[str, tuple[str, ...]] = {
    "funding": ("funding", "fundraising", "levée", "levee", "investissement"),
    "event": ("event", "évén", "even", "rencontre"),
    "blog": ("blog", "analyse", "interview", "opinion", "tribune", "édito", "edito"),
    "news": ("news", "actualit", "presse"),
}

# Checked in order; the first match wins, so "blog" is resolved before "news".
_TYPE_PRIORITY = ("funding", "event", "blog", "news")


def _article_type(category: str | None) -> str:
    """Map an article category to the frontend news type."""
    if not category:
        return "news"
    category_lower = category.lower()
    for article_type in _TYPE_PRIORITY:
        if any(marker in category_lower for marker in ARTICLE_TYPE_MARKERS[article_type]):
            return article_type
    return "news"


def _type_filter(article_type: str) -> Any:
    """Build an OR filter matching a UI type against the French categories."""
    from sqlalchemy import or_

    markers = ARTICLE_TYPE_MARKERS.get(article_type.strip().lower())
    if not markers:
        return None
    return or_(*[Article.category.ilike(f"%{marker}%") for marker in markers])


def _format_date(value: Any) -> str:
    """Format a datetime as a human-readable string."""
    if not value:
        return ""
    dt = cast(datetime, value)
    now = datetime.now(UTC)
    diff = now - dt.replace(tzinfo=UTC)
    if diff.days <= 0:
        return "Aujourd'hui"
    if diff.days == 1:
        return "Hier"
    if diff.days < 7:
        return f"Il y a {diff.days}j"
    if diff.days < 30:
        return f"Il y a {diff.days // 7}sem"
    return dt.strftime("%d %b %Y")


def _to_news_item(article: Article) -> NewsItem:
    """Map an Article ORM instance to a frontend NewsItem."""
    description = article.summary or (article.content[:200] + "..." if article.content else "")
    return NewsItem(
        id=str(article.article_id),
        type=_article_type(article.category),
        title=article.title,
        description=description,
        source=article.source or article.author or "The Pulse",
        sourceAvatar="/avatars/pulse.jpg",
        date=_format_date(article.published_at or article.created_at),
        publishedAt=cast(Any, article.published_at or article.created_at),
        image=article.image_url or "",
        tags=split_tags(article.tags),
        amount=None,
        round=None,
        eventDate=None,
    )


@router.get(
    "/",
    response_model=PaginatedResponse[NewsItem],
    summary="List news articles",
    description="Paginated list of news articles with optional filtering by category, search, and featured flag.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def list_articles(
    request: Request,
    db: Session = Depends(get_db),
    category: str | None = None,
    type: str | None = Query(
        None, description="UI intent: news, blog, funding or event"
    ),
    search: str | None = None,
    is_featured: bool | None = None,
    sort_by: str = Query("published_at", description="Column to sort by"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE),
) -> PaginatedResponse[NewsItem]:
    """Return a paginated list of news articles."""
    query = db.query(Article)
    if category:
        query = query.filter(Article.category.ilike(f"%{category}%"))
    if type:
        # The SPA links to /news?type=blog; without this the parameter was
        # ignored and the Blog view returned the whole unfiltered feed.
        type_filter = _type_filter(type)
        if type_filter is not None:
            query = query.filter(type_filter)
    if is_featured is not None:
        query = query.filter(Article.is_featured == is_featured)
    if search:
        query = apply_search_filter(
            query, Article, search, "title", "content", "summary", "source", "author"
        )

    # Whitelisted so a client cannot order by an arbitrary model attribute.
    sort_column = getattr(Article, sort_by if sort_by in ARTICLE_SORT_COLUMNS else "published_at")
    query = query.order_by(desc(sort_column).nullslast() if order == "desc" else asc(sort_column))
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(
        items=[_to_news_item(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


@router.get(
    "/{article_id}",
    response_model=ArticleDetail,
    summary="Article detail",
    description="Return detailed information for a single article.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def get_article(request: Request, article_id: int, db: Session = Depends(get_db)) -> ArticleDetail:
    """Return a single article by ID."""
    article = or_404(db.query(Article).filter(Article.article_id == article_id).first())
    return ArticleDetail.model_validate(article)


@router.post(
    "/",
    response_model=ArticleDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create article",
    description="Create a new article (admin only).",
)
@limiter.limit("10/minute")
def create_article(
    request: Request,
    data: ArticleCreate,
    admin: AdminUserDep,
    db: Session = Depends(get_db),
) -> ArticleDetail:
    """Create a new article."""
    article = Article(
        title=data.title,
        content=data.content,
        summary=data.summary,
        category=data.category,
        source=data.source,
        source_url=data.source_url,
        author=data.author or admin.username,
        image_url=data.image_url,
        tags=data.tags,
        is_featured=data.is_featured,
        published_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return ArticleDetail.model_validate(article)
