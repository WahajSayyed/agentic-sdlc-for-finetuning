import os, shutil, json
import subprocess
from typing_extensions import TypedDict, Optional, List, Literal, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from src.tools.read_file_structure import read_file_structure
from src.tools.read_file import read_file
from src.config.logging_config import logger
from codecarbon import EmissionsTracker

tracker = EmissionsTracker(
    project_name="agentic_sdlc",
    output_dir="/home/wahaj/study/product_WJ/emissions",
    log_level="info"
)

load_dotenv()
working_dir = os.getenv("WORKING_DIR")
MAX_REVIEW_RETRIES = int(os.getenv("MAX_REVIEW_RETRIES", 3))
MAX_STATIC_CHECK_RETRIES = int(os.getenv("MAX_STATIC_CHECK_RETRIES", 3))

llm = ChatOpenAI(
    base_url="http://localhost:8080/v1",
    # model="Qwen2.5-7B-Instruct.Q4_0.gguf",
    model="Qwen2.5-Coder-7B-Instruct.Q4_0.gguf",
    api_key="not_needed",
    # callbacks=[SimpleLogger()]
)

class AgentState(TypedDict):
    execution_id: int
    work_dir: str
    task: str
    file_structure: str
    existing_files:  Optional[Dict[str, str]]  # path -> content
    plan: Optional[Dict[str, Any]]
    code_changes: Optional[Dict[str, Any]]
    review: Optional[Dict[str, str]]
    written_files: Optional[List[str]]
    static_check_success: Optional[bool]
    static_check_output: Optional[str]
    feedback: Optional[str]
    retry_count: Dict[str, int]

def setup_node(state: AgentState):
    logger.info("*"*20)
    logger.info("Executing Setup Node")
    # To do : last execution id will be fetch from the databse and +1 will be used as next
    state["execution_id"] = 3 # hard coded temporarily 
    state["work_dir"] = os.path.join(working_dir, str(state["execution_id"]))
    state["retry_count"] = {"review" : 0, "static_check_count": 0}
    return state

def file_structure_node(state: AgentState):
    logger.info("Reading File Strucutre")
    
    # structure = read_file_structure.invoke(working_dir)
    structure = read_file_structure.invoke(state["work_dir"])
    state["file_structure"] = structure
    logger.debug(f"Updating File Structure: \n{structure}")
    return {"file_structure": state["file_structure"]}

class FilePlan(BaseModel):
    path: str = Field(description="This is an absolute path of file where work_dir is the parent directory.")
    action: Literal["create", "update"]
    reason: str

class Plan(BaseModel):
    summary: str
    files: List[FilePlan]


parser = PydanticOutputParser(pydantic_object=Plan)

planner_prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are a senior software architect.

Your job is to create a precise implementation plan.

Rules:
- Prefer updating existing files over creating new ones.
- Only create new files if necessary.
- Respect the apparent project structure.
- Keep modifications minimal and modular.
- Return structured JSON only.
"""),
    ("user", """
Task:
{task}

Working Directory:
{work_dir}

Repository file structure:
{file_structure}

{format_instructions}
""")
])



def planner_node(state: AgentState):
    logger.info("Executing Planner Node")
    formatted_prompt = planner_prompt.format_messages(
        task=state["task"],
        work_dir=state["work_dir"],
        file_structure=state["file_structure"],
        format_instructions=parser.get_format_instructions()
    )
    logger.debug(f"Python Planner Prompt: \n{formatted_prompt}")
    # response = llm.invoke(formatted_prompt)
    # plan = parser.parse(response.content)
    plan = llm.with_structured_output(Plan).invoke(formatted_prompt)
    state["plan"] = plan.model_dump()
    return {"plan": state["plan"]}


def reader_node(state: AgentState):
    logger.info("Executing Reader Node")
    plan = state["plan"]
    files_to_update = [
        file["path"] for file in plan["files"]  # ignore type-check
        if file["action"] == "update"
    ]
    existing_files = {}

    for path in files_to_update:
        content = read_file.invoke(path)
        existing_files[path] = content

    state["existing_files"] = existing_files
    logger.debug(f"Existing Files: \n{existing_files}")
    return state

def should_read(state: AgentState) -> Literal["reader", "coder"]:
    plan = state["plan"]
    try:
        for file in plan["files"]:
            if file["action"] == "update":
                return "reader"
    except FileNotFoundError:
        return "coder"
    except Exception as e:
        print(f"Error occured: {e}")
        return "coder"
    

class CodeChange(BaseModel):
    path: str = Field(description="This is an absolute path of file  where work_dir is the parent directory.")
    action: Literal["create", "update"]
    content: str # full new content(safe v1 design)  | In v2, you can move to diff/patch mode.

class CodeOutput(BaseModel):
    summary: str
    changes: List[CodeChange]


coder_parser = PydanticOutputParser(pydantic_object=CodeOutput)

coder_prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are a senior software engineer.

Your job:
Generate precise code changes based on the plan.

Rules:
- For "create" → produce complete new file.
- For "update" → modify existing file carefully.
- Preserve unrelated logic.
- Do NOT remove functionality unless required.
- Keep changes minimal and clean.
- Maintain style consistency.
- Return structured JSON only.
"""),
    ("user", """
Task:
{task}

Implementation Plan:
{plan}

Static Analysis Feedback (if any):
{feedback}

Existing Files (only for updates):
{existing_files}

Format Instructions:
{format_instructions}
""")
])

from langgraph.types import RetryPolicy
def coder_node(state: AgentState):
    logger.info("Executing Coder Node")
    formatted_prompt = coder_prompt.format_messages(
        task=state["task"],
        plan=state["plan"],
        feedback=state.get("feedback", ""),
        existing_files=state.get("existing_files", {}),
        format_instructions=coder_parser.get_format_instructions()
    )

    # response = llm.invoke(formatted_prompt)
    llm_structured = llm.with_structured_output(CodeOutput)
    try:
        code_output = llm_structured.invoke(formatted_prompt)
        # code_output = coder_parser.parse(response.content)
    except Exception as e:
        logger.error(f"Error occured during code generation. {e}")
        raise e
    state["code_changes"] = code_output.model_dump()
    logger.debug(f"Generated CODE: \n {code_output.model_dump()}")
    return state


class ReviewResult(BaseModel):
    status: Literal["approved", "needs_revision"]
    issues: List[str]
    suggestion: List[str]
    confidence: float = Field(description="The value must be between 0.0 - 1.0")

reviewer_parser = PydanticOutputParser(pydantic_object=ReviewResult)


reviewer_prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are a senior software reviewer performing static analysis.

Your job:
Evaluate the proposed code changes.

You must:
- Ensure changes align with the task.
- Ensure minimal modifications.
- Ensure no unrelated logic is removed.
- Detect missing imports.
- Detect obvious runtime risks.
- Detect architectural violations.
- Reject incomplete implementations.

Be strict but fair.

Return structured JSON only.
"""),
    ("user", """
Task:
{task}

Implementation Plan:
{plan}

Existing Files (for updates):
{existing_files}

Proposed Code Changes:
{code_changes}

