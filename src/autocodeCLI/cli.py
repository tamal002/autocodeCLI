import os
import uuid
from pathlib import Path
from dotenv import load_dotenv

from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

from langgraph.stream.transformers import AIMessageChunk
from langchain_core.messages import HumanMessage, ToolMessage, RemoveMessage

# Import agent logic from our separated file
from autocodeCLI.agent import get_agent, reset_agent, WORKING_DIR

CONFIG_FILE = Path.home() / ".autocode_env"

# 1. Attempt to load the API key on startup
if CONFIG_FILE.exists():
    load_dotenv(CONFIG_FILE)
else:
    load_dotenv()

def save_api_key(key: str):
    """Saves the API key to the user's home directory and updates the environment."""
    with open(CONFIG_FILE, "w") as f:
        f.write(f"NVIDIA_API_KEY={key}\n")
    os.environ["NVIDIA_API_KEY"] = key
    reset_agent() # Clear old agent so it uses the new key


banner = f"""
 █████╗  ██╗   ██╗ ████████╗  ██████╗   ██████╗   ██████╗  ██████╗  ███████╗
██╔══██╗ ██║   ██║ ╚══██╔══╝ ██╔═══██╗ ██╔════╝  ██╔═══██╗ ██╔══██╗ ██╔════╝
███████║ ██║   ██║    ██║    ██║   ██║ ██║       ██║   ██║ ██║  ██║ █████╗  
██╔══██║ ██║   ██║    ██║    ██║   ██║ ██║       ██║   ██║ ██║  ██║ ██╔══╝  
██║  ██║ ╚██████╔╝    ██║    ╚██████╔╝ ╚██████╗  ╚██████╔╝ ██████╔╝ ███████╗
╚═╝  ╚═╝  ╚═════╝     ╚═╝     ╚═════╝   ╚═════╝   ╚═════╝  ╚═════╝  ╚══════╝
"""

def main():
    console = Console()
    console.print(banner, style="cyan")
    console.print("[bold cyan]🚀 Auto-code CLI[/bold cyan]")
    console.print(f"[dim]Active Directory:[/] {WORKING_DIR}")
    console.rule()

    # 2. Greet the user based on whether the key is set or missing
    if not os.environ.get("NVIDIA_API_KEY"):
        console.print("[bold yellow]⚠️  No API Key detected![/bold yellow]")
        console.print("To get started, you must set your NVIDIA API key by typing:")
        console.print("[bold white]/api-key YOUR_API_KEY[/bold white]\n")
    else:
        console.print("[bold green]✅ API Key loaded successfully.[/bold green]")
        console.print("[dim]Type /api-key YOUR_KEY if you ever need to update it.[/]")

    console.print("[dim]Type 'exit' or 'quit' to leave.[/]\n")

    config = {
        "configurable": {
            "thread_id": str(uuid.uuid4())
        }
    }

    while True:
        try:
            task = console.input("[bold green]❯[/] ").strip()

            if not task:
                continue

            if task.lower() in {"exit", "quit"}:
                console.print("\n👋 Goodbye!\n")
                break

            # 3. Handle the API key setup command
            if task.startswith("/api-key "):
                new_key = task.split("/api-key ", 1)[1].strip()
                save_api_key(new_key)
                console.print("[bold green]✅ API Key saved successfully! You can now start coding.[/bold green]\n")
                continue

            # 4. THE BLOCKER: Prevent the agent from running if key is missing
            if not os.environ.get("NVIDIA_API_KEY"):
                console.print("[bold red]❌ Cannot proceed. API Key is missing.[/bold red]")
                console.print("Please set it first by typing: [bold yellow]/api-key YOUR_NVIDIA_API_KEY[/bold yellow]\n")
                continue

            # 5. Only fetch and run the agent if we passed the blocker
            agent = get_agent()

            console.print()
            spinner = Spinner("dots", text="Thinking...")
            response = ""

            with Live(spinner, console=console, refresh_per_second=15):
                for chunk, metadata in agent.stream(
                    {"messages": [HumanMessage(content=task)]},
                    config=config,
                    stream_mode="messages",
                ):
                    if isinstance(chunk, AIMessageChunk):
                        if chunk.content:
                            response += chunk.content

                        reasoning = chunk.additional_kwargs.get("reasoning_content")
                        if reasoning:
                            spinner.text = "🧠 Thinking..."

                        tool_calls = getattr(chunk, "tool_call_chunks", None)
                        if tool_calls:
                            tool = tool_calls[0].get("name")
                            if tool:
                                spinner.text = f"🔧 {tool}..."

                    elif isinstance(chunk, ToolMessage):
                        spinner.text = f"✅ {chunk.name}"

                    elif isinstance(chunk, RemoveMessage):
                        pass

                    else:
                        spinner.text = f"📨 {type(chunk).__name__}"

            console.print()

            if response:
                console.print(Text(response))

            console.rule()

        except KeyboardInterrupt:
            console.print("\n\nInterrupted.")
            break
        except Exception as e:
            console.print(f"[bold red]✗ Error: {e}[/bold red]")

if __name__ == "__main__":
    main()