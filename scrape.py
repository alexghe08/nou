import os
import re
import time
import pandas as pd
from playwright.sync_api import sync_playwright

CATEGORIES = [
    ("Combustibil (achiziții curente)", "https://achizitiipublice.gov.ro/matrix/cell/426/1"),
    ("Combustibil (versiune UCA)", "https://achizitiipublice.gov.ro/matrix/cell/427/1"),
    ("Birotică și papetărie", "https://achizitiipublice.gov.ro/matrix/cell/430/1"),
    ("Produse de curățenie", "https://achizitiipublice.gov.ro/matrix/cell/431/1"),
    ("Servicii auto", "https://achizitiipublice.gov.ro/matrix/cell/433/1"),
    ("Servicii de curățenie interioară", "https://achizitiipublice.gov.ro/matrix/cell/434/1"),
    ("Documentații standardizate în consultare", "https://achizitiipublice.gov.ro/matrix/cell/435/1"),
    ("Măști de protecție", "https://achizitiipublice.gov.ro/matrix/cell/436/1"),
    ("Servicii intelectuale", "https://achizitiipublice.gov.ro/matrix/cell/171/1"),
    ("Servicii colectare, transport și eliminare finală deșeuri medicale", "https://achizitiipublice.gov.ro/matrix/cell/402/1"),
    ("Lucrări de reparații", "https://achizitiipublice.gov.ro/matrix/cell/401/1"),
    ("Servicii de mentenanță echipamente", "https://achizitiipublice.gov.ro/matrix/cell/398/1"),
    ("Hardware", "https://achizitiipublice.gov.ro/matrix/cell/446/1"),
    ("Alimente", "https://achizitiipublice.gov.ro/matrix/cell/448/1"),
    ("Servicii întreținere spații verzi", "https://achizitiipublice.gov.ro/matrix/cell/449/1"),
    ("Furnizare energie electrică", "https://achizitiipublice.gov.ro/matrix/cell/447/1"),
    ("Materiale utile", "https://achizitiipublice.gov.ro/matrix/cell/457/1"),
    ("Execuție lucrări", "https://achizitiipublice.gov.ro/matrix/cell/72/1"),
    ("Furnizare de produse", "https://achizitiipublice.gov.ro/matrix/cell/76/1"),
    ("Servicii de întreținere și reparații auto", "https://achizitiipublice.gov.ro/matrix/cell/167/1"),
    ("Servicii de curățenie", "https://achizitiipublice.gov.ro/matrix/cell/397/1"),
    ("Servicii de proiectare", "https://achizitiipublice.gov.ro/matrix/cell/77/1"),
    ("Servicii de pază", "https://achizitiipublice.gov.ro/matrix/cell/80/1"),
]

def sanitize_filename(name):
    # Remove characters that are unsafe for filenames
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        metadata_list = []
        base_output_dir = "AchizitiiPubliceDocs"
        if not os.path.exists(base_output_dir):
            os.makedirs(base_output_dir)

        for domain, url in CATEGORIES:
            print(f"Processing category: {domain}")
            try:
                page.goto(url)

                # Wait for the document box content to load
                try:
                    # Using the selector we confirmed via grep: #documnets (sic) or simply .box-content
                    page.wait_for_selector(".box-content li a", timeout=10000)
                except Exception:
                    print(f"No documents found for {domain} (timeout waiting for selector).")
                    continue

                # Get all links in the box-content list
                links = page.locator(".box-content li a").all()
                print(f"Found {len(links)} documents.")

                sanitized_domain = sanitize_filename(domain)
                domain_dir = os.path.join(base_output_dir, sanitized_domain)
                if not os.path.exists(domain_dir):
                    os.makedirs(domain_dir)

                # Iterate through links
                # Note: Clicking links might cause navigation if not handled as download.
                # Playwright's expect_download handles attachment downloads.
                # If clicking opens a new tab, expect_download might need to be adjusted or context.expect_page() used.
                # But based on typical implementation (and <a> tag structure without href), it likely triggers a download via JS.

                for i, link in enumerate(links):
                    try:
                        text = link.inner_text().strip()
                        if not text:
                            continue

                        print(f"  Downloading: {text}")

                        # Setup download listener
                        with page.expect_download(timeout=60000) as download_info:
                            link.click()

                        download = download_info.value
                        suggested_filename = download.suggested_filename

                        # Save file
                        file_path = os.path.join(domain_dir, suggested_filename)
                        download.save_as(file_path)

                        # Extract Cell ID from URL
                        cell_id_match = re.search(r'/cell/(\d+)/', url)
                        cell_id = cell_id_match.group(1) if cell_id_match else "N/A"

                        metadata_list.append({
                            "Domain": domain,
                            "URL": url,
                            "File Name": suggested_filename,
                            "Download Path": file_path,
                            "Cell ID": cell_id,
                            "Link Text": text
                        })

                        # Small delay to be polite and avoid race conditions
                        time.sleep(0.5)

                    except Exception as e:
                        print(f"  Failed to download document: {e}")

            except Exception as e:
                print(f"Error processing {domain}: {e}")

        browser.close()

        # Save Metadata to CSV
        if metadata_list:
            df = pd.DataFrame(metadata_list)
            df.to_csv("Metadate_Achizitii.csv", index=False)
            print("Metadata saved to Metadate_Achizitii.csv")
        else:
            print("No metadata collected.")

if __name__ == "__main__":
    run()