{format_instructions}
""")
])

def reviewr_node(state: AgentState):
    logger.info("Executing Reviewer Node")
    formatted_prompt = reviewer_prompt.format_messages(
        task=state["task"],
        plan=["plan"],
        existing_files=state.get("existing_files", {}),
        code_changes=state["code_changes"],
        format_instructions=reviewer_parser.get_format_instructions()
    )

    response = llm.invoke(formatted_prompt)
    reviewe_result = reviewer_parser.parse(response.content)
    state["review"] = reviewe_result.model_dump()
    
    logger.info(f"Review by Reviewer Node: \n{reviewe_result.model_dump()}")
    return state

def review_descision(state: AgentState):
    if state["review"]["status"].lower() == "approved":
        state["retry_count"]["review"] = 0  # reset
        return "approve"
    state["retry_count"]["review"] += 1
    if state["retry_count"]["review"] >= MAX_REVIEW_RETRIES:
        return "abort"
    return "revise"

def writer_node(state: AgentState, backup: bool = True):
    """
    Persist code changes to disk safely.

    Args:
        state: AgentState containing code_changes
        backup: wheather to backup overwritten files
    """
    logger.info("Executing Writer Node")
    written_files = []

    code_changes = state.get("code_changes", {}).get("changes", [])
    work_dir = state["work_dir"]
    for change in code_changes:
        path = change["path"]
        if not path.startswith(work_dir):
            logger.critical(f"skipping the file due to wrong file path: {path}")
            continue
        content = change["content"]
        action = change["action"]
        # Ensure directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if backup and action == "update" and os.path.exists(path):
            backup_path = path + ".bak"
            shutil.copyfile(path, backup_path)

        # Write new content
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        written_files.append(path)

    state["written_files"] = written_files
    logger.debug(f"Written Files: \n{written_files}")
    return state

def static_check_node(state: AgentState):
    logger.info("Executing Static Check Node")
    written_files = state.get("written_files", [])

    if not written_files:
        state["static_check_success"] = True
        state["static_check_output"] = "No Files written."
        return state

    result = subprocess.run(
        ["ruff", "check", "--output-format", "json"] + written_files,
        capture_output=True,
        text=True
    )

    state["static_check_success"] = result.returncode == 0
    state["static_check_output"] = result.stdout + result.stderr
    
    if result.returncode != 0:
        def summarize_ruff_issue(json_output):
            try:
                issues = json.loads(json_output)
                issue_list = [
                    f"{i['filename']}:{i['location']['row']} {i['code']} {i['message']}"
                    for i in issues
                ]
                return "Ruff reported:\n" + "\n".join(issue_list)
            except Exception as e:
                return "Ruff reported issues but JSON parsing failed:\n" + json_output
        state["feedback"] = summarize_ruff_issue(result.stdout)
    else:
        state["feedback"] = None
    logger.info(f"Static Check FEEDBACK: \n{state["feedback"]}")
    return state

def static_check_decision(state: AgentState):
    if state["static_check_success"]:
        state["retry_count"]["static_check_count"] = 0  # reset
        return "pass" 
    state["retry_count"]["static_check_count"] += 1

    if state["retry_count"]["static_check_count"] >= MAX_STATIC_CHECK_RETRIES:
        return "abort"
    return "retry"


workflow = StateGraph(AgentState)
workflow.add_node("setup", setup_node)
workflow.add_node("file_structure", file_structure_node)
workflow.add_node("planner", planner_node, retry_policy=RetryPolicy(max_attempts=3))
workflow.add_node("reader", reader_node)
workflow.add_node("coder", coder_node, retry_policy=RetryPolicy(max_attempts=3))
workflow.add_node("reviewer", reviewr_node)
workflow.add_node("writer", writer_node)
workflow.add_node("static_check", static_check_node, retry_policy=RetryPolicy(max_attempts=3))

workflow.set_entry_point("setup")

workflow.add_edge("setup", "file_structure")
workflow.add_edge("file_structure", "planner")
workflow.add_conditional_edges("planner", should_read)
# workflow.add_edge("reader", END) #TESTINGGGGG
workflow.add_edge("reader", "coder")
workflow.add_edge("coder", "reviewer")
workflow.add_conditional_edges(
    "reviewer", review_descision,
    {
        "approve": "writer",
        "abort": "writer",
        "revise" : "coder"
    }
)
workflow.add_edge("writer", "static_check")
workflow.add_conditional_edges(
    "static_check", 
    static_check_decision,
    {
        "pass": END,
        "abort": END,
        "retry": "coder"
    })

graph = workflow.compile()
# Get binary PNG data
png_data = graph.get_graph().draw_mermaid_png()

# Save to file
output_file = "python_agent_workflow_graph.png"
with open(output_file, "wb") as f:
    f.write(png_data)

print(f"Graph saved to {output_file}")

config = {"recursion_limit": 50}
input_state = {"task": "Write a detailed FastAPI endpoint for CRUD ops for a llm application that can take user input in text of file format"}
tracker.start()
result = graph.invoke(input_state, config=config)
logger.info("EXECUTION COMPLETED!")
print(result)
tracker.stop()