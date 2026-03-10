# Enterprise Coding Agent — LangGraph Implementation

## Overview

A multi-agent coding system built with LangGraph that uses separate specialized agents for planning, executing, and reviewing code changes. The agent is git-aware, LSP-enhanced, and sandboxed to a working directory.

---

## Architecture

```
User Request
     │
     ▼
┌─────────────────┐
│   git_context   │  Injects branch, changed files, diff summary into state
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     planner     │  Explores codebase, builds structured plan
│                 │◄─────────────────────────────┐
└────────┬────────┘                              │
         │                                       │
         ▼ (tool calls)                          │
┌─────────────────┐                              │
│  planner_tools  │  list_directory, search_code,│
│                 │  LSP tools, git tools         │
└────────┬────────┘                              │
         │ (done)                                │
         ▼                                       │
┌─────────────────┐                              │
│  extract_plan   │  Parses JSON plan from LLM   │
└────────┬────────┘  into structured state       │
         │                                       │
         ▼                                       │
┌─────────────────┐                              │
│    executor     │  Reads files, applies edits  │
│                 │◄──────────────┐              │
└────────┬────────┘               │              │
         │                        │              │
         ▼ (tool calls)           │              │
┌─────────────────┐               │              │
│ executor_tools  │  read_file,   │              │
│                 │  apply_diff,  │              │
│                 │  write_file   │              │
└────────┬────────┘               │              │
         │ (done)                 │              │
         ▼                        │              │
┌─────────────────┐               │              │
│    reviewer     │  Reads files, runs checks    │
│                 │◄──────────┐   │              │
└────────┬────────┘           │   │              │
         │                    │   │              │
         ▼ (tool calls)       │   │              │
┌─────────────────┐           │   │              │
│ reviewer_tools  │  read_file_for_review,       │
│                 │  run_syntax_check,           │
│                 │  git_get_file_diff           │
└────────┬────────┘           │   │              │
         │ (done)             │   │              │
         ▼                    │   │              │
┌─────────────────┐           │   │              │
│ process_review  │───────────┘   │              │
│                 │  needs_revision? ────────────┘
│                 │  approved / max revisions? ──► END
└─────────────────┘
```

---

## File Structure

```
src/agents/coding_agent/
├── main.py          # Entry point — run_agent()
├── graph.py         # build_graph() — wires all nodes and edges
├── nodes.py         # build_nodes() — all agent logic, prompts, routing
├── states.py        # AgentState, GitContext TypedDicts
├── tools.py         # make_tools() — filesystem tools (closure-bound)
├── lsp_client.py    # LSPClient — speaks JSON-RPC to pylsp
├── lsp_tools.py     # make_lsp_tools() — LSP tools (closure-bound)
└── git_tools.py     # make_git_tools() + get_git_context()
```

---

## State

```python
class GitContext(TypedDict):
    branch: str
    last_commit: str
    changed_files: list[str]
    staged_files: list[str]
    diff_summary: str

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    working_dir: str
    git_context: GitContext | None
    plan: dict | None
    file_changes: list[dict]
    review_status: Literal["approved", "needs_revision", "pending"]
    review_feedback: str
    revision_count: int
    planner_iterations: int
    executor_iterations: int
    intent: Literal["read_only", "modify"]
```

---

## Agents

### 1. Git Context Node
Runs before all agents. Detects if `working_dir` is a git repo and injects branch, changed files, and diff summary as a message so the planner sees it naturally.

Degrades gracefully — if not a git repo, injects a notice and continues.

### 2. Planner Agent
**Goal:** Explore the codebase and produce a structured JSON plan.

**Tools available:**
| Tool | Purpose |
|---|---|
| `list_directory` | Explore file tree (sandboxed to working_dir) |
| `search_code` | Grep for patterns across files |
| `lsp_find_definition` | Find where a symbol is defined |
| `lsp_find_references` | Find all usages of a symbol |
| `lsp_get_file_symbols` | List all functions/classes in a file |
| `git_get_file_diff` | See what changed in a file since last commit |
| `git_get_recent_commits` | Get recent commit history for context |

**Output — structured JSON plan:**
```json
{
  "task_description": "...",
  "files_to_read": ["path/to/file.py"],
  "files_to_edit": ["path/to/file.py"],
  "steps": ["step 1", "step 2"]
}
```

**Key behaviour:** The planner receives the real file tree pre-injected into its prompt before making any tool calls — eliminating path hallucination.

### 3. Extract Plan Node
Parses the planner's final JSON response into structured state. Strips markdown fences defensively. Falls back gracefully on `JSONDecodeError`.

### 4. Executor Agent
**Goal:** Execute the plan — read files and apply precise edits.

**Tools available:**
| Tool | Purpose |
|---|---|
| `read_file` | Read file contents |
| `apply_diff` | Surgical string replacement (preferred) |
| `write_file` | Full file overwrite (new files only) |

**Key behaviour:** Prefers `apply_diff` over `write_file` to preserve surrounding code. Never wraps output in markdown fences.

### 5. Reviewer Agent
**Goal:** Verify the changes are correct, complete, and safe.

