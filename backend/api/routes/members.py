"""Members / community API routes."""

from datetime import datetime
from io import BytesIO
from typing import Any, cast

from badge_generator import generate as generate_badge_image
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import asc, case, desc, func
from sqlalchemy.orm import Session

from backend.api.common import apply_search_filter, or_404
from backend.api.deps import (
    AdminUserDep,
    OptionalUserOrMemberDep,
    UserOrMemberDep,
    get_db,
)
from backend.api.limiter import limiter
from backend.core.config import settings
from backend.core.email import send_confirmation_email
from backend.core.security import generate_confirmation_token, generate_secure_token, hash_password
from backend.models import (
    BadgeGeneration,
    DirectMessage,
    Expert,
    Founder,
    Incubator,
    Investor,
    MemberEntityLink,
    Post,
    PostComment,
    PostLike,
    PulseMember,
    Startup,
    User,
)
from backend.schemas import (
    ConversationPartner,
    ConversationReply,
    ConversationThreadResponse,
    DirectMessageCreate,
    DirectMessageResponse,
    EntityContact,
    MemberOnboardRequest,
    MemberOnboardResponse,
    MessageSearchHit,
    PaginatedResponse,
    PostCommentCreate,
    PostCommentItem,
    PostCreate,
    PostDetail,
    PostItem,
    PostLikeItem,
    PulseMemberCreate,
    PulseMemberDetail,
    PulseMemberPublicItem,
    PulseMemberUpdate,
    StartConversationRequest,
    StartConversationResponse,
)

router = APIRouter(prefix="/members", tags=["members"])


def _is_owner_or_admin(
    current_user: User | None,
    current_member: PulseMember | None,
    member: PulseMember,
) -> bool:
    """Return True if the current user is admin or the member owns the record."""
    if current_user and current_user.username == settings.ADMIN_USERNAME:
        return True
    return bool(current_member and current_member.id == member.id)


def _to_member_detail(member: PulseMember) -> PulseMemberDetail:
    """Map a PulseMember to the detail schema."""
    return PulseMemberDetail.model_validate(member)


# Columns a client may sort members by. Anything outside this set — notably
# password_hash, reset_token and confirmation_token — would turn ORDER BY into
# an oracle for guessing secrets one character at a time.
MEMBER_SORT_COLUMNS = {"created_at", "full_name", "role", "id"}


def _member_sort_clause(sort_by: str, order: str) -> Any:
    """Return a safe ORDER BY clause for member queries."""
    column_name = sort_by if sort_by in MEMBER_SORT_COLUMNS else "created_at"
    column = getattr(PulseMember, column_name)
    return desc(column) if order == "desc" else asc(column)


