import os
import json
import re
from docx import Document
from schema import DocumentMetadata, RagFragment

# Configuration
INPUT_DIR = "72__Executie_lucrari"
OUTPUT_FILE = "RAG_Fragments.jsonl"
MAX_CHUNK_SIZE = 1500  # Characters

class DocxIngestor:
    def __init__(self, input_dir, output_file):
        self.input_dir = input_dir
        self.output_file = output_file
        self.fragments = []

    def run(self):
        print(f"Scanning directory: {self.input_dir}")
        for root, dirs, files in os.walk(self.input_dir):
            for file in files:
                if file.endswith(".docx") and not file.startswith("~$"):
                    filepath = os.path.join(root, file)
                    print(f"Processing: {filepath}")
                    try:
                        self.process_file(filepath, file, root)
                    except Exception as e:
                        print(f"Error processing {filepath}: {e}")

        self.save_fragments()

    def process_file(self, filepath, filename, root):
        doc = Document(filepath)
        metadata = self.extract_metadata(filename, root)

        current_headings = []
        current_chunk_text = []

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            # Heuristic for headings
            if self.is_heading(para):
                # Save previous chunk if it has content
                if current_chunk_text:
                    self.add_fragment(current_chunk_text, metadata, current_headings)
                    current_chunk_text = []

                # Update headings stack
                level = self.get_heading_level(para)
                if level <= len(current_headings):
                    current_headings = current_headings[:level-1]
                current_headings.append(text)
            else:
                current_chunk_text.append(text)

                # Check size limit
                if sum(len(t) for t in current_chunk_text) > MAX_CHUNK_SIZE:
                    self.add_fragment(current_chunk_text, metadata, current_headings)
                    current_chunk_text = []

        # Add final chunk
        if current_chunk_text:
            self.add_fragment(current_chunk_text, metadata, current_headings)

    def is_heading(self, para):
        if para.style.name.startswith('Heading'):
            return True
        # Fallback regex for common legal headings
        text = para.text.strip()
        if re.match(r'^(Section|Secțiunea|Capitolul|Articolul|Art\.|Rule)\s+[IVX0-9]+', text, re.IGNORECASE):
            return True
        return False

    def get_heading_level(self, para):
        if para.style.name.startswith('Heading'):
            try:
                return int(para.style.name.replace('Heading', '').strip())
            except ValueError:
                return 1
        return 1 # Default level for regex matches

    def extract_metadata(self, filename, root):
        # Extract section from directory name
        section_code = "Unknown"
        # Check from longest to shortest Roman numeral substring to avoid prefix matching
        # I matches II and III. II matches III.
        if "Sectiunea_III" in root: section_code = "III"
        elif "Sectiunea_II" in root: section_code = "II"
        elif "Sectiunea_IV" in root: section_code = "IV"
        elif "Sectiunea_VI" in root: section_code = "VI"
        elif "Sectiunea_V" in root: section_code = "V"
        elif "Sectiunea_I" in root: section_code = "I"

        doc_type = "Document"
        if "Instructiuni" in filename: doc_type = "Instructiuni"
        elif "Caiet" in filename: doc_type = "Caiet Sarcini"
        elif "Contract" in filename: doc_type = "Contract"
        elif "Formular" in filename: doc_type = "Formular"

        return DocumentMetadata(
            file_id=filename,
            original_name=filename,
            section_code=section_code,
            document_type=doc_type,
            applicability="General", # Default
            content_class="Clause" # Default
        )

    def add_fragment(self, text_list, metadata, headings):
        text = "\n".join(text_list)
        fragment = RagFragment(
            chunk_id=f"{metadata.file_id}_{len(self.fragments)}",
            text=text,
            metadata=metadata,
            parent_headings=list(headings)
        )
        self.fragments.append(fragment)

    def save_fragments(self):
        with open(self.output_file, 'w', encoding='utf-8') as f:
            for frag in self.fragments:
                f.write(frag.model_dump_json() + "\n")
        print(f"Saved {len(self.fragments)} fragments to {self.output_file}")

if __name__ == "__main__":
    ingestor = DocxIngestor(INPUT_DIR, OUTPUT_FILE)
    ingestor.run()
