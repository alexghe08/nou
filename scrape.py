import os
import re
import time
from playwright.sync_api import sync_playwright

# Configuration
BASE_URL = "https://achizitiipublice.gov.ro/matrix/cell/72/1"
ROOT_DIR = "72__Executie_lucrari"

# Directory Mapping based on keywords
DIR_MAPPING = {
    "instructiuni": "01_Sectiunea_I_Instructiuni",
    "fisa de date": "01_Sectiunea_I_Instructiuni",
    "caiet de sarcini": "02_Sectiunea_II_CaietSarcini",
    "contract": "03_Sectiunea_III_Contracte",
    "acord": "03_Sectiunea_III_Contracte", # Note: Framework agreements might land here if not carefully filtered
    "formular": "06_Sectiunea_VI_Formulare",
    "factori": "07_Factori_Evaluare",
    "evaluare": "07_Factori_Evaluare"
}

def normalize_filename(text):
    return re.sub(r'[\\/*?:"<>|]', "", text)

def get_target_directory(filename):
    lower_name = filename.lower()
    for key, folder in DIR_MAPPING.items():
        if key in lower_name:
            return os.path.join(ROOT_DIR, folder)
    return os.path.join(ROOT_DIR, "CleanedDocs") # Fallback

def run():
    with sync_playwright() as p:
        print(f"Launching browser to scrape {BASE_URL}...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        try:
            page.goto(BASE_URL, timeout=30000)
            print("Page loaded.")

            # The memory states the container has a typo: #documnets
            selector = "#documnets"
            try:
                page.wait_for_selector(selector, timeout=10000)
                print(f"Found container {selector}")
            except:
                print(f"Container {selector} not found. Trying fallback selectors or exiting.")
                # Fallback for robustness
                if page.query_selector("#documents"):
                    selector = "#documents"
                else:
                    print("No document container found.")
                    # Take screenshot for debug
                    # page.screenshot(path="debug_scrape.png")
                    browser.close()
                    return

            # Find download links
            # Typically these are <a> tags. We assume they have some text indicating the document name.
            links = page.query_selector_all(f"{selector} a")

            print(f"Found {len(links)} potential document links.")

            for i, link in enumerate(links):
                text = link.inner_text().strip()
                href = link.get_attribute("href")

                if not href or "Download" not in href:
                    continue

                print(f"Processing: {text}")

                # Determine target directory
                target_dir = get_target_directory(text)
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir, exist_ok=True)

                # Download
                try:
                    with page.expect_download(timeout=10000) as download_info:
                        # Sometimes clicking opens a new tab or triggers download
                        link.click()

                    download = download_info.value
                    # Use the text as filename if suggested filename is generic,
                    # but usually suggested_filename is better.
                    # However, we want to preserve the mapping context.
                    suggested_name = download.suggested_filename
                    final_name = f"{normalize_filename(text)}_{suggested_name}" if "download" in suggested_name.lower() else suggested_name

                    save_path = os.path.join(target_dir, final_name)
                    download.save_as(save_path)
                    print(f"Saved to {save_path}")

                except Exception as e:
                    print(f"Failed to download {text}: {e}")

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
