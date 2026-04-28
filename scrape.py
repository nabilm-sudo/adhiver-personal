import os
import yaml
import csv
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

CAPTURE_DIR = "captures"
LOG_FILE = os.path.join(CAPTURE_DIR, "log.csv")
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")

COOKIE_SELECTORS = [
    "button:has-text('Accept all')",
    "button:has-text('Accept All')",
    "button:has-text('Accept')",
    "button:has-text('OK')",
    "button:has-text('Agree')",
    "button:has-text('Got it')",
    "button:has-text('Tout accepter')",
    "button:has-text('Accepter')",
    "[id*='accept']",
    "[class*='accept']",
]

def load_sites():
    with open("sites.yaml", "r") as f:
        return yaml.safe_load(f)

def dismiss_cookies(page):
    for selector in COOKIE_SELECTORS:
        try:
            btn = page.locator(selector).first
            if btn.is_visible(timeout=1000):
                btn.click()
                page.wait_for_timeout(500)
                return True
        except:
            continue
    return False

def scrape_site(browser, site, log_rows):
    url = site["url"]
    name = site["name"]
    domain = url.replace("https://", "").replace("http://", "").split("/")[0].replace("www.", "")
    out_dir = os.path.join(CAPTURE_DIR, domain, TODAY)

    if os.path.exists(out_dir):
        print(f"  SKIP {name} — already captured today")
        return

    os.makedirs(out_dir, exist_ok=True)
    status = "ok"
    error_msg = ""

    try:
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(url, wait_until="networkidle", timeout=30000)
        dismiss_cookies(page)
        page.wait_for_timeout(2000)

        page.screenshot(path=os.path.join(out_dir, "screenshot.png"), full_page=True)
        html = page.content()
        with open(os.path.join(out_dir, "page.html"), "w", encoding="utf-8") as f:
            f.write(html)

        print(f"  OK   {name}")
        page.close()
    except Exception as e:
        status = "error"
        error_msg = str(e)[:200]
        print(f"  FAIL {name}: {error_msg}")

    log_rows.append([TODAY, name, domain, url, status, error_msg])

def main():
    sites = load_sites()
    os.makedirs(CAPTURE_DIR, exist_ok=True)
    log_rows = []

    print(f"Scraping {len(sites)} sites — {TODAY}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for site in sites:
            scrape_site(browser, site, log_rows)
        browser.close()

    write_header = not os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(["date", "name", "domain", "url", "status", "error"])
        w.writerows(log_rows)

    print("Done.")

if __name__ == "__main__":
    main()
