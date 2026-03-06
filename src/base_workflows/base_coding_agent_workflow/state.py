
from typing_extensions import TypedDict, Optional, List, Literal, Dict, Any
from typing import Annotated
from .pydantic_models import CodeChange, FilePlan

def append_list(existing, new):
    """Reducer that accumulates list results from parallel subgraphs."""
    return (existing or []) + (new or [])

class BaseAgentState(TypedDict):
    execution_id: int
    work_dir: str
    task: str
    file_structure: str
    existing_files:  Optional[Dict[str, str]]  # path -> content
    plan: Optional[Dict[str, Any]]
    code_changes: Annotated[Optional[Dict[str, Any]], append_list]
    written_files: Annotated[Optional[List[str]], append_list]
    review: Optional[Dict[str, str]]
    static_check_success: Optional[bool]
    static_check_output: Optional[str]
    feedback: Optional[str]
    retry_count: Dict[str, int]

class BaseFileAgentState(TypedDict):
    # Inherited context
    execution_id: int
    work_dir: str
    task: str
    feedback: Optional[str]
    retry_count: Dict[str, int]
    written_files: Annotated[Optional[List[str]], append_list]
    # Per-file fields
    file_plan: FilePlan                     # single FilePlan (not a list)
    existing_file_content: Optional[str]    # content of file being modified
    code_change: Optional[CodeChange]       # single file output
    review: Optional[Dict[str, str]]
    code_changes: Annotated[Optional[Dict[str, Any]], append_list]
    static_check_success: Optional[bool]
    static_check_output: Optional[str]    