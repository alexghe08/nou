from typing import List, Optional
from pydantic import BaseModel, Field

class DocumentMetadata(BaseModel):
    title: str = Field(..., description="Title of the document")
    url: str = Field(..., description="Download URL")
    local_path: str = Field(..., description="Local file path")
    domain: str = Field(..., description="Procurement domain")
    section: str = Field(..., description="Section (A, B, C, D) or Other")
    file_type: str = Field(..., description="docx, xlsx, etc.")

class ProcurementSection(BaseModel):
    section_name: str
    documents: List[DocumentMetadata] = []
    text_content: Optional[str] = Field(None, description="Aggregated text content for this section")

class DosarAchizitie(BaseModel):
    domain: str = Field(..., description="e.g. 'Servicii de curatenie'")

    # Structured Data Fields (to be extracted or generated)
    autoritate_contractanta: Optional[str] = None
    obiectul_achizitiei: Optional[str] = None
    cod_cpv: Optional[str] = None
    valoare_estimata: Optional[float] = None
    moneda: str = "RON"

    # Sections of the dossier
    sectiunea_a: ProcurementSection = Field(default_factory=lambda: ProcurementSection(section_name="A - Instructiuni & DUAE"))
    sectiunea_b: ProcurementSection = Field(default_factory=lambda: ProcurementSection(section_name="B - Caiet de Sarcini"))
    sectiunea_c: ProcurementSection = Field(default_factory=lambda: ProcurementSection(section_name="C - Contract"))
    sectiunea_d: ProcurementSection = Field(default_factory=lambda: ProcurementSection(section_name="D - Formulare"))

    class Config:
        arbitrary_types_allowed = True
