"""Build the site from src/ into site/ (what goes on GitHub Pages).

  src/site.css, src/site.js   shared styles and script (inlined into every page)
  src/pages/*.html            page bodies; first two lines are <!-- title: --> and <!-- description: -->
  src/data.json               eBay numbers shown on the site      (refresh: ebay_profile.py, then edit)
  src/stock.json              live eBay listings                  (refresh: python3 ebay_profile.py stock)
  src/quotes.json             buyer feedback quotes, verbatim     (pick from: python3 ebay_profile.py feedback)
  src/sold.json               the recently-sold sheet

Run:  python3 build.py
Writes site/*.html, sitemap.xml, robots.txt, assets/favicon.svg, plus preview/index.html
(a head-less copy of the home page for the private Claude preview).
"""
import datetime as dt
import html
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
SRC, OUT, PREVIEW = ROOT / 'src', ROOT / 'site', ROOT / 'preview'
MIRROR = Path('/private/tmp/claude-501/-Users-cole-Desktop/7a9b7872-3cdf-4297-bbcd-a77bbfd7289d/scratchpad/www')
SITE = 'https://spanotechnologies.com'
EBAY = 'https://www.ebay.com/str/spanotechnologies'
FEEDBACK = 'https://www.ebay.com/fdbk/feedback_profile/spanotechnologies'
NAV = [('guide.html', 'Guide', 'Buying guide'), ('faq.html', 'FAQ', 'FAQ'), ('about.html', 'About', 'About'),
       ('roadmap.html', "What's next", "What's next"), ('contact.html', 'Contact', 'Contact')]

# The ST mark, traced from brand/mark-dark.png
S_PTS = '157,0 482,0 418,64 288,64 257,96 513,96 352,257 0,257 64,193 320,193 352,161 96,161 194,63'
T_PTS = '531,0 855,0 791,64 693,64 500,257 405,257 597,64 467,64'
MARK = (f'<svg class="mark" viewBox="0 0 856 258" aria-hidden="true" focusable="false">'
        f'<polygon points="{S_PTS}"/><polygon points="{T_PTS}"/></svg>')
MARK_LINES = (f'<svg viewBox="0 0 856 258" aria-hidden="true" focusable="false">'
              f'<polygon points="{S_PTS}" pathLength="1"/><polygon points="{T_PTS}" pathLength="1"/></svg>')
HERO_MARK = f'''<div class="hero-mark" aria-hidden="true">
  <svg viewBox="0 0 856 258" focusable="false">
    <defs>
      <linearGradient id="mkfill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1c1c1f"/><stop offset="1" stop-color="#47474c"/></linearGradient>
      <linearGradient id="mksheen" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".42"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
      <clipPath id="mkclip"><polygon points="{S_PTS}"/><polygon points="{T_PTS}"/></clipPath>
    </defs>
    <g class="mk mk-s"><polygon points="{S_PTS}" fill="url(#mkfill)"/></g>
    <g class="mk mk-t"><polygon points="{T_PTS}" fill="url(#mkfill)"/></g>
    <g clip-path="url(#mkclip)"><g transform="skewX(-45)"><rect class="mk-sheen" x="-420" y="-20" width="190" height="300" fill="url(#mksheen)"/></g></g>
    <polygon class="mk-line" points="{S_PTS}" pathLength="1"/><polygon class="mk-line" points="{T_PTS}" pathLength="1"/>
  </svg>
</div>'''
ARR = ('<svg class="arr" viewBox="0 0 12 12" aria-hidden="true" focusable="false">'
       '<path d="M2 10 10 2M3.5 2H10v6.5" fill="none" stroke="currentColor" stroke-width="1.7"/></svg>')
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;600'
         '&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500&display=swap">')
JSONLD = ('<script type="application/ld+json">{"@context":"https://schema.org","@type":"Organization",'
          '"name":"Spano Technologies","url":"https://spanotechnologies.com/",'
          '"logo":"https://spanotechnologies.com/assets/apple-touch-icon.png",'
          '"email":"cole@spanotechnologies.com","sameAs":["https://www.ebay.com/str/spanotechnologies"]}</script>')

DATA = json.loads((SRC / 'data.json').read_text())
esc = html.escape