@router.get(
    "/",
    response_model=PaginatedResponse[PulseMemberPublicItem],
    summary="List members",
    description=(
        "Paginated public directory of confirmed community members. "
        "Contact details are not exposed; administrators use /admin/members for the full record."
    ),
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def list_members(
    request: Request,
    db: Session = Depends(get_db),
    role: str | None = None,
    search: str | None = None,
    sort_by: str = Query("created_at", description="Column to sort by"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE),
) -> PaginatedResponse[PulseMemberPublicItem]:
    """Return the public, paginated community member directory.

    This endpoint is unauthenticated, so it only ever exposes confirmed members
    through :class:`PulseMemberPublicItem` and never searches or sorts on
    columns holding contact details or secrets.
    """
    query = db.query(PulseMember).filter(PulseMember.is_confirmed.is_(True))
    if role:
        query = query.filter(PulseMember.role.ilike(f"%{role}%"))
    if search:
        query = apply_search_filter(query, PulseMember, search, "full_name", "role")

    query = query.order_by(_member_sort_clause(sort_by, order))
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(
        items=[PulseMemberPublicItem.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


_BADGE_CATEGORIES = {
    "entrepreneur",
    "startup",
    "investisseur",
    "vc",
    "amic",
    "président",
    "president",
    "programme",
    "incubateur",
    "accelerateur",
    "accélérateur",
    "talent",
    "professionnel",
    "expert",
    "mentor",
    "venture_studio",
    "venture studio",
    "studio",
}


def _initials(full_name: str) -> str:
    parts = [p for p in full_name.strip().split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][0].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def _generate_initials_avatar(full_name: str, size: int = 400) -> BytesIO:
    """Create a circular avatar with the user's initials as a fallback photo."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((0, 0, size, size), fill=(7, 11, 18, 255))
    initials = _initials(full_name)
    # Use a default font; scale roughly by size
    try:
        font: ImageFont.FreeTypeFont | ImageFont.ImageFont = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size // 2)
    except Exception:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), initials, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (size - text_w) // 2 - bbox[0]
    y = (size - text_h) // 2 - bbox[1]
    draw.text((x, y), initials, font=font, fill=(238, 242, 255, 255))
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def _validate_badge_ref_url(ref_url: str | None) -> str | None:
    if not ref_url:
        return None
    from urllib.parse import urlparse

    parsed = urlparse(ref_url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ref_url must be an HTTP/HTTPS URL",
        )
    return ref_url[:500]


@router.post(
    "/badge",
    summary="Generate member badge",
    description="Generate a PNG badge for the authenticated member or with the provided data. Returns the image as an attachment.",
)
@limiter.limit("10/minute")
def generate_member_badge(
    request: Request,
    full_name: str = Form(..., max_length=150),
    role_label: str = Form(..., max_length=100),
    category: str = Form(..., max_length=50),
    ref_url: str | None = Form(None, max_length=500),
    photo: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    user_or_member: UserOrMemberDep = (None, None),
) -> StreamingResponse:
    """Generate a PNG badge, audit the event, and return the image."""
    current_user, current_member = user_or_member
    if not current_user and not current_member:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    category_clean = category.strip().lower()
    if category_clean not in _BADGE_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid badge category: {category}",
        )

    full_name_clean = full_name.strip()[:150]
    role_label_clean = role_label.strip()[:100]
    ref_url_clean = _validate_badge_ref_url(ref_url)

    # Determine photo source
    photo_stream: BytesIO
    if photo is not None:
        if photo.content_type not in ("image/png", "image/jpeg", "image/jpg", "image/webp"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Photo must be a PNG, JPEG, or WebP image",
            )
        contents = photo.file.read()
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Photo must be smaller than 5MB",
            )
        photo_stream = BytesIO(contents)
    else:
        photo_stream = _generate_initials_avatar(full_name_clean)

    try:
        badge_buf = generate_badge_image(
            photo_stream,
            full_name=full_name_clean,
            role=role_label_clean,
            category=category_clean,
            ref_url=ref_url_clean,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate badge",
        ) from exc

    # Audit the generation event

    audit = BadgeGeneration(
        member_id=current_member.id if current_member else None,
        full_name=full_name_clean,
        category=category_clean,
        role_label=role_label_clean,
        ref_url=ref_url_clean,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        created_at=datetime.utcnow(),
    )
    db.add(audit)
    db.commit()

    filename = f"badge_{full_name_clean.replace(' ', '_').replace('/', '_')[:30]}.png"
    return StreamingResponse(
        badge_buf,
        media_type="image/png",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post(
    "/",
    response_model=PulseMemberDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create member",
    description=(
        "Create a community member record without a password (admin invite flow). "
        "Self-service registration goes through POST /members/onboard."
    ),
)
@limiter.limit("10/minute")
def create_member(
    request: Request,
    data: PulseMemberCreate,
    admin: AdminUserDep,
    db: Session = Depends(get_db),
) -> PulseMemberDetail:
    """Create a passwordless community member record (admin only).

    Left unauthenticated this endpoint let anyone inject arbitrary members into
    the directory; self-registration is handled by ``/members/onboard``, which
    requires a password and issues a confirmation token.
    """
    existing = db.query(PulseMember).filter(PulseMember.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A member with this email already exists",
        )
    member = PulseMember(
        email=data.email,
        full_name=data.full_name,
        role=data.role,
        profile_pic=data.profile_pic,
        linkedin=data.linkedin,
        form_data=data.form_data,
        confirmation_token=generate_confirmation_token(),
        is_confirmed=False,
        created_at=datetime.utcnow(),
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return _to_member_detail(member)


@router.get(
    "/newsfeed",
    response_model=PaginatedResponse[PostItem],
    summary="Community newsfeed",
    description="Return the public community newsfeed posts.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def newsfeed(
    request: Request,
    db: Session = Depends(get_db),
    actor: OptionalUserOrMemberDep = (None, None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE),
) -> PaginatedResponse[PostItem]:
    """Return the public community newsfeed.

    Anonymous visitors get the plain public list. A signed-in caller also gets
    ``liked_by_me`` per post, resolved in one extra query, so the client can
    render the correct state without asking for every post individually — the
    list deliberately does not carry the full ``likes`` array.
    """
    query = db.query(Post).filter(Post.is_published.is_(True)).order_by(desc(Post.created_at))
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    liked_ids: set[int] = set()
    current_user, current_member = actor
    if items and (current_user or current_member):
        actor_type = "member" if current_member else "user"
        actor_id = current_member.id if current_member else current_user.user_id  # type: ignore[union-attr]
        liked_ids = {
            row[0]
            for row in db.query(PostLike.post_id).filter(
                PostLike.post_id.in_([p.post_id for p in items]),
                PostLike.actor_type == actor_type,
                PostLike.actor_id == actor_id,
            )
        }

    posts: list[PostItem] = []
    for post in items:
        item = PostItem.model_validate(post)
        item.liked_by_me = post.post_id in liked_ids
        posts.append(item)

    return PaginatedResponse(
        items=posts,
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


@router.post(
    "/newsfeed",
    response_model=PostItem,
    status_code=status.HTTP_201_CREATED,
    summary="Create newsfeed post",
    description="Create a new community newsfeed post. Authenticated actors only.",
)
@limiter.limit("10/minute")
def create_post(
    request: Request,
    data: PostCreate,
    db: Session = Depends(get_db),
    user_or_member: UserOrMemberDep = (None, None),
) -> PostItem:
    """Create a new community post."""
    current_user, current_member = user_or_member
    if not current_user and not current_member:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    actor_name = current_member.full_name if current_member else getattr(current_user, "username", "")
    actor_role = current_member.role if current_member else None
    post = Post(
        author_name=data.author_name or actor_name,
        author_role=data.author_role or actor_role,
        content=data.content,
        post_type=data.post_type,
        image_url=data.image_url,
        link_url=data.link_url,
        link_title=data.link_title,
        tags=data.tags,
        is_published=True,
        created_at=datetime.utcnow(),
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return PostItem.model_validate(post)


@router.post(
    "/messages",
    response_model=DirectMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send direct message",
    description="Send a direct message to another community member. Sender identity is derived from the authenticated actor when not provided.",
)
@limiter.limit("10/minute")
def send_message(
    request: Request,
    data: DirectMessageCreate,
    db: Session = Depends(get_db),
    user_or_member: UserOrMemberDep = (None, None),
) -> DirectMessageResponse:
    """Create a direct message scoped to the authenticated actor."""
    current_user, current_member = user_or_member
    if not current_user and not current_member:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    actor_name = current_member.full_name if current_member else getattr(current_user, "username", "")
    actor_email = _get_actor_email(current_user, current_member)
    recipient_email = data.to_email.strip().lower()
    if recipient_email == actor_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send a message to yourself",
        )
    # The recipient must be a real account. Without this the endpoint accepts any
    # address, which is how the Flask original could be used to send anywhere.
    recipient = _resolve_recipient(db, recipient_email)

    message = DirectMessage(
        post_id=data.post_id,
        # The display name is taken from the recipient's profile rather than the
        # request body, so a sender cannot mislabel who they wrote to.
        to_name=recipient.full_name,
        to_email=recipient_email,
        from_name=actor_name,
        from_email=actor_email,
        message=data.message,
        is_read=False,
        created_at=datetime.utcnow(),
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return DirectMessageResponse.model_validate(message)


@router.get(
    "/messages",
    response_model=PaginatedResponse[DirectMessageResponse],
    summary="List direct messages",
    description="List all direct messages (admin only).",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def list_messages(
    request: Request,
    admin: AdminUserDep,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE),
) -> PaginatedResponse[DirectMessageResponse]:
    """Return all direct messages."""
    query = db.query(DirectMessage).order_by(desc(DirectMessage.created_at))
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(
        items=[DirectMessageResponse.model_validate(m) for m in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


def _parse_form_data(data: MemberOnboardRequest) -> dict[str, Any]:
    """Return form_data as a dict, defaulting to empty."""
    return data.form_data or {}


def _map_onboarding_to_entities(
    db: Session,
    member: PulseMember,
    data: MemberOnboardRequest,
) -> None:
    """Create a minimal directory record based on the member's role/form data."""
    import json

    form = _parse_form_data(data)
    role = (data.role or "").lower()

    if "startup" in role or "entrepreneur" in role:
        startup = Startup(
            startup_name=form.get("startup_name") or form.get("company_name") or data.full_name,
            contact_email=data.email,
            sector=form.get("sector") or form.get("industry"),
            stage=form.get("stage") or form.get("startup_stage"),
            location=form.get("location") or form.get("city"),
            description=form.get("description") or form.get("bio"),
            homepage_url=form.get("website") or form.get("homepage_url"),
            linkedin=data.linkedin or form.get("linkedin"),
            logo_url=data.profile_pic or form.get("logo_url"),
        )
        db.add(startup)

    elif "founder" in role:
        names = data.full_name.strip().split()
        founder = Founder(
            founder_id=generate_secure_token(),
            # The link back to the account. Set here because this is the one
            # moment the identity is *known* rather than guessed: the row is
            # being built from this member's own details. Without it the
            # profile page has no way to tell whose it is.
            member_id=member.id,
            name=data.full_name,
            first_name=form.get("first_name") or (names[0] if names else None),
            last_name=form.get("last_name") or (names[-1] if names else None),
            current_title=form.get("title") or form.get("current_title"),
            current_employer=form.get("company") or form.get("current_employer"),
            location=form.get("location") or form.get("city"),
            linkedin_url=data.linkedin or form.get("linkedin"),
            profile_pic=data.profile_pic or form.get("profile_pic"),
            skills=form.get("skills") or form.get("expertise"),
        )
        db.add(founder)

    elif "investor" in role or "vc" in role:
        investor = Investor(
            investor_name=form.get("investor_name") or form.get("company_name") or data.full_name,
            hq_email=data.email,
            domain=form.get("website") or form.get("domain"),
            primary_investor_type=form.get("investor_type") or data.role,
            description=form.get("description") or form.get("bio"),
            linkedin_url=data.linkedin or form.get("linkedin"),
            logo_url=data.profile_pic or form.get("logo_url"),
        )
        db.add(investor)

    elif (
        "incubateur" in role
        or "accelerateur" in role
        or "accélérateur" in role
        or "programme" in role
    ):
        incubator = Incubator(
            incubator=form.get("incubator_name") or form.get("organization_name") or data.full_name,
            email=data.email,
            description=form.get("description") or form.get("bio"),
            type_organisme=data.role,
            ville=form.get("city") or form.get("location"),
            linkedin=data.linkedin or form.get("linkedin"),
            image_url=data.profile_pic or form.get("image_url"),
        )
        db.add(incubator)

    elif "expert" in role or "mentor" in role:
        # "expert" and "mentor" were accepted roles with no branch here, so the
        # experts table never received a row and the Experts & Mentors directory
        # was permanently empty.
        expert = Expert(
            full_name=data.full_name,
            email=data.email,
            location=form.get("location") or form.get("city"),
            current_title=form.get("title") or form.get("current_title"),
            organization=form.get("organization") or form.get("company"),
            expertise_domain=form.get("expertise_domain") or form.get("domain"),
            years_experience=form.get("years_experience") or form.get("experience"),
            professional_bio=form.get("bio") or form.get("description"),
            skills=form.get("skills") or form.get("expertise"),
            services_offered=form.get("services_offered") or form.get("services"),
            availability=form.get("availability"),
            linkedin_url=data.linkedin or form.get("linkedin"),
            profile_pic=data.profile_pic or form.get("profile_pic"),
        )
        db.add(expert)

    member.form_data = json.dumps(form) if form else None


@router.post(
    "/onboard",
    response_model=MemberOnboardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Onboard a new member",
    description="Register a community member with a password, create a directory record based on role, and send a confirmation email.",
)
@limiter.limit("10/minute")
def onboard_member(
    request: Request,
    data: MemberOnboardRequest,
    db: Session = Depends(get_db),
) -> MemberOnboardResponse:
    """Create a new PulseMember, map role data to entity tables, and queue confirmation."""
    email = data.email.strip().lower()
    existing = db.query(PulseMember).filter(PulseMember.email == email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A member with this email already exists",
        )

    token = generate_confirmation_token()
    member = PulseMember(
        email=email,
        full_name=data.full_name.strip(),
        role=data.role.strip(),
        profile_pic=data.profile_pic,
        linkedin=data.linkedin,
        confirmation_token=token,
        is_confirmed=False,
        password_hash=hash_password(data.password),
        created_at=datetime.utcnow(),
    )
    db.add(member)
    db.flush()  # flush so member.id is available for any FK usage

    _map_onboarding_to_entities(db, member, data)
    db.commit()
    db.refresh(member)

    confirmation_url = send_confirmation_email(member.email, token)
    return MemberOnboardResponse(
        message="Member registered. Please confirm your email.",
        member_id=member.id,
        confirmation_token=token if not confirmation_url else None,
        confirmation_url=confirmation_url,
    )


@router.get(
    "/confirm/{token}",
    summary="Confirm member email",
    description="Confirm a member account using the confirmation token sent by email.",
)
@limiter.limit("10/minute")
def confirm_member(
    request: Request,
    token: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Confirm a member by token."""
    member = db.query(PulseMember).filter(PulseMember.confirmation_token == token).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired confirmation token",
        )
    member.is_confirmed = True
    member.confirmation_token = None
    db.commit()
    db.refresh(member)
    return {"message": "Email confirmed successfully", "member_id": member.id}


def _resolve_recipient(db: Session, email: str) -> PulseMember:
    """Return the member behind an email, or refuse to create the message.

    The Flask inbox wrote whatever address the client supplied, which made
    ``/inbox/reply`` an open relay for sending to arbitrary addresses. A message
    may now only be addressed to an account that actually exists.
    """
    recipient = (
        db.query(PulseMember).filter(func.lower(PulseMember.email) == email).first()
    )
    if recipient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No community member exists with that email address",
        )
    return recipient


def _partner_directory(
    db: Session, emails: list[str], *, public_only: bool = False
) -> dict[str, dict[str, Any]]:
    """Return {email: {name, pic, member_id, expert_id, role}} for conversation partners.

    Restores the avatar and expert lookup the Flask inbox performed, which was
    dropped during the FastAPI migration. Two queries regardless of how many
    partners there are.

    ``public_only`` restricts the lookup to accounts the directory already
    publishes. Callers use it where a hit would otherwise answer "does this
    address have an account here?" for an address the asker has no relationship
    with.
    """
    if not emails:
        return {}

    member_q = db.query(PulseMember).filter(func.lower(PulseMember.email).in_(emails))
    if public_only:
        member_q = member_q.filter(PulseMember.is_confirmed.is_(True))

    directory: dict[str, dict[str, Any]] = {}
    for member in member_q.all():
        key = (member.email or "").strip().lower()
        directory[key] = {
            "name": member.full_name,
            "pic": member.profile_pic,
            "member_id": member.id,
            "expert_id": None,
            "role": member.role,
        }
    for expert in db.query(Expert).filter(func.lower(Expert.email).in_(emails)).all():
        key = (expert.email or "").strip().lower()
        entry = directory.setdefault(
            key,
            {"name": expert.full_name, "pic": expert.profile_pic, "member_id": None, "role": None},
        )
        # An expert profile supplies the id and, when the member has no avatar
        # of their own, the picture.
        entry["expert_id"] = expert.expert_id
        if not entry.get("pic"):
            entry["pic"] = expert.profile_pic
    return directory


def _get_actor_email(current_user: User | None, current_member: PulseMember | None) -> str:
    """Return the email address representing the current actor for inbox scoping."""
    if current_member:
        if not current_member.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Member email is missing",
            )
        return current_member.email.strip().lower()
    if current_user:
        if not current_user.email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email required for inbox access",
            )
        return current_user.email.strip().lower()
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
    )


def _like_needle(term: str) -> str:
    """Return a LIKE pattern that treats the caller's term as literal text.

    Without escaping, a search for ``%`` matches every row and ``_`` matches any
    single character, so a caller could switch the filter off by typing a wildcard.
    """
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped.lower()}%"


def _partner_expression(actor_email: str) -> Any:
    """SQL expression yielding the other end of a message, for this actor."""
    return case(
        (func.lower(DirectMessage.from_email) == actor_email, func.lower(DirectMessage.to_email)),
        else_=func.lower(DirectMessage.from_email),
    )


def _actor_messages(actor_email: str) -> Any:
    """Predicate limiting a message query to rows the actor sent or received.

    Every inbox read composes this, and it is the whole of the isolation
    guarantee. Both sides are case-folded because rows written by the original
    Flask inbox kept whatever casing the client sent, and a thread must not
    fragment on capitalisation.
    """
    return (func.lower(DirectMessage.from_email) == actor_email) | (
        func.lower(DirectMessage.to_email) == actor_email
    )


@router.get(
    "/conversations/unread-count",
    summary="Unread message counter",
    description="Total unread messages for the actor and how many conversations they span.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def unread_count(
    request: Request,
    db: Session = Depends(get_db),
    user_or_member: UserOrMemberDep = (None, None),
) -> dict[str, int]:
    """Return the counters behind the navigation badge.

    Declared before ``/conversations/{partner_email}`` so the literal path wins
    the route match rather than being read as a partner address.
    """
    current_user, current_member = user_or_member
    actor_email = _get_actor_email(current_user, current_member)
    row = (
        db.query(
            func.count(DirectMessage.id),
            func.count(func.distinct(func.lower(DirectMessage.from_email))),
        )
        .filter(
            func.lower(DirectMessage.to_email) == actor_email,
            DirectMessage.is_read.is_(False),
        )
        .one()
    )
    return {"unread": int(row[0] or 0), "conversations": int(row[1] or 0)}


@router.get(
    "/messages/search",
    response_model=PaginatedResponse[MessageSearchHit],
    summary="Search message text",
    description=(
        "Search across the authenticated actor's own messages. Only messages the actor sent "
        "or received are searched, so a term can never surface someone else's mail."
    ),
)
@limiter.limit(settings.RATE_LIMIT_SEARCH)
def search_messages(
    request: Request,
    db: Session = Depends(get_db),
    user_or_member: UserOrMemberDep = (None, None),
    q: str = Query(..., min_length=2, max_length=120),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE),
) -> PaginatedResponse[MessageSearchHit]:
    """Return the actor's own messages whose body matches ``q``."""
    current_user, current_member = user_or_member
    actor_email = _get_actor_email(current_user, current_member)
    needle = _like_needle(q.strip())

    query = db.query(DirectMessage).filter(
        _actor_messages(actor_email),
        func.lower(DirectMessage.message).like(needle, escape="\\"),
    )
    total = query.count()
    rows = (
        query.order_by(desc(DirectMessage.created_at), desc(DirectMessage.id))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    def partner_of(msg: DirectMessage) -> tuple[bool, str]:
        outgoing = (msg.from_email or "").strip().lower() == actor_email
        return outgoing, ((msg.to_email if outgoing else msg.from_email) or "").strip().lower()

    directory = _partner_directory(db, [partner_of(m)[1] for m in rows if partner_of(m)[1]])

    items: list[MessageSearchHit] = []
    for msg in rows:
        outgoing, partner_email = partner_of(msg)
        profile = directory.get(partner_email, {})
        items.append(
            MessageSearchHit(
                id=msg.id,
                partner_email=partner_email,
                partner_name=profile.get("name") or (msg.to_name if outgoing else msg.from_name),
                partner_pic=profile.get("pic"),
                outgoing=outgoing,
                message=msg.message,
                is_read=bool(msg.is_read),
                created_at=msg.created_at,
            )
        )
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


@router.get(
    "/conversations",
    response_model=list[ConversationPartner],
    summary="List conversation partners",
    description=(
        "Conversation partners for the authenticated actor, with unread counts, last-message "
        "previews and the partner's avatar and profile ids. The optional search term matches a "
        "partner's address and the text of the messages exchanged with them."
    ),
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def list_conversations(
    request: Request,
    db: Session = Depends(get_db),
    user_or_member: UserOrMemberDep = (None, None),
    q: str | None = Query(None, max_length=120, description="Filter by address or message text"),
    unread_only: bool = Query(False, description="Only conversations with unread messages"),
    limit: int = Query(100, ge=1, le=200, description="Maximum conversations to return"),
) -> list[ConversationPartner]:
    """List conversation partners for the current user or member.

    Aggregated in SQL rather than in Python. The previous implementation loaded
    every message the actor had ever exchanged into memory on each request and
    grouped them there, so opening the inbox cost more the longer someone had
    been using it. This runs in three bounded queries regardless of mailbox size.
    """
    current_user, current_member = user_or_member
    actor_email = _get_actor_email(current_user, current_member)
    partner = _partner_expression(actor_email)
    mine = _actor_messages(actor_email)

    unread_case = case(
        (
            (func.lower(DirectMessage.to_email) == actor_email) & DirectMessage.is_read.is_(False),
            1,
        ),
        else_=0,
    )

    summary_q = (
        db.query(
            partner.label("partner"),
            func.count(DirectMessage.id).label("message_count"),
            func.sum(unread_case).label("unread"),
            func.max(DirectMessage.created_at).label("last_at"),
            func.max(DirectMessage.id).label("last_id"),
        )
        .filter(mine, partner.isnot(None))
        .group_by(partner)
    )

    if q and q.strip():
        needle = _like_needle(q.strip())
        # A thread matches when the partner's address matches, or when any
        # message in it does. The second clause is what makes the box searchable
        # by content rather than only by who sent it.
        threads_matching_text = (
            db.query(partner)
            .filter(mine, func.lower(DirectMessage.message).like(needle, escape="\\"))
            .distinct()
        )
        summary_q = summary_q.filter(
            partner.like(needle, escape="\\") | partner.in_(threads_matching_text)
        )

    if unread_only:
        summary_q = summary_q.having(func.sum(unread_case) > 0)

    rows = summary_q.order_by(desc(func.max(DirectMessage.created_at))).limit(limit).all()
    if not rows:
        return []

    # The newest row of each thread supplies the preview. ``max(id)`` identifies
    # it because ids are assigned in insertion order.
    last_messages = {
        m.id: m
        for m in db.query(DirectMessage).filter(DirectMessage.id.in_([r.last_id for r in rows]))
    }
    directory = _partner_directory(db, [r.partner for r in rows])

    results: list[ConversationPartner] = []
    for row in rows:
        last = last_messages.get(row.last_id)
        profile = directory.get(row.partner, {})
        fallback_name = (last.from_name or last.to_name) if last else None
        results.append(
            ConversationPartner(
                email=row.partner,
                name=profile.get("name") or fallback_name or row.partner,
                unread_count=int(row.unread or 0),
                last_message_at=cast(datetime, row.last_at),
                last_message_preview=(last.message[:120] if last and last.message else None),
                profile_pic=profile.get("pic"),
                member_id=profile.get("member_id"),
                expert_id=profile.get("expert_id"),
                role=profile.get("role"),
                message_count=int(row.message_count or 0),
            )
        )
    return results


@router.get(
    "/conversations/{partner_email}",
    response_model=ConversationThreadResponse,
    summary="Get conversation thread",
    description=(
        "A page of messages between the authenticated actor and the given partner, newest "
        "page first. Only messages the actor sent or received are ever returned."
    ),
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def get_conversation(
    request: Request,
    partner_email: str,
    db: Session = Depends(get_db),
    user_or_member: UserOrMemberDep = (None, None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=settings.MAX_PAGE_SIZE),
) -> ConversationThreadResponse:
    """Return a single conversation thread scoped to the current actor."""
    current_user, current_member = user_or_member
    actor_email = _get_actor_email(current_user, current_member)
    partner_email = partner_email.strip().lower()
    if partner_email == actor_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot view a conversation with yourself",
        )

    # The actor must be one end of every message returned: this predicate is
    # what keeps one member out of another's inbox. Both sides are case-folded
    # so a row the Flask inbox wrote with the address capitalised still belongs
    # to the same thread the conversation list groups it into.
    from_l = func.lower(DirectMessage.from_email)
    to_l = func.lower(DirectMessage.to_email)
    query = db.query(DirectMessage).filter(
        ((from_l == actor_email) & (to_l == partner_email))
        | ((from_l == partner_email) & (to_l == actor_email))
    )
    total = query.count()

    # Page backwards from the newest message, then present each page oldest-first.
    rows = (
        query.order_by(desc(DirectMessage.created_at), desc(DirectMessage.id))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    rows.reverse()

    # An empty thread means the caller has never exchanged a message with this
    # address. Enriching it anyway would turn this endpoint into an oracle:
    # probe an address, learn whether it has an account and who owns it. So when
    # there is no conversation, only accounts the directory already publishes
    # are resolved.
    directory = _partner_directory(db, [partner_email], public_only=total == 0)
    profile = directory.get(partner_email, {})
    partner = ConversationPartner(
        email=partner_email,
        name=profile.get("name") or partner_email,
        unread_count=0,
        profile_pic=profile.get("pic"),
        member_id=profile.get("member_id"),
        expert_id=profile.get("expert_id"),
        role=profile.get("role"),
        message_count=total,
    )

    return ConversationThreadResponse(
        partner_email=partner_email,
        messages=[DirectMessageResponse.model_validate(m) for m in rows],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
        partner=partner,
    )


@router.post(
    "/conversations/{partner_email}/reply",
    response_model=DirectMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Reply to conversation",
    description=(
        "Send a reply to an existing community member. The recipient must be a real account: "
        "an arbitrary address is refused rather than silently stored."
    ),
)
@limiter.limit("10/minute")
def reply_to_conversation(
    request: Request,
    partner_email: str,
    data: ConversationReply,
    db: Session = Depends(get_db),
    user_or_member: UserOrMemberDep = (None, None),
) -> DirectMessageResponse:
    """Send a reply in a conversation scoped to the current actor."""
    current_user, current_member = user_or_member
    actor_email = _get_actor_email(current_user, current_member)
    partner_email = partner_email.strip().lower()
    if partner_email == actor_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send a message to yourself",
        )

    # Refusing an unknown address is the fix for the open-relay behaviour the
    # Flask inbox had, where any string was accepted as a recipient.
    recipient = _resolve_recipient(db, partner_email)

    actor_name = current_member.full_name if current_member else getattr(current_user, "username", "")
    message = DirectMessage(
        to_name=recipient.full_name,
        to_email=partner_email,
        from_name=actor_name,
        from_email=actor_email,
        message=data.message.strip(),
        is_read=False,
        created_at=datetime.utcnow(),
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return DirectMessageResponse.model_validate(message)


@router.post(
    "/conversations/{partner_email}/read",
    summary="Mark conversation as read",
    description="Mark all messages from the partner to the authenticated actor as read.",
)
@limiter.limit("10/minute")
def mark_conversation_read(
    request: Request,
    partner_email: str,
    db: Session = Depends(get_db),
    user_or_member: UserOrMemberDep = (None, None),
) -> dict[str, int]:
    """Mark messages from the partner to the actor as read."""
    current_user, current_member = user_or_member
    actor_email = _get_actor_email(current_user, current_member)
    partner_email = partner_email.strip().lower()

    # Scoped to messages addressed *to* the actor, so this can never flip the
    # read flag on someone else's mail. Case-folded to match how the thread is
    # read, so a legacy row cannot stay stuck unread.
    updated = (
        db.query(DirectMessage)
        .filter(
            func.lower(DirectMessage.from_email) == partner_email,
            func.lower(DirectMessage.to_email) == actor_email,
            DirectMessage.is_read.is_(False),
        )
        .update({"is_read": True}, synchronize_session=False)
    )
    db.commit()
    return {"marked_read": updated}


def _get_actor_id_and_type(
    current_user: User | None, current_member: PulseMember | None
) -> tuple[str, int]:
    """Return (actor_type, actor_id) for the current authenticated actor."""
    if current_member:
        return "member", current_member.id
    if current_user:
        return "user", current_user.user_id
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
    )


@router.get(
    "/newsfeed/{post_id}",
    response_model=PostDetail,
    summary="Get post with interactions",
    description="Return a single newsfeed post including its likes and comments.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def get_post_detail(
    request: Request,
    post_id: int,
    db: Session = Depends(get_db),
) -> PostDetail:
    """Return a published newsfeed post with likes and comments."""
    # Unpublished posts must stay invisible: this endpoint is unauthenticated.
    post = or_404(
        db.query(Post).filter(Post.post_id == post_id, Post.is_published.is_(True)).first()
    )
    likes = (
        db.query(PostLike)
        .filter(PostLike.post_id == post_id)
        .order_by(asc(PostLike.created_at))
        .all()
    )
    comments = (
        db.query(PostComment)
        .filter(PostComment.post_id == post_id)
        .order_by(asc(PostComment.created_at))
        .all()
    )
    data = PostItem.model_validate(post).model_dump()
    data["likes"] = [PostLikeItem.model_validate(like) for like in likes]
    data["comments"] = [PostCommentItem.model_validate(comment) for comment in comments]
    return PostDetail(**data)


@router.post(
    "/newsfeed/{post_id}/like",
    summary="Like a post",
    description="Like a newsfeed post. Idempotent: duplicate likes are ignored.",
)
@limiter.limit("10/minute")
def like_post(
    request: Request,
    post_id: int,
    db: Session = Depends(get_db),
    user_or_member: UserOrMemberDep = (None, None),
) -> dict[str, Any]:
    """Like a post, scoped to the current actor."""
    current_user, current_member = user_or_member
    actor_type, actor_id = _get_actor_id_and_type(current_user, current_member)
    post = or_404(db.query(Post).filter(Post.post_id == post_id).first())

    existing = (
        db.query(PostLike)
        .filter(
            PostLike.post_id == post_id,
            PostLike.actor_type == actor_type,
            PostLike.actor_id == actor_id,
        )
        .first()
    )
    if existing:
        return {"message": "Already liked", "like_id": existing.id}

    like = PostLike(
        post_id=post_id,
        actor_type=actor_type,
        actor_id=actor_id,
        created_at=datetime.utcnow(),
    )
    db.add(like)
    post.likes_count = (post.likes_count or 0) + 1
    db.commit()
    db.refresh(like)
    return {"message": "Liked", "like_id": like.id}


@router.post(
    "/newsfeed/{post_id}/comment",
    response_model=PostCommentItem,
    status_code=status.HTTP_201_CREATED,
    summary="Comment on a post",
    description="Add a comment to a newsfeed post.",
)
@limiter.limit("10/minute")
def comment_on_post(
    request: Request,
    post_id: int,
    data: PostCommentCreate,
    db: Session = Depends(get_db),
    user_or_member: UserOrMemberDep = (None, None),
) -> PostCommentItem:
    """Add a comment to a post, scoped to the current actor."""
    current_user, current_member = user_or_member
    actor_type, actor_id = _get_actor_id_and_type(current_user, current_member)
    post = or_404(db.query(Post).filter(Post.post_id == post_id).first())

    comment = PostComment(
        post_id=post_id,
        actor_type=actor_type,
        actor_id=actor_id,
        content=data.content.strip(),
        created_at=datetime.utcnow(),
    )
    db.add(comment)
    post.comments_count = (post.comments_count or 0) + 1
    db.commit()
    db.refresh(comment)
    return PostCommentItem.model_validate(comment)


@router.get(
    "/{member_id}",
    response_model=PulseMemberDetail,
    summary="Member profile",
    description="Return a member profile. Only the owner or an admin can access full details.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def get_member(
    request: Request,
    member_id: int,
    db: Session = Depends(get_db),
    user_or_member: UserOrMemberDep = (None, None),
) -> PulseMemberDetail:
    """Return a single member profile."""
    current_user, current_member = user_or_member
    member = or_404(db.query(PulseMember).filter(PulseMember.id == member_id).first())
    if not _is_owner_or_admin(current_user, current_member, member):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this member profile",
        )
    return _to_member_detail(member)


@router.put(
    "/{member_id}",
    response_model=PulseMemberDetail,
    summary="Update member profile",
    description="Update a member profile. Only the owner or an admin can modify it.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def update_member(
    request: Request,
    member_id: int,
    data: PulseMemberUpdate,
    db: Session = Depends(get_db),
    user_or_member: UserOrMemberDep = (None, None),
) -> PulseMemberDetail:
    """Update a member profile."""
    current_user, current_member = user_or_member
    member = or_404(db.query(PulseMember).filter(PulseMember.id == member_id).first())
    if not _is_owner_or_admin(current_user, current_member, member):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this member profile",
        )
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(member, field, value)
    db.commit()
    db.refresh(member)
    return _to_member_detail(member)


# Entities resolved through an approved claim in ``member_entity_links``.
_CLAIM_ENTITY_TYPES = ("startup", "investor", "incubator")
# Founders resolve differently: their ids are strings, so they cannot live in
# the claim table at all. See ``_founder_contact``.
_ENTITY_TYPES = (*_CLAIM_ENTITY_TYPES, "founder")


@router.get(
    "/by-entity/{entity_type}/{entity_id}",
    response_model=EntityContact,
    summary="Find the member behind a directory entity",
    description=(
        "Resolves a directory profile to the community member behind it, so the page "
        "can offer a Message button. Startups, investors and incubators resolve through "
        "an approved claim; founders resolve through the account their profile was "
        "created from. Returns contactable=false rather than an error when nobody "
        "holds the profile."
    ),
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def entity_contact(
    request: Request,
    entity_type: str,
    entity_id: str,
    db: Session = Depends(get_db),
    actor: OptionalUserOrMemberDep = (None, None),
) -> EntityContact:
    """Return the confirmed member who represents this directory profile.

    ``entity_id`` is a string because founder ids are: a scraped founder carries
    a numeric one and an onboarded founder carries a random token, so typing the
    path as an integer would make founder profiles unaddressable.

    Two resolution paths, because the directory has two shapes of identity:

    * startup / investor / incubator — an approved row in ``member_entity_links``,
      read entity-to-member, which the composite index already covers;
    * founder — ``Founders.member_id``, stamped at onboarding from the member the
      profile was built from.

    No email is returned either way: the client messages by member id through
    ``POST /members/{id}/messages``, so an address never reaches the browser.
    """
    if entity_type not in _ENTITY_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"entity_type must be one of: {', '.join(_ENTITY_TYPES)}",
        )

    absent = EntityContact(contactable=False, entity_type=entity_type, entity_id=entity_id)

    if entity_type == "founder":
        founder = db.query(Founder).filter(Founder.founder_id == entity_id).first()
        # An unclaimed scraped profile has no account behind it, which is not an
        # error: the page renders, it just offers no way to make contact.
        member_id = founder.member_id if founder else None
    else:
        # A claim id is always an integer. A non-numeric one cannot match a row,
        # so it is reported absent rather than raising on the cast.
        try:
            claim_id = int(entity_id)
        except ValueError:
            return absent

        link = (
            db.query(MemberEntityLink)
            .filter(
                MemberEntityLink.entity_type == entity_type,
                MemberEntityLink.entity_id == claim_id,
                MemberEntityLink.status == "approved",
            )
            # Oldest approved claim wins, so a page does not switch owners as
            # more people are approved onto the same entity.
            .order_by(asc(MemberEntityLink.approved_at), asc(MemberEntityLink.id))
            .first()
        )
        member_id = link.member_id if link else None

    if member_id is None:
        return absent

    member = (
        db.query(PulseMember)
        .filter(PulseMember.id == member_id, PulseMember.is_confirmed.is_(True))
        .first()
    )
    if member is None:
        # Held by an account that is gone or unconfirmed: nothing to message.
        return absent

    _current_user, current_member = actor
    return EntityContact(
        contactable=True,
        entity_type=entity_type,
        entity_id=entity_id,
        member_id=member.id,
        full_name=member.full_name,
        role=member.role,
        profile_pic=member.profile_pic,
        is_self=current_member is not None and current_member.id == member.id,
    )


@router.post(
    "/{member_id}/messages",
    response_model=StartConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Message a member by id",
    description=(
        "Start or continue a conversation with a community member identified by id. "
        "The recipient's address is resolved on the server, so a sender never needs to "
        "know it in order to make contact."
    ),
)
@limiter.limit("10/minute")
def message_member(
    request: Request,
    member_id: int,
    data: StartConversationRequest,
    db: Session = Depends(get_db),
    user_or_member: UserOrMemberDep = (None, None),
) -> StartConversationResponse:
    """Send a message addressed by member id.

    The inbox is keyed by email, but email addresses are deliberately absent from
    the public directory, so before this existed there was no way to open a
    conversation from the UI at all. Resolving the recipient here keeps the
    address server-side and limits contact to accounts the directory already
    publishes.
    """
    current_user, current_member = user_or_member
    actor_email = _get_actor_email(current_user, current_member)
    actor_name = current_member.full_name if current_member else getattr(current_user, "username", "")

    recipient = (
        db.query(PulseMember)
        .filter(PulseMember.id == member_id, PulseMember.is_confirmed.is_(True))
        .first()
    )
    if recipient is None or not recipient.email:
        # Unconfirmed and unknown ids are indistinguishable, so this cannot be
        # used to probe which accounts exist but are not yet listed.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
        )

    recipient_email = recipient.email.strip().lower()
    if recipient_email == actor_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send a message to yourself",
        )

    message = DirectMessage(
        to_name=recipient.full_name,
        to_email=recipient_email,
        from_name=actor_name,
        from_email=actor_email,
        message=data.message,
        is_read=False,
        created_at=datetime.utcnow(),
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return StartConversationResponse(
        partner_email=recipient_email,
        partner_name=recipient.full_name,
        message=DirectMessageResponse.model_validate(message),
    )


@router.get(
    "/{member_id}/newsfeed",
    response_model=PaginatedResponse[PostItem],
    summary="Member newsfeed",
    description="Return posts relevant to a member's community feed.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def member_newsfeed(
    request: Request,
    member_id: int,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE),
) -> PaginatedResponse[PostItem]:
    """Return a member's newsfeed."""
    query = db.query(Post).filter(Post.is_published.is_(True)).order_by(desc(Post.created_at))
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(
        items=[PostItem.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )
