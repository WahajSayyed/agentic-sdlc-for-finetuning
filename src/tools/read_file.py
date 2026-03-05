import os
from pathlib import Path
from langchain_core.tools import tool
from dotenv import load_dotenv
load_dotenv()


# @tool
# def read_file(file_path: str) -> str:
#     """Read file from disk"""
#     base_path = os.getenv("WORKING_DIR")
#     if not base_path:
#         raise ValueError("WORKING_DIR_NOT_SET")
#     absolute_file_path = os.path.join(base_path, file_path)

#     if not absolute_file_path:
#         raise FileNotFoundError("File not found")
#     with open(absolute_file_path, "r") as fhand:
#         return fhand.read()



@tool
def read_file(file_path: str) -> str:
    """Read file from disk inside WORKING_DIR only."""
    
    # base_path = os.getenv("WORKING_DIR")
    # if not base_path:
    #     return "WORKING_DIR_NOT_SET"

    # base_path = Path(base_path).resolve()
    # target_path = (base_path / file_path).resolve()

    # # Prevent directory traversal
    # if not str(target_path).startswith(str(base_path)):
    #     return "INVALID_PATH"
    file_path = Path(file_path).resolve()
    if not file_path.is_file():
        return "FILE_NOT_FOUND"

    return file_path.read_text(encoding="utf-8")