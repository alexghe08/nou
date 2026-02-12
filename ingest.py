import os
import re
import uuid
import pandas as pd
from docx import Document
from schema import DosarAchizitie, DocumentMetadata, ProcurementSection, TextChunk

METADATA_FILE = "Metadate_Achizitii.csv"
OUTPUT_FILE = "RAG_Fragments.jsonl"

def classify_document(filename: str) -> tuple[str, str]:
    """
    Returns (section_code, document_type) based on filename patterns for 'Execuție lucrări'.
    Mapping rules based on user report:
    - Section I: Instructiuni, Fisa de date
    - Section II: Caiet de sarcini, Frame, Specificatii
    - Section III: Contract, CG, CS, Acord
    - Section VI: Formulare, Propunere, Declaratii
    - Section IV/V: Typically missing or Acord Cadru specific variants
    """
    name = filename.lower()

    if "fisa de date" in name:
        return "I", "Fisa de Date"
    if "instructiuni" in name:
        return "I", "Instructiuni"

    if "caiet de sarcini" in name or "specificatii" in name:
        return "II", "Caiet de Sarcini"

    if "contract" in name:
        if "cg" in name:
            return "III", "Conditii Generale"
        if "cs" in name:
            return "III", "Conditii Specifice"
        return "III", "Contract"

    if "formular" in name or "propunere" in name or "declarati" in name or "criteriu" in name:
        return "VI", "Formulare"

    if "acord" in name and "cadru" in name:
        # Heuristic: assign to III by default if not specified as 'reluare'
        return "III", "Acord Cadru"

    return "VI", "Altele" # Default to Forms/Others

def extract_chunks_with_context(path: str, metadata: DocumentMetadata) -> list[TextChunk]:
    chunks = []
    try:
        doc = Document(path)

        # Hierarchy stack: [(level, text)]
        # Level: Heading 1 = 1, Heading 2 = 2, etc. Normal text = 99
        heading_stack = []

        current_chunk_text = []

        def flush_chunk():
            if current_chunk_text:
                text_content = "\n".join(current_chunk_text).strip()
                if text_content:
                    # Construct context path from stack
                    context_path = [h[1] for h in heading_stack]

                    chunks.append(TextChunk(
                        chunk_id=str(uuid.uuid4()),
                        text=text_content,
                        context_path=context_path,
                        metadata=metadata
                    ))
                current_chunk_text.clear()

        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue

            style_name = p.style.name

            # Determine Heading Level
            level = 99
            if style_name.startswith("Heading"):
                try:
                    level = int(style_name.replace("Heading", "").strip())
                except:
                    pass
            elif "Titlu" in style_name or "Title" in style_name:
                level = 1

            if level < 10: # It's a heading
                flush_chunk() # Save previous content

                # Pop headers of same or lower importance (higher level number)
                while heading_stack and heading_stack[-1][0] >= level:
                    heading_stack.pop()

                heading_stack.append((level, text))
                # Treat heading itself as content or just context?
                # Usually beneficial to have it in context, but maybe start a new chunk with it?
                # We'll treat it as context for subsequent text.
            else:
                current_chunk_text.append(text)

        flush_chunk() # Final flush

        # Handle Tables
        for i, table in enumerate(doc.tables):
            table_text = []
            for row in table.rows:
                row_cells = [c.text.strip().replace("\n", " ") for c in row.cells if c.text.strip()]
                if row_cells:
                    table_text.append(" | ".join(row_cells))

            if table_text:
                chunks.append(TextChunk(
                    chunk_id=str(uuid.uuid4()),
                    text=f"[Table {i+1}]\n" + "\n".join(table_text),
                    context_path=["Table"], # Tables often break flow, hard to map to exact heading without position tracking
                    metadata=metadata
                ))

    except Exception as e:
        print(f"Error chunking {path}: {e}")

    return chunks

def run():
    if not os.path.exists(METADATA_FILE):
        print("Metadata file not found. Run scrape.py first.")
        return

    df = pd.read_csv(METADATA_FILE)

    # Group by Domain to process each independently
    grouped = df.groupby("Domain")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f_out:
        for domain, group in grouped:
            print(f"Processing Domain: {domain} ({len(group)} docs)")

            dosar = DosarAchizitie(domain=domain)

            for _, row in group.iterrows():
                filepath = row["Download Path"]
                if not os.path.exists(filepath):
                    continue

                filename = row["File Name"]
                sec_code, doc_type = classify_document(filename)

                file_id = f"file_{uuid.uuid4().hex[:8]}"

                meta = DocumentMetadata(
                    file_id=file_id,
                    original_name=filename,
                    url=row["URL"],
                    local_path=filepath,
                    domain=domain,
                    section_code=sec_code,
                    document_type=doc_type,
                    file_type=os.path.splitext(filename)[1]
                )

                # Extract chunks if docx
                chunks = []
                if meta.file_type.lower() == ".docx":
                    chunks = extract_chunks_with_context(filepath, meta)

                # Assign to Section
                target_section = None
                if sec_code == "I": target_section = dosar.sectiunea_i
                elif sec_code == "II": target_section = dosar.sectiunea_ii
                elif sec_code == "III": target_section = dosar.sectiunea_iii
                elif sec_code == "IV": target_section = dosar.sectiunea_iv
                elif sec_code == "V": target_section = dosar.sectiunea_v
                elif sec_code == "VI": target_section = dosar.sectiunea_vi

                if target_section:
                    target_section.documents.append(meta)
                    target_section.chunks.extend(chunks)

            # Write the full structured object for this domain
            f_out.write(dosar.model_dump_json() + "\n")
        # (Optional: commented out to keep file clean, or write to separate file)
        # for section in [dosar.sectiunea_i, dosar.sectiunea_ii, dosar.sectiunea_iii, dosar.sectiunea_vi]:
        #     for chunk in section.chunks:
        #         f_out.write(chunk.model_dump_json() + "\n")

    print(f"Ingestion complete. Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    run()
