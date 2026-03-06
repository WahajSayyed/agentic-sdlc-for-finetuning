from typing_extensions import Literal
from src.base_workflows.base_coding_agent_workflow.state import BaseAgentState
from src.config.logging_config import logger

def should_read(state: BaseAgentState) -> Literal["reader", "process_files"]:
    plan = state["plan"]
    try:
        for file in plan["files"]:
            if file["action"] == "update":
                return "reader"
        return "process_files"
    except FileNotFoundError:
        return "process_files"
    except Exception as e:
        print(f"Error occured: {e}")
        return "process_files"