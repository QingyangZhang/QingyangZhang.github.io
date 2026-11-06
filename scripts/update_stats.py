"""Fetch Google Scholar citations and GitHub stars, write data/stats.json."""
import json, os, re, html, urllib.request

SCHOLAR_ID = "64vwsrsAAAAJ"
PAPERS = {  # key -> (title prefix in Scholar, lower-case), GitHub repo
    "empo":   ("right question is already half the answer", "QingyangZhang/EMPO"),
    "come":   ("come: test-time adaption", "BlueWhaleLab/COME"),
    "dul":    ("the best of both worlds", "QingyangZhang/DUL"),
    "qmf":    ("provable dynamic fusion", "QingyangZhang/QMF"),
    "cml":    ("calibrating multimodal learning", "QingyangZhang/CML"),
    "survey": ("multimodal fusion on low-quality data", "QingyangZhang/awesome-low-quality-multimodal-learning"),
}
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "stats.json")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"


def get(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")


old = json.load(open(OUT)) if os.path.exists(OUT) else {"papers": {}}
papers = old.get("papers", {})
total = old.get("total_citations")

# Google Scholar
try:
    s = get(f"https://scholar.google.com/citations?user={SCHOLAR_ID}&hl=en&pagesize=100")
    rows = re.findall(r'class="gsc_a_at"[^>]*>(.*?)</a>.*?class="gsc_a_ac[^"]*"[^>]*>(\d*)</a>', s, re.S)
    for title, c in rows:
        t = html.unescape(title).lower()
        for k, (prefix, _) in PAPERS.items():
            if t.startswith(prefix):
                papers.setdefault(k, {})["citations"] = int(c or 0)
    m = re.findall(r'class="gsc_rsb_std">(\d+)', s)
    if m:
        total = int(m[0])
    print("scholar ok", len(rows))
except Exception as e:
    print("scholar failed, keep old values:", e)

# GitHub stars
hdr = {"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"} if os.environ.get("GITHUB_TOKEN") else {}
for k, (_, repo) in PAPERS.items():
    try:
        d = json.loads(get(f"https://api.github.com/repos/{repo}", hdr))
        papers.setdefault(k, {})["stars"] = d["stargazers_count"]
    except Exception as e:
        print("github failed", repo, e)

from datetime import datetime, timezone
json.dump({"updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
           "total_citations": total, "papers": papers}, open(OUT, "w"), indent=2)
print(open(OUT).read())