def header(current):
    cur = ' aria-current="page"'
    links = ''.join(f'<a href="{h}"{cur if h == current else ""}>{short}</a>' for h, short, _ in NAV)
    sheet = ''.join(f'<a href="{h}"{cur if h == current else ""}>{long}<small>0{i}</small></a>'
                    for i, (h, _, long) in enumerate([('index.html', 'Home', 'Home')] + NAV, 1))
    return f'''<a class="skip" href="#main">Skip to content</a>
<header class="bar">
  <div class="wrap">
    <a class="brand" href="index.html" aria-label="Spano Technologies home">{MARK}<span class="wordmark">Spano Technologies</span></a>
    <div class="bar-end">
      <nav class="menu" aria-label="Main">{links}</nav>
      <a class="btn small" href="{EBAY}" target="_blank" rel="noopener">Shop {ARR}</a>
      <button class="burger" type="button" aria-expanded="false" aria-controls="sheet" aria-label="Menu"><span></span><span></span></button>
    </div>
  </div>
  <div class="progress" aria-hidden="true"></div>
</header>
<div class="sheet" id="sheet">
  <nav aria-label="Menu">{sheet}</nav>
  <div class="sheet-foot">
    <a class="btn" href="{EBAY}" target="_blank" rel="noopener">Shop on eBay {ARR}</a>
    <p class="proof"><span>{DATA["PCT"]}% positive</span><span>{DATA["SOLD"]}+ sold</span><span>Since {DATA["SINCE"]}</span></p>
  </div>
</div>'''


FOOTER = f'''<footer>
  <div class="wrap">
    <div class="foot-word" aria-hidden="true">Spano Technologies</div>
    <div class="foot-grid">
      <div>{MARK}<p>Used business laptops and computer memory, checked by hand and sold on eBay since {DATA["SINCE"]}.</p></div>
      <div><h4>Shop</h4><nav aria-label="Shop"><a href="{EBAY}" target="_blank" rel="noopener">eBay store {ARR}</a><a href="{FEEDBACK}" target="_blank" rel="noopener">Feedback {ARR}</a><a href="index.html#stock">In stock now</a></nav></div>
      <div><h4>Info</h4><nav aria-label="Info"><a href="guide.html">Buying guide</a><a href="faq.html">FAQ</a><a href="about.html">About</a><a href="roadmap.html">What's next</a></nav></div>
      <div><h4>Contact</h4><nav aria-label="Contact"><a href="contact.html">Contact page</a><a href="mailto:cole@spanotechnologies.com">cole@spanotechnologies.com</a></nav></div>
    </div>
    <div class="legal"><span>© {dt.date.today().year} Spano Technologies</span><span>Independent seller. eBay is a trademark of eBay Inc.</span></div>
  </div>
</footer>'''


def stock_block():
    data = json.loads((SRC / 'stock.json').read_text())
    items = data['items']
    when = dt.date.fromisoformat(data['as_of']).strftime('%b %-d, %Y')
    if not items:
        return (f'<div class="empty"><h3>Nothing listed right now.</h3><p class="muted">Stock arrives in batches and the good '
                f'machines go quickly. Save the store on eBay to see the next batch when it lands.</p>'
                f'<a class="btn small" href="{EBAY}" target="_blank" rel="noopener">Open the eBay store {ARR}</a></div>')
    cards = []
    for it in items:
        title = esc(it['title'].strip())
        img = (f'<div class="stock-img"><img src="{it["image"]}" alt="{title}" loading="lazy"></div>' if it['image']
               else '<div class="stock-img"></div>')
        cards.append(f'<a class="stock-card" href="{it["url"]}" target="_blank" rel="noopener">{img}<div class="stock-body">'
                     f'<p class="eyebrow live"><i></i>In stock</p><h3>{title}</h3>'
                     f'<div class="stock-meta"><span class="price">${float(it["price"]):,.2f}</span>'
                     f'<span class="btn small">View on eBay {ARR}</span></div></div></a>')
    one = ' one' if len(items) == 1 else ''
    return (f'<div class="stock{one}">{"".join(cards)}</div>'
            f'<p class="stock-note">Listings as of {when}. Price and availability are confirmed on eBay.</p>')


