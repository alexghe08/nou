import os
import json
import pandas as pd
from docx import Document
from schema import DosarAchizitie, DocumentMetadata, ProcurementSection

METADATA_FILE = "Metadate_Achizitii.csv"
OUTPUT_FILE = "RAG_Fragments.jsonl"

def get_section_from_filename(filename: str) -> str:
    lower_name = filename.lower()
    if "sectiunea a" in lower_name or "instructiuni" in lower_name or "fisa de date" in lower_name:
        return "A"
    elif "sectiunea b" in lower_name or "caiet de sarcini" in lower_name or "specificatii" in lower_name:
        return "B"
    elif "sectiunea c" in lower_name or "contract" in lower_name or "acord" in lower_name:
        return "C"
    elif "sectiunea d" in lower_name or "formular" in lower_name or "propunere" in lower_name:
        return "D"
    return "Other"

def extract_text_from_docx(path: str) -> str:
    try:
        doc = Document(path)
        text = []
        for p in doc.paragraphs:
            t = p.text.strip()
            if t:
                text.append(t)
        # Also extract basic table text
        for table in doc.tables:
            for row in table.rows:
                row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_text:
                    text.append(" | ".join(row_text))
        return "\n".join(text)
    except Exception as e:
        print(f"Error reading docx {path}: {e}")
        return ""

def run():
    if not os.path.exists(METADATA_FILE):
        print("Metadata file not found. Run scrape.py first.")
        return

    df = pd.read_csv(METADATA_FILE)

    # Group by Domain to create one Dosar per domain
    grouped = df.groupby("Domain")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f_out:
        for domain, group in grouped:
            print(f"Processing Domain: {domain}")

            dosar = DosarAchizitie(domain=domain)

            for _, row in group.iterrows():
                filepath = row["Download Path"]
                if not os.path.exists(filepath):
                    continue

                section_code = get_section_from_filename(os.path.basename(filepath))

                meta = DocumentMetadata(
                    title=row["File Name"],
                    url=row["URL"],
                    local_path=filepath,
                    domain=domain,
                    section=section_code,
                    file_type=os.path.splitext(filepath)[1]
                )

                # Extract text if docx
                content = ""
                if meta.file_type.lower() == ".docx":
                    content = extract_text_from_docx(filepath)

                # Assign to section
                if section_code == "A":
                    dosar.sectiunea_a.documents.append(meta)
                    if content:
                        if dosar.sectiunea_a.text_content:
                            dosar.sectiunea_a.text_content += "\n\n" + content
                        else:
                            dosar.sectiunea_a.text_content = content
                elif section_code == "B":
                    dosar.sectiunea_b.documents.append(meta)
                    if content:
                        if dosar.sectiunea_b.text_content:
                            dosar.sectiunea_b.text_content += "\n\n" + content
                        else:
                            dosar.sectiunea_b.text_content = content
                elif section_code == "C":
                    dosar.sectiunea_c.documents.append(meta)
                    if content:
                        if dosar.sectiunea_c.text_content:
                            dosar.sectiunea_c.text_content += "\n\n" + content
                        else:
                            dosar.sectiunea_c.text_content = content
                elif section_code == "D":
                    dosar.sectiunea_d.documents.append(meta)
                    if content:
                        if dosar.sectiunea_d.text_content:
                            dosar.sectiunea_d.text_content += "\n\n" + content
                        else:
                            dosar.sectiunea_d.text_content = content

            # Serialize the Dossier to JSONL
            # We exclude the full text content from the main JSONL line if it's too huge,
            # but for RAG purposes we usually want chunks.
            # Here, we save the structured object.
            # Note: For real RAG, we would chunk `text_content` and save to vector DB.
            # This JSONL serves as the "Knowledge Base Source".

            f_out.write(dosar.model_dump_json() + "\n")

    print(f"Ingestion complete. Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    run()
