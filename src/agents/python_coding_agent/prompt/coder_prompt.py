from langchain_core.prompts import ChatPromptTemplate


coder_prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are a senior software engineer.

Your job:
Generate precise code changes based on the plan.

Rules:
- For "create" → produce complete new file.
- For "update" → modify existing file carefully.
- Preserve unrelated logic.
- Do NOT remove functionality unless required.
- Keep changes minimal and clean.
- Maintain style consistency.
- Return structured JSON only.
"""),
    ("user", """
Task:
{task}

Implementation Plan:
{plan}

Static Analysis Feedback (if any):
{feedback}

Existing Files (only for updates):
{existing_files}

Format Instructions:
{format_instructions}
""")
])
