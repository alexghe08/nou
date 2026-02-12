from pydantic import BaseModel, Field
from typing import Optional, List

class DocumentMetadata(BaseModel):
    file_id: str = Field(..., description="Unique identifier for the file")
    original_name: str = Field(..., description="Original filename")
    section_code: str = Field(..., description="Legal section (I-VI)")
    document_type: str = Field(..., description="Functional category (e.g., Specificatie Tehnica)")
    article_ref: Optional[str] = Field(None, description="Legal article reference (e.g., Art. 15.2)")
    applicability: Optional[str] = Field(None, description="Procedure type (e.g., Licitatie Deschisa)")
    content_class: Optional[str] = Field(None, description="Content type (e.g., Clauza_Penalizatoare)")

class RagFragment(BaseModel):
    chunk_id: str
    text: str
    metadata: DocumentMetadata
    parent_headings: List[str] = Field(default_factory=list, description="Hierarchy of headings leading to this chunk")
