import os
import shutil
from docx import Document

# Source and Destination paths
SRC_DIR = "72__Executie_lucrari/03_Sectiunea_III_Contracte"
DEST_DIR_IV = "72__Executie_lucrari/04_Sectiunea_IV_AcordCadru_FaraReluare"
DEST_DIR_V = "72__Executie_lucrari/05_Sectiunea_V_AcordCadru_CuReluare"

TEMPLATE_NAME_DEFAULT = "I_CONTRACT_Lucrari.docx"

def find_contract_template(src_dir):
    # Find any .docx file containing 'Contract' or 'I_CONTRACT'
    if not os.path.exists(src_dir):
        return None
    for file in os.listdir(src_dir):
        if file.endswith(".docx") and "Contract" in file:
            return os.path.join(src_dir, file)
    return None

def create_dummy_template_if_missing(filepath):
    if not os.path.exists(filepath):
        print(f"Creating dummy template at {filepath}")
        doc = Document()
        doc.add_heading("CONTRACT DE EXECUTIE LUCRARI", 0)
        p = doc.add_paragraph()
        run = p.add_run("Art. 1. Obiectul Contractului...")
        run.bold = True
        doc.add_paragraph("Art. 2. Pretul Contractului...")
        doc.save(filepath)
        return filepath
    return filepath

def synthesize_agreement(src_path, dest_dir, type_label):
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    filename = os.path.basename(src_path)
    new_filename = filename.replace("CONTRACT", "ACORD_CADRU").replace("Contract", "Acord_Cadru")
    if new_filename == filename:
         new_filename = "Synthesized_Acord_Cadru_" + filename

    dest_path = os.path.join(dest_dir, new_filename)

    print(f"Synthesizing {dest_path} from {src_path}...")

    try:
        doc = Document(src_path)
        # Search and replace in runs to preserve formatting (bold/italic)
        for para in doc.paragraphs:
            for run in para.runs:
                if "Contract" in run.text:
                    run.text = run.text.replace("Contract", "Acord Cadru")
                if "CONTRACT" in run.text:
                    run.text = run.text.replace("CONTRACT", "ACORD CADRU")
                if "Pret Fix" in run.text and type_label == "CuReluare":
                    run.text = run.text.replace("Pret Fix", "Preturi Unitare")

        doc.save(dest_path)
        print(f"Successfully created {dest_path}")
    except Exception as e:
        print(f"Failed to synthesize: {e}")

def run():
    # Try to find existing template
    template_path = find_contract_template(SRC_DIR)

    if not template_path:
        print("No template found. Creating dummy.")
        template_path = os.path.join(SRC_DIR, TEMPLATE_NAME_DEFAULT)
        create_dummy_template_if_missing(template_path)

    # Synthesize Section IV
    synthesize_agreement(template_path, DEST_DIR_IV, "FaraReluare")

    # Synthesize Section V
    synthesize_agreement(template_path, DEST_DIR_V, "CuReluare")

if __name__ == "__main__":
    run()
