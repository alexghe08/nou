from typing import List, Optional
from pydantic import BaseModel, Field

class DocumentMetadata(BaseModel):
    file_id: str = Field(..., description="Unique file identifier (e.g. file_72_01)")
    original_name: str = Field(..., description="Original filename")
    url: str = Field(..., description="Download URL")
    local_path: str = Field(..., description="Local file path")
    domain: str = Field(..., description="Procurement domain")
    section_code: str = Field(..., description="Legal Section (I-VI)")
    document_type: str = Field(..., description="Functional category (e.g. Fisa de Date, Contract, Formular)")
    file_type: str = Field(..., description="docx, xlsx, etc.")
    content_class: Optional[str] = Field(None, description="Classification of content (e.g. Clauza_Penalizatoare)")

class TextChunk(BaseModel):
    chunk_id: str
    text: str
    context_path: List[str] = Field(default_factory=list, description="Hierarchy path [Heading 1, Heading 2...]")
    metadata: DocumentMetadata

class ProcurementSection(BaseModel):
    section_code: str # I, II, III, IV, V, VI
    section_name: str
    documents: List[DocumentMetadata] = []
    chunks: List[TextChunk] = [] # chunks are stored here instead of raw text

class DosarAchizitie(BaseModel):
    domain: str = Field(..., description="e.g. 'Execuție lucrări'")

    # Structured Data Fields
    autoritate_contractanta: Optional[str] = None
    obiectul_achizitiei: Optional[str] = None
    cod_cpv: Optional[str] = None
    valoare_estimata: Optional[float] = None
    moneda: str = "RON"

    # Sections I-VI
    sectiunea_i: ProcurementSection = Field(default_factory=lambda: ProcurementSection(section_code="I", section_name="Instructiuni si Fisa de Date"))
    sectiunea_ii: ProcurementSection = Field(default_factory=lambda: ProcurementSection(section_code="II", section_name="Caiet de Sarcini"))
    sectiunea_iii: ProcurementSection = Field(default_factory=lambda: ProcurementSection(section_code="III", section_name="Clauze Contractuale"))
    sectiunea_iv: ProcurementSection = Field(default_factory=lambda: ProcurementSection(section_code="IV", section_name="Acord Cadru fara reluarea competitiei"))
    sectiunea_v: ProcurementSection = Field(default_factory=lambda: ProcurementSection(section_code="V", section_name="Acord Cadru cu reluarea competitiei"))
    sectiunea_vi: ProcurementSection = Field(default_factory=lambda: ProcurementSection(section_code="VI", section_name="Formulare si Modele"))

    class Config:
        arbitrary_types_allowed = True
