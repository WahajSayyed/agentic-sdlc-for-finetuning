from langchain_core.output_parsers import PydanticOutputParser
from ..prompt.reviewer_prompt import reviewer_prompt
from src.base_workflows.base_coding_agent_workflow.pydantic_models import ReviewResult
from src.base_workflows.base_coding_agent_workflow.state import BaseFileAgentState
from src.config.llm_config import llm
from src.config.logging_config import logger

reviewer_parser = PydanticOutputParser(pydantic_object=ReviewResult)

def reviewer_node(state: BaseFileAgentState):
    logger.info("Executing Reviewer Node")
    formatted_prompt = reviewer_prompt.format_messages(
        task=state["task"],
        plan=state["file_plan"],              # actual plan for this file
        existing_files=state.get("existing_file_content", ""),  # single file content
        code_changes=state["code_change"],
        format_instructions=reviewer_parser.get_format_instructions()
    )

    llm_structured = llm.with_structured_output(ReviewResult)
    review_result = llm_structured.invoke(formatted_prompt)
    # review_result = reviewer_parser.parse(response.content)

    retry_count = dict(state.get("retry_count") or {})
    if review_result.status.lower() != "approved":
        retry_count["review"] = retry_count.get("review", 0) + 1

    logger.info(f"Review by Reviewer Node:\n{review_result.model_dump()}")
    
    return {
        **state,
        "review": review_result.model_dump(),  # return delta only, not mutated state
        "retry_count": retry_count
    }
