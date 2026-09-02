
import os
import re
import json
import time
import warnings
import pandas as pd
from time import sleep
from pathlib import Path
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

warnings.filterwarnings("ignore")
load_dotenv()

EMAIL = os.getenv("EMAIL", "ridhimasharma54321@gmail.com")
PASSWORD = os.getenv("PASSWORD", "Riddhi@123#!")

INPUT_XLSX = "linkedin_profiles.xlsx"   # must have a column named 'URL'
OUTPUT_DIR = Path("data")
PROFILES_DIR = OUTPUT_DIR / "profiles"
COMBINED_XLSX = OUTPUT_DIR / "combined_profiles.xlsx"
PROFILES_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------- helpers ----------
def sanitize_filename(name: str) -> str:
    name = name.strip()
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = re.sub(r'\s+', '_', name)
    if not name:
        name = "profile"
    return name[:120]

def scroll_to_end(driver, pause=0.8, max_attempts=40):
    """Scroll to bottom slowly until no change in page height."""
    last_height = driver.execute_script("return document.body.scrollHeight")
    attempts = 0
    while attempts < max_attempts:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep(pause)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            attempts += 1
            sleep(0.3)
        else:
            last_height = new_height
            attempts = 0
    # small extra scroll for safety
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    sleep(0.7)

def click_all_show_more(driver):
    """Click on visible show-more buttons (if any) to expand long text."""
    try:
        # common class name, also try XPath for buttons that contain 'see more'
        buttons = driver.find_elements(By.XPATH, "//button[contains(., 'See more') or contains(., 'Show more') or contains(@class,'inline-show-more-text__button')]")
        for b in buttons:
            try:
                if b.is_displayed():
                    driver.execute_script("arguments[0].click();", b)
                    sleep(0.4)
            except Exception:
                continue
    except Exception:
        pass

def safe_text(elem):
    return elem.get_text().strip() if elem else ""

# ---------- scraping logic ----------
def parse_profile_html(html, URL):
    soup = BeautifulSoup(html, "lxml")
    profile = {"URL": URL}

    # name
    name_sel = soup.find('h1')  # fallback: pick first h1
    profile['name'] = safe_text(name_sel) if name_sel else ""

    # headline (text-body-medium or meta)
    headline = soup.find(lambda tag: tag.name == "div" and 'text-body-medium' in (tag.get("class") or []))
    if not headline:
        # fallback: look for <div> with role or near name
        headline = soup.find('div', {'class': re.compile(r'headline|title|pv-top-card--.*', re.I)})
    profile['headline'] = safe_text(headline) if headline else ""

    # about / summary
    about = soup.find('div', {'class': re.compile(r'display-flex.*pv-top-card|about|summary|description', re.I)})
    # try a broader search if exact class missing
    if not about:
        about = soup.find('div', string=True, attrs={'class': re.compile(r'pv-about-section|inline-show-more-text__content', re.I)}) if soup.find_all() else None
    # Better fallback: find element with 'About' heading then following sibling
    if not about:
        about_heading = soup.find(string=re.compile(r'About', re.I))
        if about_heading and about_heading.parent:
            # sibling or next element
            candidate = about_heading.parent.find_next_sibling()
            if candidate:
                about = candidate
    profile['about'] = safe_text(about) if about else ""

    # sections helper
    def find_section_by_id_fragment(soup_obj, frag):
        # search for section or div with id or aria-label containing frag
        sec = soup_obj.find(lambda tag: (tag.name in ["section", "div"]) and (tag.get("id") and frag in tag.get("id")) )
        if sec:
            return sec
        sec = soup_obj.find(lambda tag: (tag.name in ["section", "div"]) and (tag.get("aria-label") and frag in tag.get("aria-label")))
        if sec:
            return sec
        # try by heading text
        header = soup_obj.find(string=re.compile(fr"^{frag}$", re.I))
        if header:
            return header.parent.find_next_sibling() if header.parent else None
        return None

    # EXPERIENCES
    exp_section = find_section_by_id_fragment(soup, "experience")
    experiences = []
    if exp_section:
        # experiences often in li or div blocks
        blocks = exp_section.find_all(['li','div'], recursive=True)
        # heuristics: pick blocks that contain 'visually-hidden' spans or role=article
        candidate_blocks = []
        for b in blocks:
            if b.find('span', {'class': 'visually-hidden'}) or b.get('role') == 'article' or b.find('h3'):
                candidate_blocks.append(b)
        # parse candidate blocks
        for b in candidate_blocks:
            try:
                title = b.find(['h3','span'], {'class': re.compile(r'visually-hidden|t-16|t-14', re.I)})
                company = b.find(['p','span','h4'], string=True)
                time_el = b.find(string=re.compile(r'\d{4}|mo|yr', re.I))
                exp = {
                    "title": safe_text(b.find('h3')) or safe_text(title) or "",
                    "company": safe_text(b.find('p')) or (safe_text(company) if company else ""),
                    "duration": time_el.strip() if time_el else ""
                }
                experiences.append(exp)
            except Exception:
                continue
    profile['experience'] = experiences

    # EDUCATION
    edu_section = find_section_by_id_fragment(soup, "education")
    educations = []
    if edu_section:
        items = edu_section.find_all(['li','div'])
        for it in items:
            spans = it.find_all('span')
            if not spans:
                continue
            educations.append({
                "school": safe_text(spans[0]) if len(spans) > 0 else "",
                "degree": safe_text(spans[1]) if len(spans) > 1 else "",
                "duration": safe_text(spans[2]) if len(spans) > 2 else ""
            })
    profile['education'] = educations

    # LICENSES & CERTS
    cert_section = find_section_by_id_fragment(soup, "licenses")
    certs = []
    if cert_section:
        items = cert_section.find_all(['li','div'])
        for it in items:
            spans = it.find_all('span')
            if not spans: continue
            certs.append({
                "name": safe_text(spans[0]) if len(spans) > 0 else "",
                "issuer": safe_text(spans[1]) if len(spans) > 1 else "",
                "date": safe_text(spans[2]) if len(spans) > 2 else ""
            })
    profile['licenses'] = certs

    # PROJECTS
    proj_section = find_section_by_id_fragment(soup, "projects")
    projects = []
    if proj_section:
        items = proj_section.find_all(['li','div'])
        for it in items:
            spans = it.find_all('span')
            if not spans: continue
            projects.append({
                "name": safe_text(spans[0]) if len(spans)>0 else "",
                "duration": safe_text(spans[1]) if len(spans)>1 else "",
                "description": safe_text(spans[2]) if len(spans)>2 else ""
            })
    profile['projects'] = projects

    # COURSES
    course_section = find_section_by_id_fragment(soup, "courses")
    courses = []
    if course_section:
        items = course_section.find_all(['li','div'])
        for it in items:
            spans = it.find_all('span')
            if not spans: continue
            courses.append({
                "course_name": safe_text(spans[0]) if len(spans)>0 else "",
                "associated_with": safe_text(spans[1]) if len(spans)>1 else ""
            })
    profile['courses'] = courses

    # HONORS & AWARDS
    honors_section = find_section_by_id_fragment(soup, "honors")
    honors = []
    if honors_section:
        items = honors_section.find_all('span')
        honors = [safe_text(i) for i in items if safe_text(i)]
    profile['honors_and_awards'] = honors

    return profile

