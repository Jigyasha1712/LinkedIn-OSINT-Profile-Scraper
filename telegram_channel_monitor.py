from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
import re

# ✅ ChromeDriver path
CHROME_DRIVER_PATH = r"chromedriver.exe"

# ✅ Direct Telegram-focused queries
queries = [
    # Alcohol / Party
    '"party drink india" site:t.me',
    '"beer lovers india" site:t.me',
    '"vodka group india" site:t.me',
    '"alcohol lovers india" site:t.me',
    '"weekend drinkers india" site:t.me',
    '"party freaks india" site:t.me',
    '"night life india" site:t.me',
    '"fun and chill india" site:t.me',
    '"hangout india" site:t.me',
    '"vibe with us india" site:t.me',

    # Smoking
    '"smokers india" site:t.me',
    '"smoking adda" site:t.me',
    '"cigarette lovers india" site:t.me',
    '"smoking zone india" site:t.me',
    '"chain smokers india" site:t.me',

    # Weed / Discussion (Awareness only)
    '"weed india discussion" site:t.me',
    '"stoners india" site:t.me',
    '"weed community india" site:t.me',
    '"420 india" site:t.me',
    '"ganja lovers india" site:t.me',
]

# ✅ Chrome setup
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--disable-notifications")

service = Service(CHROME_DRIVER_PATH)
driver = webdriver.Chrome(service=service, options=chrome_options)

telegram_data = []

def is_group_or_channel(url: str) -> bool:
    """
    ✅ Filter only valid Telegram groups or channels
    - group links often have /joinchat/, /+/, or /g/
    - channel links usually have /c/, /s/, or simple usernames (without ?start or ?attach)
    """
    group_patterns = [
        r"t\.me/joinchat/",
        r"t\.me/\+",
        r"t\.me/[A-Za-z0-9_]+$",
        r"t\.me/[A-Za-z0-9_]+/$",
        r"t\.me/s/[A-Za-z0-9_]+"
    ]
    for pattern in group_patterns:
        if re.search(pattern, url):
            return True
    return False


def scrape_current_page(query):
    """Scrape Telegram links from the current Google page"""
    time.sleep(3)
    for _ in range(2):  # Scroll for better results
        driver.execute_script("window.scrollBy(0, 1200);")
        time.sleep(1.5)

    results = driver.find_elements(By.CSS_SELECTOR, "div.tF2Cxc")

    for res in results:
        try:
            title = res.find_element(By.TAG_NAME, "h3").text.strip()
            link = res.find_element(By.TAG_NAME, "a").get_attribute("href")
            snippet = res.find_element(By.CSS_SELECTOR, "div.VwiC3b").text.strip()
        except:
            continue

        # ✅ Only Telegram group/channel links
        if "https://t.me/" in link and is_group_or_channel(link):
            print(f"Title: {title}")
            print(f"URL: {link}")
            print(f"Description: {snippet}")
            print("-" * 80)

            telegram_data.append({
                "Title": title,
                "URL": link,
                "Description": snippet,
                "Query": query
            })


for query in queries:
    print(f"\n🔍 Searching for: {query}")
    driver.get(f"https://www.google.com/search?q={query}")
    time.sleep(3)

    page_num = 1
    max_pages = 3  # ✅ Crawl 3 pages per query

    while page_num <= max_pages:
        print(f"📄 Page {page_num} for: {query}")
        scrape_current_page(query)

        try:
            next_button = driver.find_element(By.ID, "pnnext")
            next_button.click()
            page_num += 1
            time.sleep(3)
        except:
            print("🚫 No more pages found.")
            break

    print("⏳ Waiting 8 seconds before next query...")
    time.sleep(8)

driver.quit()

# ✅ Save to text
with open("telegram_groups_channels.txt", "w", encoding="utf-8") as f:
    for entry in telegram_data:
        f.write(f"Title: {entry['Title']}\n")
        f.write(f"URL: {entry['URL']}\n")
        f.write(f"Description: {entry['Description']}\n")
        f.write(f"Query: {entry['Query']}\n")
        f.write("-" * 80 + "\n")

# ✅ Save to Excel
df = pd.DataFrame(telegram_data)
df.to_excel("telegram_groups_channels.xlsx", index=False)

print(f"\n✅ Done! Total Telegram groups/channels found: {len(telegram_data)}")
print("📁 Saved as telegram_groups_channels.txt and telegram_groups_channels.xlsx")
