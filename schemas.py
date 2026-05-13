from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class BranchCreate(BaseModel):
    branch_name: str = Field(..., min_length=2, max_length=100)
    location: str = Field(..., min_length=2, max_length=100)

class BranchUpdate(BaseModel):
    branch_name: Optional[str] = None
    location: Optional[str] = None

class BranchResponse(BaseModel):
    id: int
    branch_name: str
    location: str

    model_config = ConfigDict(from_attributes=True)