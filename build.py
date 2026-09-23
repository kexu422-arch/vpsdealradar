# ILANG: role=static-builder; source=data/offers.json + .ilang/site.ilang; writes=site/.
# ILANG: boundary=never fabricate prices, dates, commissions, or provider records.

import html
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
SITE = ROOT / "site"


def config():
    text = (ROOT / ".ilang" / "site.ilang").read_text(encoding="utf-8")
    m = re.search(r"::STATE\{@SITE, brand:([^,]+), niche:([^,]+), domain:([^}]+)", text)
    providers, active = [], False
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("::MODULE{PROVIDERS"): active = True; continue
        if active and line.startswith("::MODULE{"): active = False
        if active and line and not line.startswith("::") and "|" in line:
            name, website, source, affiliate = [x.strip() for x in line.split("|", 3)]
            providers.append({"name": name, "website": website, "source": source, "affiliate": affiliate})
    return {"brand": m.group(1).strip(), "niche": m.group(2).strip(), "domain": m.group(3).strip().rstrip("/"), "providers": providers}


def esc(value): return html.escape(str(value or ""))
def layout(title, description, body, canonical, cfg):
    return f'''<!doctype html><html lang="en-US"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(description)}"><link rel="canonical" href="{esc(canonical)}">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:type" content="website"><meta property="og:url" content="{esc(canonical)}"><meta name="twitter:card" content="summary_large_image"><link rel="stylesheet" href="/assets/style.css"></head><body><header><a class="brand" href="/">{esc(cfg['brand'])}</a><nav><a href="/providers/">Providers</a><a href="/compare/">Compare</a></nav></header><main>{body}</main><footer>Public-source VPS offers. Prices and availability are shown only when found on the linked provider page. <a href="/about/">Site rules</a></footer></body></html>'''


def offer_card(o, cfg):
    price = f'<p class="price">{esc(o.get("price"))}</p>' if o.get("price") else '<p class="muted">Price not stated on source page</p>'
    discount = f'<span class="badge">{esc(o.get("discount"))}</span>' if o.get("discount") else ''
    slug = re.sub(r'[^a-z0-9]+', '-', (o.get('provider','offer') + '-' + o.get('title','offer')).lower()).strip('-')[:80]
    return f'<article class="card"><div>{discount}<h3>{esc(o.get("title"))}</h3><p>{esc(o.get("provider"))}</p>{price}<a class="button" href="/deals/{slug}/">View details</a></div><small>Source: <a href="{esc(o.get("source_url"))}">{esc(o.get("source_url"))}</a></small></article>'

def itemlist(offers, cfg):
    entries = []
    for pos, o in enumerate(offers, 1):
        slug = re.sub(r'[^a-z0-9]+', '-', (o.get('provider','offer') + '-' + o.get('title','offer')).lower()).strip('-')[:80]
        entries.append({"@type":"ListItem", "position":pos, "url":cfg['domain'] + '/deals/' + slug + '/'})
    return '<script type="application/ld+json">' + json.dumps({"@context":"https://schema.org", "@type":"ItemList", "itemListElement":entries}) + '</script>'

def deal_page(o, cfg, slug):
    offer = {"@context":"https://schema.org", "@type":"Offer", "url":cfg['domain'] + '/deals/' + slug + '/', "availability":"https://schema.org/InStock"}
    if o.get('price') and o.get('currency'): offer.update({"price":o['price'], "priceCurrency":o['currency']})
    if o.get('valid_until'): offer['priceValidUntil'] = o['valid_until']
    ld = '<script type="application/ld+json">' + json.dumps(offer) + '</script>'
    price = f'<p class="price">{esc(o.get("price"))}</p>' if o.get('price') else '<p class="muted">Price not stated on source page.</p>'
    body = f'<section class="hero">{ld}<p class="eyebrow">{esc(o.get("provider"))}</p><h1>{esc(o.get("title"))}</h1>{price}<p>This record is copied from a public provider page and may change. Check the source before purchase.</p><a class="button" href="{esc(o.get("affiliate_url") or o.get("offer_url"))}" rel="nofollow sponsored">Open provider source</a><p><small>Source: <a href="{esc(o.get("source_url"))}">{esc(o.get("source_url"))}</a></small></p></section>'
    return layout(f"{o.get('provider')} offer — {cfg['brand']}", o.get('title','Verified VPS offer'), body, cfg['domain'] + '/deals/' + slug + '/', cfg)