def quote_block():
    out = []
    for q in json.loads((SRC / 'quotes.json').read_text()):
        out.append(f'<figure class="quote"><blockquote>{esc(q["text"])}</blockquote>'
                   f'<figcaption><b>Verified eBay buyer</b><span>{esc(q["item"])} · {esc(q["when"])}</span></figcaption></figure>')
    return ''.join(out)


def sold_block(group):
    return ''.join(f'<li><b>{esc(m)}</b><span>{esc(s)}</span><em>Sold</em></li>'
                   for m, s in json.loads((SRC / 'sold.json').read_text())[group])


def page(name):
    raw = (SRC / 'pages' / name).read_text()
    for k, v in DATA.items():
        raw = raw.replace('{{' + k + '}}', v)
    if '{{STOCK}}' in raw:
        raw = raw.replace('{{STOCK}}', stock_block())
    raw = (raw.replace('{{QUOTES}}', quote_block()).replace('{{SOLD_LAPTOPS}}', sold_block('laptops')).replace('{{SOLD_MEMORY}}', sold_block('memory'))
              .replace('{{HERO_MARK}}', HERO_MARK).replace('{{EBAY}}', EBAY).replace('{{FEEDBACK_URL}}', FEEDBACK)
              .replace(' ↗', ' ' + ARR)
              .replace('<section class="page-head">',
                       f'<section class="page-head"><div class="head-mark" aria-hidden="true">{MARK_LINES}</div>'))
    title = re.search(r'<!-- title: (.*?) -->', raw).group(1)
    desc = re.search(r'<!-- description: (.*?) -->', raw).group(1)
    body = re.sub(r'<!-- (title|description): .*? -->\n', '', raw)
    return title, desc, body


def build():
    css = (SRC / 'site.css').read_text()
    js = (SRC / 'site.js').read_text()
    OUT.mkdir(exist_ok=True)
    PREVIEW.mkdir(exist_ok=True)
    (OUT / 'assets').mkdir(exist_ok=True)
    (OUT / 'assets' / 'favicon.svg').write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" fill="#09090a"/>'
        f'<g transform="translate(6 24.2) scale(0.0607)" fill="#f2f2f0"><polygon points="{S_PTS}"/><polygon points="{T_PTS}"/></g></svg>\n')
    names = []
    for f in sorted((SRC / 'pages').glob('*.html')):
        title, desc, body = page(f.name)
        current = f.name if f.name != '404.html' else ''
        main = f'{header(current)}\n<main id="main">\n{body}</main>\n{FOOTER}\n<script>\n{js}</script>\n'
        if f.name == '404.html':  # served from any path, so links must be root-absolute
            main = re.sub(r'(src|href)="(assets/|[a-z0-9]+\.html)', r'\1="/\2', main).replace('href="/index.html', 'href="/')
        slug = '' if f.name == 'index.html' else f.name[:-5]
        extra = '' if f.name == '404.html' else f'<link rel="canonical" href="{SITE}/{slug}">\n'
        extra += JSONLD + '\n' if f.name == 'index.html' else ''
        if f.name != '404.html':
            names.append(slug)
        full = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="icon" type="image/svg+xml" href="/assets/favicon.svg">
<link rel="icon" type="image/png" href="/assets/favicon.png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Spano Technologies">
<meta property="og:url" content="{SITE}/{slug}">
<meta property="og:image" content="{SITE}/assets/og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#09090a">
<meta name="color-scheme" content="dark">
{extra}{FONTS}
<style>
{css}</style>
</head>
<body>
{main}</body>
</html>
'''
        (OUT / f.name).write_text(full)
        print('wrote', f.name)
        if f.name == 'index.html':
            (PREVIEW / 'index.html').write_text(
                f'<title>{title}</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
                f'{FONTS}\n<style>\n{css}</style>\n{main}')
    order = ['', 'guide', 'faq', 'about', 'roadmap', 'contact']
    urls = ''.join(f'  <url><loc>{SITE}/{p}</loc></url>\n' for p in order if p in names)
    (OUT / 'sitemap.xml').write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'{urls}</urlset>\n')
    (OUT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n')
    print('wrote sitemap.xml, robots.txt, assets/favicon.svg')
    if MIRROR.parent.exists():  # copy for the local preview server, which cannot read the Desktop
        shutil.copytree(OUT, MIRROR / 'site', dirs_exist_ok=True)


if __name__ == '__main__':
    build()
