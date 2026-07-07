import os
import subprocess
from pathlib import Path
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langgraph.checkpoint.memory import InMemorySaver
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool

# Setup Working Directory and Environment
WORKING_DIR = os.getcwd()


ask_user_approval = None


@tool(description="Deletes a file from the current project directory.")
def delete_file(path: str) -> str:
    """Delete a file from the current project."""
    path = path.lstrip("/\\")
    full_path = Path(WORKING_DIR) / path

    # 1. STOP AND ASK THE HUMAN
    if ask_user_approval:
        is_approved = ask_user_approval(f"delete the file: {full_path.name}")
        if not is_approved:
            return f"Error: The user denied permission to delete {full_path.name}."

    # 2. EXECUTE IF APPROVED
    if not full_path.exists():
        return f"{full_path} does not exist."

    full_path.unlink()
    return f"Deleted {full_path}"



@tool(description="Executes a git command in the current project directory.")
def execute_git_command(command: str) -> str:
    """
    Execute a Git command safely within the project repository.

    Args:
        command: The complete git command to run (e.g., "git status", "git add .", "git commit -m 'feat: init'").

    Returns:
        The standard output or error from the git execution.
    """
    # Guardrail: Ensure it is strictly a git command for security boundaries
    clean_command = command.strip()
    if not clean_command.startswith("git"):
        return "Error: This tool only accepts commands that begin with 'git'."

    # Identify modifying/destructive git operations that require human intervention
    write_operations = ["commit", "push", "reset", "clean", "checkout", "revert", "merge", "init"]
    
    # Check if the command contains any of the write operations
    requires_approval = any(op in clean_command for op in write_operations)

    # Trigger your Questionary UI hook if approval is required
    if requires_approval and ask_user_approval:
        is_approved = ask_user_approval(f"execute command: '{clean_command}'")
        if not is_approved:
            return f"Error: The user explicitly denied permission to run '{clean_command}'."

    try:
        # Run the command safely inside the active workspace directory
        result = subprocess.run(
            clean_command,
            shell=True,
            cwd=WORKING_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30  # Prevent hanging commands
        )
        
        output = result.stdout if result.stdout else ""
        error = result.stderr if result.stderr else ""
        
        if result.returncode != 0:
            return f"Command failed with exit code {result.returncode}.\nOutput: {output}\nError: {error}"
        
        return output if output.strip() else "Command executed successfully with no text output."

    except Exception as e:
        return f"An exception occurred while executing the system process: {str(e)}"



# sub-agent
code_reviewer = {
    "name": "code_reviewer",
    "description": "Expert agent responsible for comprehensive code review across all languages.",
    "system_prompt": """
            You are a senior software engineer specializing in universal code reviews.

            Your responsibilities include:
            1. Detect syntax and runtime errors specific to the language being used.
            2. Identify logical bugs and incorrect assumptions.
            3. Find edge cases the code does not handle.
            4. Review algorithmic complexity and performance.
            5. Detect security vulnerabilities.
            6. Evaluate readability, maintainability, and standard code style for the given framework.
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
You are a Universal Software Engineering Agent.

**Role**: Your objective is to take natural language coding tasks from the user and deliver clean, production-ready, well-structured code directly into the current directory. You operate seamlessly across any programming language, framework, or environment.

**Workflow Rules**:
1. **Understand First**: Check the current directory structure before assuming where files belong.
2. **Development**: Write actual files directly in the current root directory. Always use descriptive naming, include standard documentation, and follow language-specific best practices.
3. **Project Requirements**: If creating a new project, generate a README.md that includes: project purpose, setup instructions, and execution instructions. Create dependency files (like package.json, requirements.txt, or Cargo.toml) appropriate for the detected stack.
4. **Quality Control**: Once code is written, delegate a review to the code_reviewer sub-agent. If the reviewer flags issues, apply fixes until the review is clean.
5. **Final Delivery**: Verify all files and inform the user how to get started.

**Version Control Rules**:
- You have access to the `execute_git_command` tool. 
- Use `git status` or `git diff` to explore the codebase state if you are unsure what changes have been made.
- Do not make a git commit unless the user explicitly asks you to save or commit your changes.

**Guidelines**:
- You are operating in the user's current working directory. Do not create a new root folder for the project unless explicitly instructed; put the files right where you are.
- Prioritize production-quality code over pseudo-code.
- If a task is complex, modularize the code across multiple logical files based on standard architectural patterns for that language.
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
        
        # Dynamically fetch the provider and model configured by cli.py
        provider = os.environ.get("AUTOCODE_PROVIDER", "openai")
        model_name = os.environ.get("AUTOCODE_MODEL", "gpt-4o")

        # Use LangChain's universal initializer to build the exact model class needed
        model = init_chat_model(
            model=model_name,
            model_provider=provider,
            temperature=0.1,
        )

        _agent_instance = create_deep_agent(
            model=model,
            system_prompt=SYSTEM_PROMPT,
            tools=[delete_file, execute_git_command],
            subagents=[code_reviewer],
            # Note: virtual_mode=False is critical here so it writes actual files to the user's directory
            backend=FilesystemBackend(root_dir=WORKING_DIR, virtual_mode=False),
            checkpointer=checkpointer
        )
    return _agent_instance




def reset_agent():
    """Forces the agent to rebuild on the next call (crucial when providers/models change at runtime)."""
    global _agent_instance
    _agent_instance = None