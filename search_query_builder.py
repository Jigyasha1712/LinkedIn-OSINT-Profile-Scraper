from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time

# Chrome Driver Path
CHROME_DRIVER_PATH = r"chromedriver.exe"

# India-specific NeuroGum Queries
queries = [
    'site:instagram.com "cigarette" "India" daterange:20251119-20251126',
    'site:instagram.com ("cigarette" OR "smoking") ("India" OR "Indian") daterange:20251119-20251126',
    'site:instagram.com/reel "cigarette" "India" daterange:20251119-20251126',
    'site:instagram.com "cigarette" ("Delhi" OR "Mumbai" OR "Bangalore" OR "Hyderabad" OR "Kolkata") daterange:20251119-20251126',
    'site:instagram.com "cigarette" ("India" OR "New Delhi" OR "Mumbai" OR "Bengaluru") daterange:20251119-20251126',
    'site:instagram.com ("#cigarette" OR "#smoking") ("#india" OR "#indian") daterange:20251119-20251126',
    'site:instagram.com "cigarette" ("influencer" OR "creator") "India" daterange:20251119-20251126',
    'site:instagram.com "cigarette" ("nightlife" OR "street" OR "pub") "India" daterange:20251119-20251126',
    'site:instagram.com ("cigarette" AND "photography") ("India" OR "Indian") daterange:20251119-20251126',
    'site:instagram.com "cigarette" ("lifestyle" OR "daily life") "India" daterange:20251119-20251126',
    'site:instagram.com "cigarette" ("college" OR "campus" OR "students") "India" daterange:20251119-20251126',
    'site:instagram.com ("smoke" AND "edit") ("India" OR "Indian") daterange:20251119-20251126',
    'site:instagram.com "cigarette" ("travel" OR "mountain" OR "roadtrip") "India" daterange:20251119-20251126',
    'site:instagram.com "cigarette" ("boy" OR "boys") ("India" OR "Indian") daterange:20251119-20251126',
    'site:instagram.com "cigarette" ("dhua" OR "bidi" OR "sutta") "India" daterange:20251119-20251126'
]

# Chrome setup
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")

service = Service(CHROME_DRIVER_PATH)
driver = webdriver.Chrome(service=service, options=chrome_options)

instagram_data = []

# Loop all queries
for query in queries:
    print(f"\n🔍 Searching for: {query}")
    driver.get(f"https://www.google.com/search?q={query}")
    time.sleep(3)

    # --- 7 Pages Scraping ---
    for page in range(1, 8):  # 7 pages
        print(f"📄 Scraping Page {page}")

        # Scroll
        for _ in range(3):
            driver.execute_script("window.scrollBy(0, 1500);")
            time.sleep(1.5)

        results = driver.find_elements(By.CSS_SELECTOR, "div.tF2Cxc")

        for res in results:
            try:
                title = res.find_element(By.TAG_NAME, "h3").text.strip()
                link = res.find_element(By.TAG_NAME, "a").get_attribute("href")
                snippet = res.find_element(By.CSS_SELECTOR, "div.VwiC3b").text.strip()
            except:
                continue

            if "instagram.com" in link:
                print(f"\nTitle: {title}")
                print(f"URL: {link}")
                print(f"Description: {snippet}")
                print("-" * 70)

                instagram_data.append({
                    "Title": title,
                    "URL": link,
                    "Description": snippet,
                    "Query": query,
                    "Page": page
                })

        # GO TO NEXT PAGE
        try:
            next_button = driver.find_element(By.XPATH, "//a[@id='pnnext']")
            next_button.click()
            time.sleep(4)
        except:
            print("⚠ No more pages available.")
            break

    time.sleep(5)

driver.quit()

# Save results
df = pd.DataFrame(instagram_data)
df.to_excel("Instagram_india.xlsx", index=False)

with open("Instagram_india.txt", "w", encoding="utf-8") as f:
    for entry in instagram_data:
        f.write(f"Title: {entry['Title']}\n")
        f.write(f"URL: {entry['URL']}\n")
        f.write(f"Description: {entry['Description']}\n")
        f.write(f"Query: {entry['Query']}\n")
        f.write(f"Page: {entry['Page']}\n")
        f.write("-" * 80 + "\n")

print(f"\n✅ DONE — Total Instagram Results: {len(instagram_data)}")
print("📁 Saved: neurogum_india_reviews_positive.xlsx")
print("📄 Saved: neurogum_india_reviews_positive.txt")
