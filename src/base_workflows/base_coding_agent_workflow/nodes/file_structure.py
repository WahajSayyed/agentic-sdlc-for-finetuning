from src.base_workflows.base_coding_agent_workflow.state import BaseAgentState
from src.config.logging_config import logger
from src.tools.read_file_structure import read_file_structure


def file_structure_node(state: BaseAgentState):

    logger.info("Reading File Strucutre")
    
    structure = read_file_structure.invoke(state["work_dir"])
    state["file_structure"] = structure
    
    logger.debug(f"Updating File Structure: \n{structure}")
    
    return {"file_structure": state["file_structure"]}