# ILANG: role=scraper; source=public provider pages; boundary=never invent offers/prices.
# ILANG: reads=.ilang/site.ilang; writes=data/offers.json; runtime=no API keys.

import json
import re
import time
import urllib.request
import urllib.robotparser
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).parent


def load_config():
    text = (ROOT / ".ilang" / "site.ilang").read_text(encoding="utf-8")
    state = re.search(r"::STATE\{@SITE, brand:([^,]+), niche:([^,]+), domain:([^}]+)", text)
    providers = []
    in_providers = False
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("::MODULE{PROVIDERS"):
            in_providers = True
            continue
        if in_providers and line.startswith("::MODULE{"):
            in_providers = False
        if in_providers and line and not line.startswith("::") and "|" in line:
            name, website, source, affiliate = [x.strip() for x in line.split("|", 3)]
            providers.append({"name": name, "website": website, "source": source, "affiliate": affiliate})
    return {"brand": state.group(1).strip(), "niche": state.group(2).strip(), "domain": state.group(3).strip(), "providers": providers}


def allowed(url):
    parsed = urllib.parse.urlparse(url)
    rp = urllib.robotparser.RobotFileParser(f"{parsed.scheme}://{parsed.netloc}/robots.txt")
    try:
        rp.read()
        return rp.can_fetch("VPSDealRadarBot/1.0 (+public-site)", url)
    except Exception:
        return False


def fetch(url):
    if not allowed(url):
        return ""
    req = urllib.request.Request(url, headers={"User-Agent": "VPSDealRadarBot/1.0 (+public-site)"})
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return response.read().decode("utf-8", errors="replace")
    except Exception:
        return ""


def extract(provider, html, fetched_at):
    if not html:
        return []
    plain = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", html, flags=re.I)
    plain = re.sub(r"<[^>]+>", " ", plain)
    plain = re.sub(r"\s+", " ", plain).strip()
    # Only emit a record when the public page contains an explicit deal/sale/discount signal.
    matches = re.findall(r"[^.]{0,160}(?:discount|deal|sale|promo|coupon|offer)[^.]{0,240}\.?", plain, flags=re.I)
    offers = []
    for item in matches[:20]:
        item = item.strip()
        if len(item) < 20:
            continue
        price = re.search(r"(?:[$€£]\s?\d+(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?\s?(?:USD|EUR|GBP))", item, re.I)
        discount = re.search(r"\b\d{1,3}%\s?(?:off|discount)?\b", item, re.I)
        offers.append({
            "title": item[:180], "price": price.group(0) if price else None,
            "discount": discount.group(0) if discount else None,
            "currency": None, "offer_url": provider["source"], "valid_until": None,
            "source_url": provider["source"], "provider": provider["name"],
            "fetched_at": fetched_at, "affiliate_url": provider["affiliate"] or provider["website"],
        })
    return offers


def main():
    config = load_config()
    fetched_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    offers = []
    for provider in config["providers"]:
        offers.extend(extract(provider, fetch(provider["source"]), fetched_at))
        time.sleep(1)
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "offers.json").write_text(json.dumps({"fetched_at": fetched_at, "offers": offers}, indent=2), encoding="utf-8")
    print(f"Fetched {len(offers)} public offers from {len(config['providers'])} configured providers")


if __name__ == "__main__":
    main()
