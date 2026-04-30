import os
import yaml
import csv
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

CAPTURE_DIR = "captures"
LOG_FILE = os.path.join(CAPTURE_DIR, "log.csv")
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")

COOKIE_SELECTORS = [
    # English
    "button:has-text('Accept all')",
    "button:has-text('Accept All')",
    "button:has-text('Accept All Cookies')",
    "button:has-text('Accept all cookies')",
    "button:has-text('Accept Cookies')",
    "button:has-text('Accept cookies')",
    "button:has-text('Accept')",
    "button:has-text('Agree')",
    "button:has-text('Agree & Continue')",
    "button:has-text('Allow all')",
    "button:has-text('Allow All')",
    "button:has-text('Allow all cookies')",
    "button:has-text('OK')",
    "button:has-text('Got it')",
    "button:has-text('I understand')",
    "button:has-text('Continue')",
    "button:has-text('Yes, I agree')",
    # French
    "button:has-text('Tout accepter')",
    "button:has-text('Accepter tout')",
    "button:has-text('Accepter')",
    "button:has-text('Autoriser')",
    "button:has-text('J\\'accepte')",
    "button:has-text('Continuer')",
    # German
    "button:has-text('Alle akzeptieren')",
    "button:has-text('Alle annehmen')",
    "button:has-text('Akzeptieren')",
    "button:has-text('Einverstanden')",
    "button:has-text('Zustimmen')",
    "button:has-text('Alles erlauben')",
    # Generic selectors
    "[id*='accept' i]",
    "[id*='cookie' i][id*='accept' i]",
    "[class*='accept' i]",
    "[data-action='accept']",
    "[aria-label*='accept' i]",
    "[aria-label*='cookie' i][role='button']",
    "#onetrust-accept-btn-handler",
    ".onetrust-accept-btn-handler",
    "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll",
    "#didomi-notice-agree-button",
    ".cc-accept",
    ".cc-allow",
    ".cookie-consent-accept",
    "[data-testid='cookie-accept']",
    "[data-cy='cookie-accept']",
]

def load_sites():
    with open("sites.yaml", "r") as f:
        return yaml.safe_load(f)

def dismiss_cookies(page):
    # Try main page first
    if _try_dismiss(page):
        return True
    # Try inside iframes (many cookie banners live in iframes)
    for frame in page.frames:
        if frame == page.main_frame:
            continue
        try:
            if _try_dismiss(frame):
                return True
        except:
            continue
    return False

def _try_dismiss(context):
    for selector in COOKIE_SELECTORS:
        try:
            btn = context.locator(selector).first
            if btn.is_visible(timeout=500):
                btn.click()
                context.wait_for_timeout(500)
                return True
        except:
            continue
    return False

def scrape_site(browser, site, log_rows):
    url = site["url"]
    name = site["name"]
    domain = url.replace("https://", "").replace("http://", "").split("/")[0].replace("www.", "")
    if site.get("local_only") and os.environ.get("GITHUB_ACTIONS"):
        print(f"  SKIP {name} — local only (blocked from CI)")
        return
    out_dir = os.path.join(CAPTURE_DIR, domain, TODAY)

    if os.path.exists(out_dir):
        print(f"  SKIP {name} — already captured today")
        return

    os.makedirs(out_dir, exist_ok=True)
    status = "ok"
    error_msg = ""

    try:
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        stealth_sync(page)
        try:
            page.goto(url, wait_until="networkidle", timeout=15000)
        except:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)

        # Try dismissing cookies up to 3 times (some banners appear with delay)
        for attempt in range(3):
            if dismiss_cookies(page):
                page.wait_for_timeout(1000)
                break
            if attempt < 2:
                page.wait_for_timeout(1500)

        if site.get("local_only"):
            page.wait_for_timeout(8000)
        else:
            page.wait_for_timeout(1000)
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
        is_ci = os.environ.get("GITHUB_ACTIONS")
        browser = p.chromium.launch(headless=True if is_ci else False)
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
