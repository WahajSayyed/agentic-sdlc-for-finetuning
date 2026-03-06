# BaseCodingAgent — Architecture & Workflow

## Overview

`BaseCodingAgent` is an abstract base class that defines a **language-agnostic coding agent workflow** using LangGraph. Concrete agents (e.g. `PythonCodingAgent`, `JavaScriptCodingAgent`) inherit from it and only override language-specific nodes — all graph wiring, state management, and generic nodes are inherited as-is.

---

## Folder Structure

```
src/
├── base_workflows/
│   ├── base_coding_agent_workflow/                          # Abstract base — never instantiated directly
│   │   ├── __init__.py
│   │   ├── agent.py                   # BaseCodingAgent class
│   │   ├── state.py                   # BaseAgentState, BaseFileAgentState
│   │   ├── models.py                  # Plan, FilePlan, CodeChange, Review (Pydantic)
│   │   └── nodes/                     # Generic node implementations
│   │       ├── __init__.py
│   │       ├── setup.py               # setup_node
│   │       ├── file_structure.py      # file_structure_node
│   │       ├── process_files.py       # make_process_files_node (factory)
│   │       ├── reader.py              # reader_node
│   │       └── writer.py              # writer_node
|
├── agents/
│   ├── python_agent/                  # Concrete Python implementation
│   │   ├── __init__.py
│   │   ├── agent.py                   # PythonCodingAgent(BaseCodingAgent)
│   │   ├── prompt/
│   │   │   ├── planner_prompt.py
│   │   │   ├── coder_prompt.py
│   │   │   └── reviewer_prompt.py
│   │   └── nodes/
│   │       ├── planner.py
│   │       ├── coder.py
│   │       ├── reviewer.py
│   │       └── static_check.py        # ruff-specific
│   │
│   └── javascript_agent/              # Concrete JavaScript implementation
│       ├── agent.py                   # JavaScriptCodingAgent(BaseCodingAgent)
│       ├── prompt/
│       └── nodes/
│           └── static_check.py        # eslint-specific
│
├── config/
│   ├── language_config.py             # LanguageConfig dataclass
│   └── llm_config.py                  # LLM initialization
│
└── utils/
    └── logger.py
```

---

## State Design

Two TypedDicts are used — one for the main graph and one for the per-file subgraph.

### `BaseAgentState` — Main Graph
```python
class BaseAgentState(TypedDict):
    execution_id: int
    work_dir: str
    task: str
    file_structure: str
    existing_files: Optional[Dict[str, str]]     # path → content
    plan: Optional[Dict[str, Any]]               # planner output
    code_changes: Annotated[List[Dict], append_list]   # reducer: accumulates per file
    written_files: Annotated[List[str], append_list]   # reducer: accumulates per file
    static_check_success: Optional[bool]
    static_check_output: Optional[str]
    feedback: Optional[str]
    retry_count: Dict[str, int]
```

### `BaseFileAgentState` — File Subgraph
```python
class BaseFileAgentState(TypedDict):
    execution_id: int
    work_dir: str
    task: str
    feedback: Optional[str]
    retry_count: Dict[str, int]
    file_plan: Dict[str, Any]                    # single FilePlan
    existing_file_content: Optional[str]         # content of file being modified
    code_change: Optional[Dict[str, Any]]        # single file output (singular)
    review: Optional[Dict[str, str]]
    written_files: Optional[List[str]]
    static_check_success: Optional[bool]
    static_check_output: Optional[str]
```

> **Key distinction:** `BaseAgentState` uses `code_changes` (plural, with reducer) to accumulate results across parallel/sequential file processing. `BaseFileAgentState` uses `code_change` (singular, no reducer) for one file at a time.

---

## Main Graph

```
__start__
    │
    ▼
  setup                    # initialize execution context
    │
    ▼
file_structure             # scan repo/directory structure
    │
    ▼
 planner ──────────────────────────────────────┐
    │                                           │
    │ (should_read)                             │
    ▼                                           ▼
 reader                               process_files (skip reader)
    │                                           │
    └───────────────────────────────────────────┘
                                        │
                                        ▼
                                   [file subgraph × N files]
                                        │
                                        ▼
                                     __end__
```

### Node Responsibilities

| Node | Type | Description |
|---|---|---|
| `setup` | Generic | Initialize `execution_id`, `work_dir`, logging |
| `file_structure` | Generic | Scan directory, populate `file_structure` in state |
| `planner` | **Abstract** | Generate `Plan` with list of `FilePlan` objects |
| `reader` | **Abstract** | Read existing files into `existing_files` dict |
| `process_files` | Generic (factory) | Loop over plan files, invoke subgraph per file |

### `should_read` Routing

```python
def should_read(state: BaseAgentState) -> Literal["reader", "process_files"]:
    for file in state["plan"]["files"]:
        if file["action"] == "update":
            return "reader"   # need to read existing files first
    return "process_files"    # all creates — skip reader
```

---

## File Subgraph

Each file in the plan is processed independently through this subgraph:

```
  coder ◄─────────────────────────────────────┐
    │                                          │ (revise)
    ▼                                          │
reviewer ──────────────────────────────────────┘
    │
    │ (approve / abort)
    ▼
 writer
    │
    ▼
static_check
    │
    ├── pass  → END
    ├── abort → END
    └── retry → coder
```

### Node Responsibilities

