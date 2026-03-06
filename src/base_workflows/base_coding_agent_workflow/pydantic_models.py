from typing_extensions import List, Literal
from pydantic import BaseModel, Field


class FilePlan(BaseModel):
    path: str = Field(description="This is an absolute path of file where work_dir is the parent directory.")
    action: Literal["create", "update"]
    reason: str

class Plan(BaseModel):
    summary: str
    files: List[FilePlan]

class CodeChange(BaseModel):
    path: str = Field(description="This is an absolute path of file  where work_dir is the parent directory.")
    action: Literal["create", "update"]
    content: str # full new content(safe v1 design)  | In v2, you can move to diff/patch mode.

class CodeOutput(BaseModel):
    summary: str
    changes: List[CodeChange]

class SingleFileOutput(BaseModel):
    summary:str
    change: CodeChange

class ReviewResult(BaseModel):
    status: Literal["approved", "needs_revision"]
    issues: List[str]
    suggestion: List[str]
    confidence: float = Field(description="The value must be between 0.0 - 1.0")
