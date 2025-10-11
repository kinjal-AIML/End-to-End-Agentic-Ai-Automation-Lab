from playwright.sync_api import sync_playwright
import time
from urllib.request import urlretrieve

with sync_playwright() as p:
    # Connect to your own local browser instance via CDP
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222", slow_mo=2000)

    # Get the default browser context or create a new one
    context = browser.contexts[0] if browser.contexts else browser.new_context()

    # Open a new page
    page = context.new_page()

    # Visit your target URL
    # page.goto("https://www.google.com/search?q=mdalamin5+github")
    # page.goto("https://www.linkedin.com/in/mdalamin5/")
    # page.goto("https://www.linkedin.com/in/abdullahmatin6920/")
    # page.goto("https://www.linkedin.com/in/rubayet-faisal-75806157/")
    # page.goto("https://www.linkedin.com/in/faiaz-hossain-nirob/")
    time.sleep(5)
    page.goto("https://arxiv.org/search")

    page.get_by_placeholder("Search term...").fill(
        "Agentic Rag"
    )

    page.get_by_role("button").get_by_text(
        "Search"
    ).nth(1).click()

    links = page.locator(
        "xpath=//a[contains(@href, 'arxiv.org/pdf')]"
    ).all()
    
    for link in links:
        url = link.get_attribute("href")
        print(url)
        urlretrieve(url, "paperData/" + url[-5:] + ".pdf")

    # Print page details
    print("Title:", page.title())
    print("URL:", page.url)
    # print("Page content:", page.content()[:500])  # Print first 500 chars
    html_content = page.content()
    title = page.title()

    # Sanitize filename (avoid special chars)
    # safe_title = "".join(c if c.isalnum() else "_" for c in title)[:60]

    # # Save the page HTML
    # file_path = f"{safe_title}.html"
    # with open(file_path, "w", encoding="utf-8") as f:
    #     f.write(html_content)

    # print(f"✅ Page saved as: {file_path}")

    # Take a screenshot
    page.screenshot(path="google-home.png")

    
    context.close()