| Node | Type | Description |
|---|---|---|
| `coder` | **Abstract** | Generate code for single `file_plan` |
| `reviewer` | **Abstract** | Review generated `code_change`, return status |
| `writer` | Generic | Write `code_change` content to disk with optional backup |
| `static_check` | **Abstract** | Run linter (ruff/eslint/golangci), populate `feedback` |

### Decision Functions

**`review_decision`**
```
approved  → "approve" → writer
revise + under retry limit → "revise" → coder
revise + over retry limit  → "abort"  → writer
```

**`static_check_decision`**
```
success               → "pass"  → END
failure + under limit → "retry" → coder  (with feedback in state)
failure + over limit  → "abort" → END
```

### Retry Loop Protection

Both loops are bounded by `retry_count` in state:

```python
retry_count: {
    "review": 0,              # incremented in reviewer_node
    "static_check_count": 0   # incremented in static_check_node
}
```

Counters are reset to `{}` at the start of each file in `process_files_node`.

---

## `BaseCodingAgent` Class

```python
class BaseCodingAgent(ABC):

    # Must override — language-specific
    @abstractmethod
    def planner_node(self, state): ...

    @abstractmethod
    def coder_node(self, state): ...

    @abstractmethod
    def reviewer_node(self, state): ...

    @abstractmethod
    def static_check_node(self, state): ...

    # Can override — generic defaults provided
    def setup_node(self, state): ...
    def reader_node(self, state): ...
    def writer_node(self, state): ...
    def process_files_node(self, state): ...
    def should_read(self, state): ...
    def review_decision(self, state): ...
    def static_check_decision(self, state): ...

    # Graph builders — wiring uses self.* so concrete methods resolve at runtime
    def build_file_subgraph(self): ...
    def build_main_graph(self): ...

    # Entry point
    def run(self, task, work_dir, execution_id): ...
```

> **Why graph builders are methods, not standalone functions:** `build_main_graph()` and `build_file_subgraph()` use `self.planner_node`, `self.coder_node` etc. This means the wiring is done at instantiation time, and Python resolves them to the concrete subclass implementation — no imports of abstract nodes needed.

---

## `process_files_node` — Factory Pattern

Since `process_files_node` needs to invoke `file_subgraph`, but the subgraph is only available after the concrete agent is instantiated, a factory function is used:

```python
# base/nodes/process_files.py
def make_process_files_node(file_subgraph):
    def process_files_node(state: BaseAgentState):
        all_code_changes = []
        all_written_files = []

        for file_plan in state["plan"]["files"]:
            file_state = FileAgentState(
                file_plan=file_plan,
                retry_count={},   # reset per file
                ...
            )
            result = file_subgraph.invoke(file_state)
            all_code_changes.append(result["code_change"])
            all_written_files.extend(list(set(result.get("written_files", []))))

        return {**state, "code_changes": all_code_changes, "written_files": all_written_files}

    return process_files_node

# Used in BaseCodingAgent:
def build_main_graph(self):
    file_subgraph = self.build_file_subgraph()           # build first
    process_files = make_process_files_node(file_subgraph)  # inject
    workflow.add_node("process_files", process_files)
```

---

## Creating a Concrete Agent

To add a new language, only 5 things are needed:

**1. Create the agent class:**
```python
# src/agents/go_agent/agent.py
class GoCodingAgent(BaseCodingAgent):
    def planner_node(self, state): return planner_node(state)
    def coder_node(self, state): return coder_node(state)
    def reviewer_node(self, state): return reviewer_node(state)
    def reader_node(self, state): return reader_node(state)
    def static_check_node(self, state): return static_check_node(state)  # golangci-lint
```

**2. Write language-specific prompts** in `go_agent/prompt/`

**3. Implement the 5 abstract nodes** in `go_agent/nodes/`

**4. Register in `main.py`:**
```python
AGENTS = {
    "python": PythonCodingAgent,
    "javascript": JavaScriptCodingAgent,
    "go": GoCodingAgent,          # just add this line
}
```

**5. Run:**
```python
run(task="Write a REST API", work_dir="output/1", language="go")
```

---

## State Flow Summary

```
AgentState
    plan.files = [FilePlan(fibonacci.py), FilePlan(calculator.py)]
         │
         ▼
process_files_node loops:
    ┌─ File 1: fibonacci.py ──► FileAgentState ──► subgraph ──► code_change #1 ─┐
    └─ File 2: calculator.py ─► FileAgentState ──► subgraph ──► code_change #2 ─┘
         │
         ▼
AgentState
    code_changes = [code_change #1, code_change #2]
    written_files = ["fibonacci.py", "calculator.py"]
```

---

## Key Design Rules

| Rule | Reason |
|---|---|
| Nodes return `{**state, "key": value}` deltas, never mutate state directly | LangGraph merges deltas; mutation causes bugs in retry loops |
| Decision functions are pure read-only routers | Only nodes should update state |
| Counter increment happens in the node, not the decision function | Keeps decision functions stateless and testable |
| `retry_count` reset to `{}` per file in `process_files_node` | Prevents retry counts from one file affecting the next |
| `written_files` reset in `coder_node` on each retry | Prevents duplicate entries from retry loops |
| Graph builders are methods on `BaseCodingAgent`, not standalone functions | Allows `self.*` resolution to concrete node implementations at runtime |
