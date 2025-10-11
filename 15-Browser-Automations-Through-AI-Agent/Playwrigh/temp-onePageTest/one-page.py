from playwright.sync_api import sync_playwright
import time
import os

# List of URLs to process
urls = [
    "https://www.google.com/search?q=mdalamin5+github",
    "https://www.wikipedia.org",
    "https://facebook.com",
    # ... add your 800+ links here
]

with sync_playwright() as p:
    # Connect to your local browser
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")

    # Reuse the same browser context and tab
    context = browser.contexts[0] if browser.contexts else browser.new_context()
    page = context.pages[0] if context.pages else context.new_page()

    # Ensure output directory exists
    os.makedirs("html_pages", exist_ok=True)

    for i, url in enumerate(urls, start=1):
        print(f"[{i}/{len(urls)}] Visiting: {url}")

        try:
            page.goto(url, timeout=60000)  # 60s timeout per page
            time.sleep(2)  # Optional: allow dynamic JS to load

            title = page.title() or "no_title"
            safe_title = "".join(c if c.isalnum() else "_" for c in title)[:60]
            file_path = f"html_pages/{i:03d}_{safe_title}.html"

            # Save the HTML content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(page.content())

            print(f"✅ Saved: {file_path}")

        except Exception as e:
            print(f"❌ Failed: {url} -> {e}")

    print("🎯 All pages processed.")
    context.close()
