import os
from langchain_core.tools import tool
from dotenv import load_dotenv
load_dotenv()

working_dir = os.getenv("WORKING_DIR")

@tool
def read_file_structure(path: str|None = working_dir, execution_id: int = 0):
    """
    Returns a tree-style files structure of the repository
    """
    # path = os.path.join(path, str(execution_id))
    print(path)
    tree_lines = []
    for root, dirs, files in os.walk(path):
        level = root.replace(path, "").count(os.sep)
        indent = " " * 2 * level
        tree_lines.append(f"{indent}{os.path.basename(root)}/")

        sub_indent = " " * 2 * (level + 1)
        for f in files:
            tree_lines.append(f"{sub_indent}{f}")

    return "\n".join(tree_lines)

if __name__ == "__main__":
    result = read_file_structure.invoke(working_dir)
    print(result)