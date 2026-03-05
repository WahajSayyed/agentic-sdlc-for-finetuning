
class Python_Coding_Prompt:
    def __init__(self, task):
        self.task = task
    
        self.python_coding_agent_prompt = f"""You are senior python developer. 
    Based on the given task you need to generate the code and the python filename for which the code has been generated.
    
    Task: {task}

    Generate the output in below format:
    Filename:
    Code:
    """