**Tools available:**
| Tool | Purpose |
|---|---|
| `read_file_for_review` | Read edited files |
| `run_syntax_check` | `py_compile` validation |
| `git_get_file_diff` | Compare before/after changes |

**Output — review decision:**
```json
{
  "status": "approved",
  "feedback": "...",
  "issues": []
}
```

### 6. Process Review Node
Parses reviewer JSON output. Routes to:
- `END` if approved
- `END` if `revision_count >= 2` (max revisions reached)
- Back to `executor` if `needs_revision`

---

## Security — Closure Factory Pattern

All tools are created via factory functions bound to `working_dir` at creation time. The LLM cannot override or escape the working directory regardless of what paths it passes.

```python
def make_tools(working_dir: str):
    def _safe_path(path: str) -> str:
        resolved = (Path(working_dir) / path).resolve()
        if not str(resolved).startswith(str(Path(working_dir).resolve())):
            raise ValueError(f"Access denied: {path} is outside {working_dir}")
        return str(resolved)

    @tool
    def read_file(path: str) -> str:
        safe = _safe_path(path)   # working_dir is baked in — LLM cannot change it
        with open(safe) as f:
            return f.read()

    return {"executor": [read_file, ...]}
```

Same pattern applied to `make_lsp_tools(working_dir)` and `make_git_tools(working_dir)`.

---

## Graph Wiring

```python
def build_graph(working_dir: str):
    n = build_nodes(working_dir)

    graph = StateGraph(AgentState)

    # Add all nodes
    for name, fn in {**n["nodes"], **n["tool_nodes"]}.items():
        graph.add_node(name, fn)

    # Entry
    graph.set_entry_point("git_context")
    graph.add_edge("git_context", "planner")

    # Planner flow
    graph.add_conditional_edges("planner", edges["planner_should_continue"], {
        "planner_tools": "planner_tools",
        "extract_plan": "extract_plan"
    })
    graph.add_edge("planner_tools", "planner")
    graph.add_edge("extract_plan", "executor")

    # Executor flow
    graph.add_conditional_edges("executor", edges["executor_should_continue"], {
        "executor_tools": "executor_tools",
        "reviewer": "reviewer"
    })
    graph.add_edge("executor_tools", "executor")

    # Reviewer flow
    graph.add_conditional_edges("reviewer", edges["reviewer_should_continue"], {
        "reviewer_tools": "reviewer_tools",
        "process_review": "process_review"
    })
    graph.add_edge("reviewer_tools", "reviewer")

    # Final routing
    graph.add_conditional_edges("process_review", edges["route_after_review"], {
        "executor": "executor",
        END: END
    })

    return graph.compile()
```

---

## Running the Agent

```python
# main.py
import asyncio
from langchain_core.messages import HumanMessage
from .graph import build_graph
import lsp_tools

async def run_agent(request: str, working_dir: str):
    init_lsp(working_dir)
    app = build_graph(working_dir)

    try:
        result = await app.ainvoke({
            "messages": [HumanMessage(content=request)],
            "working_dir": working_dir,
            "intent": "read_only",
            "plan": None,
            "file_changes": [],
            "review_status": "pending",
            "review_feedback": "",
            "revision_count": 0,
            "planner_iterations": 0,
            "executor_iterations": 0,
        })

        print("=== PLAN ===")
        print(result["plan"])
        print("\n=== REVIEW STATUS ===")
        print(result["review_status"])
        print(result["review_feedback"])

    finally:
        if lsp_tools.lsp_client is not None:
            lsp_tools.lsp_client.shutdown()

asyncio.run(run_agent(
    request="Add input validation to the login function",
    working_dir="/path/to/project"
))
```

```bash
python -m src.agents.coding_agent.main
```

---

## Dependencies

```bash
pip install langgraph langchain-anthropic python-lsp-server pygls
```

---

## Known Limitations & Planned Improvements

| Feature | Status |
|---|---|
| Intent classification (read-only vs modify) | 🔲 Planned |
| Loop guard — max planner/executor iterations | 🔲 Planned |
| Per-file subgraph (process files in isolation) | 🔲 Planned |
| Tree-sitter for AST-based summarization | 🔲 Planned |
| Vector search over codebase embeddings | 🔲 Planned |
| Streaming diffs shown to user before applying | 🔲 Planned |
| Pydantic structured outputs for all agents | 🔲 Planned |

---

## Design Decisions

| Decision | Rationale |
|---|---|
| `apply_diff` preferred over `write_file` | Surgical edits preserve surrounding code — lower risk of regression |
| File tree injected before planner tool calls | Eliminates path hallucination — LLM copies real paths instead of guessing |
| Tools created via factory closure | LLM cannot escape `working_dir` regardless of what path it passes |
| `lsp_tools.lsp_client` accessed via module | Captures the initialized value, not the `None` snapshot at import time |
| Git context as first node | Planner knows which files are already in play before making any decisions |
| `revision_count` cap at 2 | Prevents infinite executor ↔ reviewer loops on unsolvable tasks |
