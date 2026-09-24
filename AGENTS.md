# ILANG
TYPE: project-guardrails
PROJECT: VPS Deal Radar
LANG: zh

::STATE{@PROJECT, role:public-source static VPS offers site}
::RULE{scraper and build must read .ilang/site.ilang; changing providers there must change output}
::RULE{data must come from public provider pages permitted by robots.txt}
::BOUNDARY{never:编优惠 编价格 编佣金 绕过登录或反爬 刷量|scope:permanent}
::ALLOW{modify: scraper.py build.py templates/ .ilang/ data/ .github/ README.md}