def main():
    cfg = config(); data = json.loads((ROOT / "data" / "offers.json").read_text(encoding="utf-8")) if (ROOT / "data" / "offers.json").exists() else {"offers": [], "fetched_at": ""}
    offers = data.get("offers", []); shutil.rmtree(SITE, ignore_errors=True); (SITE / "assets").mkdir(parents=True)
    (SITE / "assets" / "style.css").write_text((ROOT / "templates" / "style.css").read_text(encoding="utf-8"), encoding="utf-8")
    cards = ''.join(offer_card(o, cfg) for o in offers) or '<div class="empty"><h2>No verified offers yet</h2><p>The next scheduled public-source scan will add offers when provider pages publish a qualifying deal. Nothing is invented.</p></div>'
    home = layout(f"{cfg['brand']} — VPS deals", "Public-source VPS deals and provider promotions, updated automatically.", f'<section class="hero"><p class="eyebrow">{esc(cfg["niche"])}</p><h1>Verified VPS deals from public sources.</h1><p>Fresh provider promotions, with source links and no made-up prices.</p></section><section><div class="section-head"><h2>Latest offers</h2><span>{len(offers)} verified records</span></div>{itemlist(offers, cfg)}<div class="grid">{cards}</div></section>', cfg['domain'] + '/', cfg)
    (SITE / "index.html").write_text(home, encoding="utf-8")
    providers = ''.join(f'<li><a href="{esc(p["website"])}">{esc(p["name"])}</a><span>{esc(p["source"])}</span></li>' for p in cfg['providers']) or '<li>No providers configured.</li>'
    (SITE / "providers").mkdir(); (SITE / "providers" / "index.html").write_text(layout(f"Providers — {cfg['brand']}", "VPS providers monitored by this site.", f'<section class="hero"><h1>Providers</h1><p>Configured in <code>.ilang/site.ilang</code>; changing that file changes this page.</p></section><ul class="providers">{providers}</ul>', cfg['domain'] + '/providers/', cfg), encoding="utf-8")
    (SITE / "compare").mkdir(); (SITE / "compare" / "index.html").write_text(layout(f"Compare VPS deals — {cfg['brand']}", "Compare currently verified VPS offers.", f'<section class="hero"><h1>Compare VPS deals</h1><p>Only current records from public provider pages are included.</p></section>{itemlist(offers, cfg)}<div class="grid">{cards}</div>', cfg['domain'] + '/compare/', cfg), encoding="utf-8")
    for o in offers:
        slug = re.sub(r'[^a-z0-9]+', '-', (o.get('provider','offer') + '-' + o.get('title','offer')).lower()).strip('-')[:80]
        target = SITE / 'deals' / slug; target.mkdir(parents=True, exist_ok=True)
        (target / 'index.html').write_text(deal_page(o, cfg, slug), encoding='utf-8')
    (SITE / "about").mkdir(); (SITE / "about" / "index.html").write_text(layout(f"About — {cfg['brand']}", "Rules and data sources for this VPS deal site.", '<section class="hero"><h1>About this site</h1><p>We scan public provider pages permitted by robots.txt. We do not invent offers, prices, commissions, or validity dates. Links are labeled as sponsored only when an affiliate URL is configured.</p><p>Site rules are maintained in <code>.ilang/site.ilang</code>.</p></section>', cfg['domain'] + '/about/', cfg), encoding="utf-8")
    (SITE / "404.html").write_text(layout(f"Page not found — {cfg['brand']}", "The requested page was not found.", '<section class="hero"><h1>Page not found</h1><p>The requested address does not exist on this site.</p><a class="button" href="/">Return home</a></section>', cfg['domain'] + '/404.html', cfg), encoding="utf-8")
    urls = ['', 'providers/', 'compare/', 'about/']; now = data.get('fetched_at', datetime.now(timezone.utc).date().isoformat())
    (SITE / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{cfg["domain"]}/{u}</loc><lastmod>{now}</lastmod></url>' for u in urls) + '</urlset>', encoding="utf-8")
    (SITE / "robots.txt").write_text('User-agent: *\nAllow: /\nSitemap: ' + cfg['domain'] + '/sitemap.xml\n', encoding="utf-8")

if __name__ == "__main__": main()
