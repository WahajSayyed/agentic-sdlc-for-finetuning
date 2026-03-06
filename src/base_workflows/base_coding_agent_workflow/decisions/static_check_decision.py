import os
from dotenv import load_dotenv
from typing_extensions import Literal
from src.base_workflows.base_coding_agent_workflow.state import BaseFileAgentState
from src.config.logging_config import logger

load_dotenv()
MAX_STATIC_CHECK_RETRIES = int(os.getenv("MAX_STATIC_CHECK_RETRIES", 3))

def static_check_decision(state: BaseFileAgentState) -> Literal["pass", "abort", "retry"]:
    if state["static_check_success"]:
        state["retry_count"]["static_check_count"] = 0  # reset
        return "pass" 
    state["retry_count"]["static_check_count"] += 1

    if state["retry_count"]["static_check_count"] >= MAX_STATIC_CHECK_RETRIES:
        return "abort"
    return "retry"
