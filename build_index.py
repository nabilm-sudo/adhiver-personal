import os
import json
from datetime import datetime

CAPTURE_DIR = "captures"
OUTPUT = "browse.html"

def gather_data():
    brands = {}
    for domain in sorted(os.listdir(CAPTURE_DIR)):
        domain_path = os.path.join(CAPTURE_DIR, domain)
        if not os.path.isdir(domain_path) or domain.startswith("."):
            continue
        dates = []
        for d in sorted(os.listdir(domain_path), reverse=True):
            shot = os.path.join(domain_path, d, "screenshot.png")
            if os.path.exists(shot):
                dates.append({"date": d, "path": shot})
        if dates:
            brands[domain] = dates
    return brands

def build_html(brands):
    cards = ""
    for domain, captures in brands.items():
        latest = captures[0]
        history = ""
        for c in captures:
            history += f'''
            <div class="history-item" onclick="showFull('{c["path"]}')">
                <img src="{c["path"]}" loading="lazy"/>
                <span>{c["date"]}</span>
            </div>'''

        cards += f'''
        <div class="card">
            <div class="card-header" onclick="toggle(this)">
                <h2>{domain}</h2>
                <span class="badge">{len(captures)} capture{"s" if len(captures)>1 else ""}</span>
            </div>
            <div class="card-latest" onclick="showFull('{latest["path"]}')">
                <img src="{latest["path"]}" loading="lazy"/>
                <span class="date">{latest["date"]}</span>
            </div>
            <div class="history" style="display:none">{history}</div>
        </div>'''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Adhiver — Homepage Archive</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #0a0a0a; color: #e0e0e0; padding: 24px; }}
  h1 {{ font-size: 1.5rem; margin-bottom: 8px; color: #fff; }}
  .subtitle {{ color: #888; margin-bottom: 24px; font-size: 0.9rem; }}
  .filter {{ margin-bottom: 24px; }}
  .filter input {{ padding: 10px 16px; border-radius: 8px; border: 1px solid #333; background: #141414; color: #fff; font-size: 0.95rem; width: 300px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(420px, 1fr)); gap: 20px; }}
  .card {{ background: #141414; border-radius: 12px; border: 1px solid #222; overflow: hidden; }}
  .card-header {{ display: flex; justify-content: space-between; align-items: center; padding: 14px 18px; cursor: pointer; }}
  .card-header:hover {{ background: #1a1a1a; }}
  .card-header h2 {{ font-size: 1rem; font-weight: 600; }}
  .badge {{ background: #2a2a2a; color: #aaa; font-size: 0.75rem; padding: 3px 10px; border-radius: 20px; }}
  .card-latest {{ cursor: pointer; padding: 0 18px 14px; position: relative; }}
  .card-latest img {{ width: 100%; border-radius: 8px; max-height: 300px; object-fit: cover; object-position: top; }}
  .card-latest .date {{ position: absolute; bottom: 22px; right: 26px; background: rgba(0,0,0,0.7); padding: 3px 10px; border-radius: 6px; font-size: 0.75rem; }}
  .history {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 10px; padding: 0 18px 18px; }}
  .history-item {{ cursor: pointer; text-align: center; }}
  .history-item img {{ width: 100%; border-radius: 6px; max-height: 120px; object-fit: cover; object-position: top; }}
  .history-item span {{ font-size: 0.7rem; color: #888; }}
  .overlay {{ display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.92); z-index: 100; justify-content: center; align-items: flex-start; padding: 40px; overflow: auto; }}
  .overlay.active {{ display: flex; }}
  .overlay img {{ max-width: 95%; border-radius: 8px; }}
  .overlay .close {{ position: fixed; top: 16px; right: 24px; color: #fff; font-size: 2rem; cursor: pointer; z-index: 101; }}
  .stats {{ display: flex; gap: 24px; margin-bottom: 24px; }}
  .stat {{ background: #141414; border: 1px solid #222; border-radius: 10px; padding: 14px 20px; }}
  .stat-val {{ font-size: 1.3rem; font-weight: 700; color: #fff; }}
  .stat-label {{ font-size: 0.75rem; color: #888; margin-top: 2px; }}
</style>
</head>
<body>
  <h1>Adhiver — Homepage Archive</h1>
  <p class="subtitle">Updated {datetime.utcnow().strftime("%d %b %Y")}</p>
  <div class="stats">
    <div class="stat"><div class="stat-val">{len(brands)}</div><div class="stat-label">Brands</div></div>
    <div class="stat"><div class="stat-val">{sum(len(v) for v in brands.values())}</div><div class="stat-label">Captures</div></div>
  </div>
  <div class="filter"><input type="text" placeholder="Filter brands..." oninput="filterCards(this.value)"/></div>
  <div class="grid" id="grid">{cards}</div>
  <div class="overlay" id="overlay" onclick="closeFull()">
    <span class="close">&times;</span>
    <img id="overlay-img" src=""/>
  </div>
  <script>
    function toggle(el) {{
      const hist = el.parentElement.querySelector('.history');
      hist.style.display = hist.style.display === 'none' ? 'grid' : 'none';
    }}
    function showFull(src) {{
      document.getElementById('overlay-img').src = src;
      document.getElementById('overlay').classList.add('active');
    }}
    function closeFull() {{
      document.getElementById('overlay').classList.remove('active');
    }}
    function filterCards(val) {{
      document.querySelectorAll('.card').forEach(c => {{
        c.style.display = c.querySelector('h2').textContent.toLowerCase().includes(val.toLowerCase()) ? '' : 'none';
      }});
    }}
    document.addEventListener('keydown', e => {{ if(e.key==='Escape') closeFull(); }});
  </script>
</body>
</html>'''
    with open(OUTPUT, "w") as f:
        f.write(html)
    print(f"Built {OUTPUT} — {len(brands)} brands")

if __name__ == "__main__":
    brands = gather_data()
    build_html(brands)
