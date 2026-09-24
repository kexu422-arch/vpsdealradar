# VPS Deal Radar

An English-language static VPS offer directory built from public provider pages. The first version deliberately ships with no invented offers; the scheduled scraper adds only records it can trace to a public source.

## Run locally

```powershell
python scraper.py
python build.py
```

Cloudflare Pages settings: build command `python build.py`, output directory `site`.

The provider list and site rules are in `.ilang/site.ilang`; both `scraper.py` and `build.py` read it. Change a provider entry, run `python build.py`, and the provider page changes.

This project uses no runtime API keys or paid inference. Affiliate links must be added only after approval under the relevant network terms.

站点规则用 I-Lang 协议描述，见 `.ilang/site.ilang`；协议说明 ilang.ai
