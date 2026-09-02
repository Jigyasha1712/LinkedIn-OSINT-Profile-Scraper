from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time

# ✅ Update your ChromeDriver path
CHROME_DRIVER_PATH = r"chromedriver.exe"

# ✅ Your Google search queries
queries = [ 'site:linkedin.com/in "data annotation" AND ("machine learning" OR "AI")', 'site:linkedin.com/in "API developer" OR "API automation" OR "REST API"', 'site:linkedin.com/in ("AI automation" OR "workflow automation" OR "RPA" OR "bot developer")', 'site:linkedin.com/in ("data annotation" OR "AI automation") "India"', 'site:linkedin.com/in ("label studio" OR "roboflow" OR "superannotate") "data annotation"', 'site:linkedin.com/in ("openai api" OR "langchain" OR "fastapi") "AI automation"', 'site:linkedin.com/in "data annotation specialist" "freelancer" India' ]


# ✅ Chrome setup
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")

service = Service(CHROME_DRIVER_PATH)
driver = webdriver.Chrome(service=service, options=chrome_options)

# ✅ To store all profile data
linkedin_data = []

for query in queries:
    print(f"\n🔍 Searching for: {query}")
    driver.get(f"https://www.google.com/search?q={query}")
    time.sleep(3)

    # scroll for better results
    for _ in range(2):
        driver.execute_script("window.scrollBy(0, 1000);")
        time.sleep(2)

    # get all Google results
    results = driver.find_elements(By.CSS_SELECTOR, "div.tF2Cxc")

    for res in results:
        try:
            title = res.find_element(By.TAG_NAME, "h3").text.strip()
            link = res.find_element(By.TAG_NAME, "a").get_attribute("href")
            snippet = res.find_element(By.CSS_SELECTOR, "div.VwiC3b").text.strip()
        except:
            continue

        if "linkedin.com/in/" in link:
            print(f"Title: {title}")
            print(f"URL: {link}")
            print(f"Description: {snippet}")
            print("-" * 80)

            linkedin_data.append({
                "Title": title,
                "URL": link,
                "Description": snippet,
                "Query": query
            })

    # ✅ Wait 10 seconds before next search
    print("⏳ Waiting 10 seconds before next query...")
    time.sleep(10)

driver.quit()

# ✅ Save to text file
with open("linkedin_profiles.txt", "w", encoding="utf-8") as f:
    for entry in linkedin_data:
        f.write(f"Title: {entry['Title']}\n")
        f.write(f"URL: {entry['URL']}\n")
        f.write(f"Description: {entry['Description']}\n")
        f.write(f"Query: {entry['Query']}\n")
        f.write("-" * 80 + "\n")

# ✅ Save to Excel
df = pd.DataFrame(linkedin_data)
df.to_excel("linkedin_profiles.xlsx", index=False)

print(f"\n✅ Done! Total LinkedIn profiles found: {len(linkedin_data)}")
print("📁 Text file saved as linkedin_profiles.txt")
print("📊 Excel file saved as linkedin_profiles.xlsx")
