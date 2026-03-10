from src.base_workflows.base_coding_agent_workflow.state import BaseAgentState
from pathlib import Path
from src.config.logging_config import logger

def file_validator_node(state: BaseAgentState):
    """
    Validates and corrects file actions in the plan based on actual filesystem state.
    Overrides LLM hallucinations: if file exists → update, if not → create.
    """
    plan = state["plan"]
    corrected = []

    for file in plan["files"]:
        file_path = Path(file["path"])
        action = file["action"]
        actual_action = "update" if file_path.is_file() else "create"

        if action != actual_action:
            logger.warning(
                f"Action mismatch for '{file_path}': "
                f"LLM said '{action}' but file {'exists' if file_path.is_file() else 'does not exist'}. "
                f"Correcting to '{actual_action}'."
            )

        corrected.append({**file, "action": actual_action})

    return {**state, "plan": {**plan, "files": corrected}}