# ---------- main ----------
def main():
    # open webdriver
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless=new")  # comment out if you want to see browser
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)

    # login
    driver.get("https://www.linkedin.com/login")
    try:
        wait.until(EC.presence_of_element_located((By.ID, "username")))
        driver.find_element(By.ID, "username").send_keys(EMAIL)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.ID, "password").submit()
        time.sleep(3)
    except Exception as e:
        print("Login step problem (maybe already logged in):", e)

    # read input Excel
    if not os.path.exists(INPUT_XLSX):
        print(f"Input file {INPUT_XLSX} not found. Create an Excel with a column named 'URL'.")
        driver.quit()
        return

    df = pd.read_excel(INPUT_XLSX)
    if 'URL' not in df.columns:
        print("Input Excel must contain a column named 'URL'")
        driver.quit()
        return

    rows = []
    for idx, row in df.iterrows():
        profile_URL = str(row['URL']).strip()
        if not profile_URL or profile_URL.lower() in ['nan','none']:
            continue
        print(f"\n>> [{idx+1}/{len(df)}] Visiting: {profile_URL}")
        try:
            driver.get(profile_URL)
            # ensure page loads
            time.sleep(2)

            # scroll to end to lazy-load sections
            scroll_to_end(driver, pause=0.7, max_attempts=30)
            # click-show-more to expand text
            click_all_show_more(driver)
            # small wait for dynamic content
            time.sleep(1.2)

            html = driver.page_source
            profile = parse_profile_html(html, profile_URL)

            # ensure name exists (if empty, try alternative parse)
            if not profile.get('name'):
                # try to get from top card
                try:
                    topname = driver.find_element(By.XPATH, "//div[contains(@class,'pv-text-details__left-panel')]//h1")
                    profile['name'] = topname.text.strip()
                except Exception:
                    pass

            # Save per-profile JSON
            safe_name = sanitize_filename(profile.get('name') or ("profile_"+str(idx+1)))
            json_path = PROFILES_DIR / f"{safe_name}.json"
            with open(json_path, "w", encoding="utf-8") as jf:
                json.dump(profile, jf, indent=4, ensure_ascii=False)

            # Flatten some fields for combined Excel (lists -> JSON strings)
            flat = {
                "name": profile.get("name", ""),
                "URL": profile.get("URL", profile_URL),
                "headline": profile.get("headline", ""),
                "about": profile.get("about", "")
            }
            # store lists as JSON strings
            for k in ["experience","education","licenses","projects","courses","honors_and_awards"]:
                flat[k] = json.dumps(profile.get(k, []), ensure_ascii=False)

            rows.append(flat)
            print(f"Saved: {json_path}")

        except Exception as e:
            print("Error fetching profile:", e)
        # wait 10 seconds between profiles
        print("Waiting 10 seconds before next profile...")
        time.sleep(10)

    # save combined excel
    if rows:
        combined_df = pd.DataFrame(rows)
        combined_df.to_excel(COMBINED_XLSX, index=False)
        print(f"\n✅ Combined Excel saved to: {COMBINED_XLSX}")
    else:
        print("\nNo profiles scraped.")

    driver.quit()
    print("Done.")

if __name__ == "__main__":
    main()
