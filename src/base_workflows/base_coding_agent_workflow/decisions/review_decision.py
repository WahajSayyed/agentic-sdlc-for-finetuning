import os
from typing_extensions import Literal
from src.base_workflows.base_coding_agent_workflow.state import BaseFileAgentState
from dotenv import load_dotenv
from src.config.logging_config import logger

load_dotenv()

MAX_REVIEW_RETRIES = int(os.getenv("MAX_REVIEW_RETRIES", 3))

def review_decision(state: BaseFileAgentState) -> Literal["approve", "revise", "abort"]:
    review = state.get("review")
    
    if not review:
        logger.warning("No review found in state, defaulting to revise")
        return "revise"

    retry_count = dict(state.get("retry_count") or {})
    current_count = retry_count.get("review", 0)

    if review.get("status", "").lower() == "approved":
        return "approve"

    if current_count >= MAX_REVIEW_RETRIES:
        logger.warning(f"Max review retries ({MAX_REVIEW_RETRIES}) reached, aborting.")
        return "abort"

    return "revise"