from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
import random

# =========================
# ✅ CONFIG
# =========================
CHROME_DRIVER_PATH = r"chromedriver.exe"

brands = [
    "HDFC Bank", "ICICI Bank", "RBL Bank",
    "Axis Bank", "Bajaj Finance", "Angel One"
]

# =========================
# ✅ BUILD SEARCH QUERIES
# =========================
queries = []

for brand in brands:
    queries.extend([
        f'site:linkedin.com/in "{brand}" -jobs -company -official',
        f'site:linkedin.com/in "{brand}" ("loan agent" OR "DSA" OR "relationship manager" OR "sales")',
        f'site:linkedin.com/posts "{brand}" -company',
        f'site:linkedin.com/posts "{brand}" ("loan" OR "credit card" OR "finance")'
    ])

# =========================
# ✅ CHROME SETUP
# =========================
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

service = Service(CHROME_DRIVER_PATH)
driver = webdriver.Chrome(service=service, options=chrome_options)

# =========================
# ✅ HELPER FUNCTION
# =========================
def is_official(title, snippet):
    official_keywords = [
        "official", "company", "ltd", "limited",
        "bank official", "corporate", "verified"
    ]
    text = (title + " " + snippet).lower()
    return any(word in text for word in official_keywords)

# =========================
# ✅ SCRAPER START
# =========================
linkedin_data = []
seen_urls = set()

for query in queries:
    print(f"\n🔍 Searching for: {query}")

    # Pagination (5 pages)
    for page in range(0, 50, 10):
        url = f"https://www.google.com/search?q={query}&start={page}"
        driver.get(url)

        time.sleep(random.randint(3, 6))

        # Scroll for loading
        for _ in range(2):
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(random.randint(1, 3))

        results = driver.find_elements(By.CSS_SELECTOR, "div.tF2Cxc")

        for res in results:
            try:
                title = res.find_element(By.TAG_NAME, "h3").text.strip()
                link = res.find_element(By.TAG_NAME, "a").get_attribute("href")
                snippet = res.find_element(By.CSS_SELECTOR, "div.VwiC3b").text.strip()
            except:
                continue

            # Skip duplicates
            if link in seen_urls:
                continue
            seen_urls.add(link)

            # Only LinkedIn profiles/posts
            if "linkedin.com/in/" in link or "linkedin.com/posts/" in link:

                # Skip official/company pages
                if is_official(title, snippet):
                    continue

                data_type = "Profile" if "/in/" in link else "Post"

                print(f"{data_type}: {title}")
                print(f"URL: {link}")
                print(f"Description: {snippet}")
                print("-" * 80)

                linkedin_data.append({
                    "Type": data_type,
                    "Title": title,
                    "URL": link,
                    "Description": snippet,
                    "Query": query
                })

        # Human-like delay
        sleep_time = random.randint(5, 10)
        print(f"⏳ Waiting {sleep_time} sec...")
        time.sleep(sleep_time)

# =========================
# ✅ CLOSE DRIVER
# =========================
driver.quit()

# =========================
# ✅ SAVE DATA
# =========================
# TXT
with open("linkedin_data.txt", "w", encoding="utf-8") as f:
    for entry in linkedin_data:
        f.write(f"Type: {entry['Type']}\n")
        f.write(f"Title: {entry['Title']}\n")
        f.write(f"URL: {entry['URL']}\n")
        f.write(f"Description: {entry['Description']}\n")
        f.write(f"Query: {entry['Query']}\n")
        f.write("-" * 80 + "\n")

# Excel
df = pd.DataFrame(linkedin_data)
df.drop_duplicates(subset=["URL"], inplace=True)
df.to_excel("linkedin_data.xlsx", index=False)

print(f"\n✅ Done! Total results: {len(df)}")
print("📁 Saved: linkedin_data.txt & linkedin_data.xlsx")