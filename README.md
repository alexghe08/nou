# Standardization and Automated Processing of Award Documentation for Works Execution (Cell 72 ANAP)

This repository implements the strategy for standardizing and processing procurement documents for "Works Execution" (Execuție Lucrări), specifically targeting "Cell 72" of the ANAP matrix.

## Directory Structure

Based on the research report, the repository is organized into the canonical 6 sections:

- `72__Executie_lucrari/`
    - `01_Sectiunea_I_Instructiuni/`: Instructions to Bidders & Data Sheet.
    - `02_Sectiunea_II_CaietSarcini/`: Technical Specifications (Frame).
    - `03_Sectiunea_III_Contracte/`: Contractual Framework (General & Specific Conditions).
    - `04_Sectiunea_IV_AcordCadru_FaraReluare/`: Framework Agreements without reopening competition (Synthesized).
    - `05_Sectiunea_V_AcordCadru_CuReluare/`: Framework Agreements with reopening competition (Synthesized).
    - `06_Sectiunea_VI_Formulare/`: Standard Forms.
    - `07_Factori_Evaluare/`: Evaluation Factors Catalog.
- `CleanedDocs/`: Default download location for uncategorized files.
- `RAG_Fragments.jsonl`: The processed output for RAG ingestion.

## Scripts

### 1. `scrape.py`
Scrapes the ANAP website (`https://achizitiipublice.gov.ro/matrix/cell/72/1`) to download the latest documents.
- Automatically classifies downloaded files into the correct section folders based on keywords.
- Targets the `#documnets` DOM element.

### 2. `synthesize.py`
Generates the missing Framework Agreement documents (Sections IV and V) by adapting the standard Execution Contract (Section III).
- Creates `Acord_Cadru` versions from `I_CONTRACT` templates.
- Adjusts terminology (e.g., "Pret Fix" -> "Preturi Unitare").

### 3. `ingest.py`
Processes the `.docx` files and chunks them for RAG (Retrieval-Augmented Generation).
- Implements **Recursive Structure-Aware Chunking**: Preserves document hierarchy (Section -> Article -> Paragraph).
- Extracts metadata based on file location and content.
- Outputs to `RAG_Fragments.jsonl`.

### 4. `schema.py`
Defines the Pydantic models for metadata and chunks:
- `DocumentMetadata`: Stores file ID, section code, article reference, etc.
- `RagFragment`: The actual text chunk with context.

## Usage

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Scrape Documents** (requires internet access and Playwright browsers):
   ```bash
   python scrape.py
   ```

3. **Synthesize Missing Documents**:
   ```bash
   python synthesize.py
   ```

4. **Ingest and Chunk**:
   ```bash
   python ingest.py
   ```

5. **Verify Output**:
   Check `RAG_Fragments.jsonl` for the generated chunks.

## Notes
- The scraping script handles the known typo in the source HTML (`#documnets`).
- The ingestion process uses heuristics for heading detection if standard styles are not used.
