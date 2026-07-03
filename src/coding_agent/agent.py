import os
from pathlib import Path
# from dotenv import load_dotenv

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langgraph.checkpoint.memory import InMemorySaver
from langchain_nvidia_ai_endpoints import ChatNVIDIA

# Setup Working Directory and Environment
WORKING_DIR = os.getcwd()
# CONFIG_FILE = Path.home() / ".autocode_env"

# if CONFIG_FILE.exists():
#     load_dotenv(CONFIG_FILE)
# else:
#     load_dotenv()


def delete_file(path: str) -> str:
    """
        Delete a file from the current project.

    Args:
        path: Relative path to the file (e.g. "/prime.py").

    Returns:
        A message indicating whether the file was deleted.
    """
    path = path.lstrip("/\\")
    full_path = Path(WORKING_DIR) / path

    if not full_path.exists():
        return f"{full_path} does not exist."

    full_path.unlink()

    return f"Deleted {full_path}"


# sub-agent
code_reviewer = {
    "name": "code_reviewer",
    "description": "Expert agent responsible for comprehensive code review.",
    "system_prompt": """
            You are a senior software engineer specializing in code reviews.

            Your responsibilities include:
            1. Detect syntax and runtime errors.
            2. Identify logical bugs and incorrect assumptions.
            3. Find edge cases the code does not handle.
            4. Review algorithmic complexity and performance.
            5. Detect security vulnerabilities.
            6. Evaluate readability, maintainability, and code style.
            7. Suggest refactoring where appropriate.
            8. Recommend better data structures or algorithms when beneficial.
            9. Explain every issue with clear reasoning.
            10. Provide corrected code snippets when necessary.

            Always structure your review as:

            ## Summary
            Overall assessment.

            ## Issues
            - Severity (Critical / High / Medium / Low)
            - Description
            - Why it is a problem
            - Recommended fix

            ## Positive Aspects
            Mention what is done well.

            ## Improved Code
            Provide revised code if substantial changes are needed.
        """,
    "tools": []
}


SYSTEM_PROMPT = """
You are a Senior Python Developer Agent.

**Role**: You are a senior Python developer. Your objective is to take natural language coding tasks from the user and deliver clean, production-ready, well-structured Python projects directly into the current directory.

**Workflow Rules**:
1. **Planning**: Use the write_to_dos tool to break the task into clear, logical implementation steps.
2. **Development**: Write actual Python files using write_file directly in the current root directory. Always use descriptive naming, include docstrings for functions, and ensure type hints are properly annotated.
3. **Project Requirements**: Always generate a README.md that includes: project purpose, setup instructions, and execution instructions. Create a requirements.txt file only if third-party packages are required.
4. **Quality Control**: Once code is written, delegate a review to the code_reviewer sub-agent. If the reviewer flags issues, use edit_file to apply fixes until the review is clean.
5. **Final Delivery**: Use ls to verify all files and inform the user how to get started by referencing the README.md.
6. **Maintenance**: Always update your to-do list status to 'complete' as you progress.

**Guidelines**:
- You are operating in the user's current working directory. Do not create a new root folder for the project; put the files right where you are.
- Prioritize production-quality code; avoid pseudo-code.
- If a task is complex, modularize the code across multiple files.
"""


checkpointer = InMemorySaver()

# ---------------------------------------------------------
# LAZY AGENT INITIALIZATION
# ---------------------------------------------------------
_agent_instance = None


def get_agent():
    """Lazily initializes and returns the agent instance."""
    global _agent_instance
    if _agent_instance is None:
        model = ChatNVIDIA(model="z-ai/glm-5.2")
        
        _agent_instance = create_deep_agent(
            model=model,
            system_prompt=SYSTEM_PROMPT,
            tools=[delete_file],
            subagents=[code_reviewer],
            # Note: virtual_mode=False is critical here so it writes actual files to the user's directory
            backend=FilesystemBackend(root_dir=WORKING_DIR, virtual_mode=False),
            checkpointer=checkpointer
        )
    return _agent_instance


def reset_agent():
    """Forces the agent to rebuild on the next call (useful if API key changes)."""
    global _agent_instance
    _agent_instance = None