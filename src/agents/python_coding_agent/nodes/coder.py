from langchain_core.output_parsers import PydanticOutputParser
from ..prompt.coder_prompt import coder_prompt
from src.base_workflows.base_coding_agent_workflow.pydantic_models import CodeOutput, SingleFileOutput
from src.base_workflows.base_coding_agent_workflow.state import BaseFileAgentState
from src.config.llm_config import llm
from src.config.logging_config import logger


coder_parser = PydanticOutputParser(pydantic_object=CodeOutput)
file_coder_parser = PydanticOutputParser(pydantic_object=SingleFileOutput)

def coder_node(state: BaseFileAgentState):
    logger.info("Executing Coder Node")
    formatted_prompt = coder_prompt.format_messages(
        task=state["task"],
        plan=state["file_plan"],
        feedback=state.get("feedback", ""),
        existing_files=state.get("existing_file_content", {}),
        format_instructions=file_coder_parser.get_format_instructions()
    )

    # response = llm.invoke(formatted_prompt)
    llm_structured = llm.with_structured_output(SingleFileOutput)
    try:
        code_output = llm_structured.invoke(formatted_prompt)
        # code_output = coder_parser.parse(response.content)
    except Exception as e:
        logger.error(f"Coder failed for {state['file_plan']['path']}: {e}")
        raise e
    # state["code_changes"] = code_output.model_dump()
    logger.debug(f"Generated CODE: \n {code_output.model_dump()}")
    return {**state, "code_change": code_output.change.model_dump(), "written_files": []} # reset written_files on each coder attempt so writer starts fresh
