import json
import subprocess
from src.base_workflows.base_coding_agent_workflow.state import BaseFileAgentState
from src.config.logging_config import logger



def static_check_node(state: BaseFileAgentState):
    logger.info("Executing Static Check Node")
    written_files = state.get("written_files", [])

    if not written_files:
        logger.info("No files written, skipping static check.")
        return {
            **state,
            "static_check_success": True,
            "static_check_output": "No files written.",
            "feedback": None
        }

    result = subprocess.run(
        ["ruff", "check", "--output-format", "json"] + written_files,
        capture_output=True,
        text=True
    )

    success = result.returncode == 0
    output = result.stdout + result.stderr
    feedback = None

    if not success:
        feedback = summarize_ruff_issue(result.stdout)
        # Increment retry counter
        retry_count = dict(state.get("retry_count") or {})
        retry_count["static_check_count"] = retry_count.get("static_check_count", 0) + 1
        logger.info(f"Static Check FEEDBACK:\n{feedback}")
    else:
        retry_count = dict(state.get("retry_count") or {})

    return {
        **state,
        "static_check_success": success,
        "static_check_output": output,
        "feedback": feedback,
        "retry_count": retry_count
    }


def summarize_ruff_issue(json_output: str) -> str:
    try:
        issues = json.loads(json_output)
        issue_list = [
            f"{i['filename']}:{i['location']['row']} {i['code']} {i['message']}"
            for i in issues
        ]
        return "Ruff reported:\n" + "\n".join(issue_list)
    except Exception:
        return "Ruff reported issues but JSON parsing failed:\n" + json_output
