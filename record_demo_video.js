const { chromium } = require('/tmp/thepulse-video/node_modules/playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'http://127.0.0.1:5001';
const OUT_DIR  = path.join(process.cwd(), 'demo-output');

// ─── helpers ────────────────────────────────────────────────────────────────

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function smoothScroll(page, to, step = 38, delay = 68) {
  const from = await page.evaluate(() => window.scrollY);
  if (to <= from) return;
  for (let y = from; y <= to; y += step) {
    await page.evaluate(s => window.scrollTo({ top: s }), y);
    await sleep(delay);
  }
}

async function smoothScrollTo(page, to, step = 55, delay = 45) {
  const from = await page.evaluate(() => window.scrollY);
  const dir  = to > from ? 1 : -1;
  for (let y = from; dir > 0 ? y <= to : y >= to; y += dir * step) {
    await page.evaluate(s => window.scrollTo({ top: s }), y);
    await sleep(delay);
  }
}

async function scrollToBottom(page, step = 40, delay = 68) {
  const h = await page.evaluate(() => document.body.scrollHeight);
  await smoothScroll(page, h, step, delay);
  await sleep(700);
}

async function scrollToTop(page) {
  await smoothScrollTo(page, 0, 60, 38);
  await sleep(700);
}

async function goto(page, url) {
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.evaluate(() => {
    const o = document.getElementById('disclaimerOverlay');
    if (o) o.style.display = 'none';
  }).catch(() => {});
  await sleep(200);
}

// Move mouse smoothly to element centre, returns bounding box
async function hover(page, locator) {
  const box = await locator.boundingBox().catch(() => null);
  if (!box) return null;
  const x = box.x + box.width  / 2;
  const y = box.y + box.height / 2;
  await page.mouse.move(x, y, { steps: 22 });
  await sleep(250);
  return box;
}

async function hoverAndClick(page, locator) {
  await hover(page, locator);
  await locator.click();
}

async function openDropdown(page, labelText) {
  const btn = page.locator('.nav-dropdown-toggle').filter({ hasText: labelText });
  await hover(page, btn);
  await btn.click();
  await sleep(600);
}

async function typeSlowly(locator, text, delay = 68) {
  await locator.click();
  await locator.fill('');
  for (const ch of text) { await locator.type(ch); await sleep(delay); }
}

// ─── main ────────────────────────────────────────────────────────────────────

async function run() {
  fs.mkdirSync(OUT_DIR, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport:    { width: 1920, height: 1080 },
    recordVideo: { dir: OUT_DIR, size: { width: 1920, height: 1080 } }
  });

  // Force light mode + suppress popups + inject visible cursor on every page
  await context.addInitScript(() => {
    localStorage.setItem('theme', 'light');
    localStorage.setItem('cookieConsent', 'accepted');
    sessionStorage.setItem('disclaimerClosed', 'true');

    const inject = () => {
      if (document.getElementById('pw-cursor')) return;
      const s = document.createElement('style');
      s.textContent = `
        #pw-cursor {
          position: fixed;
          width: 22px; height: 22px;
          background: rgba(255,255,255,0.95);
          border: 2.5px solid #00D4AA;
          border-radius: 50%;
          pointer-events: none;
          z-index: 2147483647;
          left: 0; top: 0;
          transform: translate(-50%,-50%);
          box-shadow: 0 2px 14px rgba(0,0,0,0.38);
          transition: width .08s, height .08s, background .08s;
        }
        #pw-cursor.dn { width:14px; height:14px; background:rgba(0,212,170,.9); }
      `;
      document.head.appendChild(s);
      const el = document.createElement('div');
      el.id = 'pw-cursor';
      document.body.appendChild(el);
      document.addEventListener('mousemove', e => {
        el.style.left = e.clientX + 'px';
        el.style.top  = e.clientY + 'px';
      });
      document.addEventListener('mousedown', () => el.classList.add('dn'));
      document.addEventListener('mouseup',   () => el.classList.remove('dn'));
    };

    if (document.readyState === 'loading')
      document.addEventListener('DOMContentLoaded', inject);
    else inject();
  });

  const page = await context.newPage();
  page.setDefaultTimeout(20000);

  // ── 1. LOGIN ─────────────────────────────────────────────────────────────
  await goto(page, `${BASE_URL}/login`);
  await sleep(1000);

  await page.mouse.move(960, 450, { steps: 20 });
  await typeSlowly(page.locator('input[name="username"]'), 'admin', 90);
  await sleep(300);
  await typeSlowly(page.locator('input[name="password"]'), 'admin', 90);
  await sleep(500);
  await hoverAndClick(page, page.locator('button[type="submit"]'));

  await page.waitForURL(`${BASE_URL}/`);
  await page.waitForLoadState('networkidle');
  await page.evaluate(() => {
    const o = document.getElementById('disclaimerOverlay');
    if (o) o.style.display = 'none';
  }).catch(() => {});
  await sleep(2000);

  // ── 2. HOME — scroll & newsfeed ──────────────────────────────────────────
  // Hero visible
  await page.mouse.move(960, 400, { steps: 15 });
  await sleep(800);

  // Scroll slowly to newsfeed section (~800px)
  await smoothScroll(page, 900, 32, 65);
  await sleep(800);

  // Find Karim Beqqali post
  const karimPost = page.locator('.nf-card').filter({ has: page.locator('text=Karim Beqqali') }).first();
  await karimPost.scrollIntoViewIfNeeded();
  await sleep(700);
  await hover(page, karimPost);
  await sleep(400);

  // LIKE
  const likeBtn = karimPost.locator('.nf-like-btn');
  await hover(page, likeBtn);
  await sleep(350);
  await likeBtn.click();
  await sleep(800);

  // COMMENT — show comments
  const commentBtn = karimPost.locator('.nf-comment-btn');
  await hover(page, commentBtn);
  await sleep(350);
  await commentBtn.click();
  await sleep(1200);

  // DM — Envoyer un Pulse
  const msgBtn = karimPost.locator('.nf-msg-btn');
  await hover(page, msgBtn);
  await sleep(350);
  await msgBtn.click();
  await sleep(1400);

  // Fill modal
  await typeSlowly(page.locator('#msgSenderName'),  'Youssef El Amrani',        65);
  await sleep(250);
  await typeSlowly(page.locator('#msgSenderEmail'), 'youssef@startup.ma',       60);
  await sleep(250);
  await typeSlowly(
    page.locator('#msgContent'),
    'Bravo pour cette levée ! Très inspirant pour tout l\'écosystème. J\'aimerais beaucoup échanger avec vous sur votre expérience.',
    42
  );
  await sleep(600);

  // Click "Envoyer le Pulse"
  const sendBtn = page.locator('#msgModal button[onclick="sendMsg()"]');
  await hover(page, sendBtn);
  await sleep(350);
  await sendBtn.click();
  await sleep(1400);

  // Close modal if still open
  await page.evaluate(() => {
    const m = document.getElementById('msgModal');
    if (m) m.style.display = 'none';
  }).catch(() => {});
  await sleep(800);

  // Continue scrolling homepage — actualités, appels, cofond, financer, analytics, partenaires, footer
  await scrollToBottom(page, 38, 65);

  // Back to top
  await scrollToTop(page);

  // ── 3. STARTUPS ──────────────────────────────────────────────────────────
  await goto(page, `${BASE_URL}/startups`);
  await sleep(1800);

  // Scroll lentement pour montrer la liste
  await smoothScroll(page, 800, 35, 65);
  await sleep(600);
  await smoothScroll(page, 1600, 35, 65);
  await sleep(600);

  // Click CHARI — cherche par texte dans le titre de la carte
  const chariCard = page.locator('.startup-card-title', { hasText: 'Chari' }).first();
  await chariCard.waitFor({ timeout: 10000 }).catch(() => {});
  await chariCard.scrollIntoViewIfNeeded().catch(() => {});
  await sleep(500);
  await hover(page, chariCard);
  await sleep(400);
  // Navigate via href pour être sûr
  const chariHref = await page.locator('a.startup-card').filter({ has: page.locator('text=Chari') }).first().getAttribute('href').catch(() => '/startup/117');
  await goto(page, `${BASE_URL}${chariHref || '/startup/117'}`);
  await page.waitForLoadState('networkidle');
  await sleep(1600);

  await scrollToBottom(page);
  await scrollToTop(page);

  // Click Ismail Belkhayat (founder linked on Chari page)
  const ismailLink = page.locator('a[href="/founder/99893"]').first();
  if (await ismailLink.count()) {
    await ismailLink.scrollIntoViewIfNeeded();
    await sleep(400);
    await hover(page, ismailLink);
    await sleep(350);
    await ismailLink.click();
    await page.waitForURL(`${BASE_URL}/founder/99893`);
    await page.waitForLoadState('networkidle');
  } else {
    await goto(page, `${BASE_URL}/founder/99893`);
  }
  await sleep(1600);
  await scrollToBottom(page);
  await scrollToTop(page);

  // Navigate to Mohamed Benmansour
  await goto(page, `${BASE_URL}/founder/99885`);
  await sleep(1600);
  await scrollToBottom(page);
  await scrollToTop(page);

  // ── 4. INVESTISSEURS ─────────────────────────────────────────────────────
  await hoverAndClick(page, page.locator('a[href="/investors"]').first());
  await page.waitForLoadState('networkidle');
  await sleep(1500);

  await scrollToBottom(page);
  await scrollToTop(page);

  // Click 212 Founders card
  const f212 = page.locator('a[href="/investor/15"]').first();
  if (await f212.count()) {
    await f212.scrollIntoViewIfNeeded();
    await sleep(400);
    await hover(page, f212);
    await sleep(350);
    await f212.click();
    await page.waitForURL(`${BASE_URL}/investor/15`);
    await page.waitForLoadState('networkidle');
  } else {
    await goto(page, `${BASE_URL}/investor/15`);
  }
  await sleep(1600);
  await scrollToBottom(page);
  await scrollToTop(page);

  // ── 5. INCUBATEURS ───────────────────────────────────────────────────────
  await hoverAndClick(page, page.locator('a[href="/incubators"]').first());
  await page.waitForLoadState('networkidle');
  await sleep(1500);
  await scrollToBottom(page);
  await scrollToTop(page);

  // ── 6. APPELS À PROJETS ──────────────────────────────────────────────────
  const appelLink = page.locator('a[href*="Appels"]').first();
  await hover(page, appelLink);
  await sleep(300);
  await goto(page, `${BASE_URL}/ressources?category=Appels+%C3%A0+projets`);
  await sleep(1500);
  await scrollToBottom(page);
  await scrollToTop(page);

  // ── 7. CAPITAL HUMAIN → Talents ──────────────────────────────────────────
  await openDropdown(page, 'Capital Humain');
  const talentsItem = page.locator('.nav-dropdown-menu a[href="/talents"]').first();
  await hover(page, talentsItem);
  await sleep(300);
  await talentsItem.click();
  await page.waitForLoadState('networkidle');
  await sleep(1500);
  await scrollToBottom(page);
  await scrollToTop(page);

  // CAPITAL HUMAIN → Co-Fondateurs
  await openDropdown(page, 'Capital Humain');
  const cofoundItem = page.locator('.nav-dropdown-menu a[href="/cofounders"]').first();
  await hover(page, cofoundItem);
  await sleep(300);
  await cofoundItem.click();
  await page.waitForLoadState('networkidle');
  await sleep(1500);
  await scrollToBottom(page);
  await scrollToTop(page);

  // ── 8. ÉCOSYSTÈME → Actualités ───────────────────────────────────────────
  await openDropdown(page, 'Écosystème');
  const actItem = page.locator('.nav-dropdown-menu a[href="/actualites"]').first();
  await hover(page, actItem);
  await sleep(300);
  await actItem.click();
  await page.waitForLoadState('networkidle');
  await sleep(1500);
  await scrollToBottom(page);
  await scrollToTop(page);

  // Click "Lire l'article complet" for Hamid (article 8)
  const hamidBtn = page.locator('a[href="/article/8"]').first();
  if (await hamidBtn.count()) {
    await hamidBtn.scrollIntoViewIfNeeded();
    await sleep(400);
    await hover(page, hamidBtn);
    await sleep(350);
    await hamidBtn.click();
    await page.waitForURL(`${BASE_URL}/article/8`);
    await page.waitForLoadState('networkidle');
  } else {
    await goto(page, `${BASE_URL}/article/8`);
  }
  await sleep(1600);
  await scrollToBottom(page);
  await scrollToTop(page);

  // ── 9. ÉCOSYSTÈME → Ressources ───────────────────────────────────────────
  await openDropdown(page, 'Écosystème');
  const resItem = page.locator('.nav-dropdown-menu a[href="/ressources"]').first();
  await hover(page, resItem);
  await sleep(300);
  await resItem.click();
  await page.waitForLoadState('networkidle');
  await sleep(1500);
  await scrollToBottom(page);
  await scrollToTop(page);

  // ── 10. TOOLBOX IA ───────────────────────────────────────────────────────
  await hoverAndClick(page, page.locator('a[href="/toolbox"]').first());
  await page.waitForLoadState('networkidle');
  await sleep(1500);
  await scrollToBottom(page);
  await scrollToTop(page);

  // ── 11. LANGUE + THÈME ───────────────────────────────────────────────────
  const langBtn  = page.locator('#langToggle');
  const themeBtn = page.locator('#themeToggle');

  await hover(page, langBtn);
  await sleep(700);
  await langBtn.click();   // FR → EN
  await sleep(1300);
  await langBtn.click();   // EN → FR
  await sleep(800);

  await hover(page, themeBtn);
  await sleep(700);
  await themeBtn.click();  // light → dark
  await sleep(1300);
  await themeBtn.click();  // dark → light
  await sleep(800);

  // ── 12. REJOINDRE ────────────────────────────────────────────────────────
  await hoverAndClick(page, page.locator('a.btn-join').first());
  await page.waitForLoadState('networkidle');
  await sleep(1500);
  await scrollToBottom(page);
  await scrollToTop(page);
  await scrollToBottom(page);

  // Click À propos (footer link)
  const aboutLink = page.locator('a[href="/about-us"]').last();
  await aboutLink.scrollIntoViewIfNeeded();
  await sleep(400);
  await hover(page, aboutLink);
  await sleep(350);
  await aboutLink.click();
  await page.waitForLoadState('networkidle');
  await sleep(1600);
  await scrollToBottom(page);
  await scrollToTop(page);

  // ── 13. LOGO → ACCUEIL ───────────────────────────────────────────────────
  const logoLink = page.locator('a.logo-link').first();
  await hover(page, logoLink);
  await sleep(400);
  await logoLink.click();
  await page.waitForURL(`${BASE_URL}/`);
  await page.waitForLoadState('networkidle');
  await sleep(2200);

  // ── FIN ──────────────────────────────────────────────────────────────────
  await page.close();
  await context.close();
  await browser.close();

  const files = fs.readdirSync(OUT_DIR).filter(f => f.endsWith('.webm'));
  if (!files.length) throw new Error('No video produced.');
  files.sort((a, b) => fs.statSync(path.join(OUT_DIR, b)).mtimeMs - fs.statSync(path.join(OUT_DIR, a)).mtimeMs);
  console.log(path.join(OUT_DIR, files[0]));
}

run().catch(e => { console.error(e); process.exit(1); });
