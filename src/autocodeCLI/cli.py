import os
import uuid
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text
from rich.markdown import Markdown
import time


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
        f.write(f"GOOGLE_API_KEY={key}\n")
    os.environ["GOOGLE_API_KEY"] = key
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
    if not os.environ.get("GOOGLE_API_KEY"):
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
            if not os.environ.get("GOOGLE_API_KEY"):
                console.print("[bold red]❌ Cannot proceed. API Key is missing.[/bold red]")
                console.print("Please set it first by typing: [bold yellow]/api-key YOUR_NVIDIA_API_KEY[/bold yellow]\n")
                continue

            # 5. Fetch the agent
            agent = get_agent()

            console.print()
            response = ""
            
            # Start the timer
            start_time = time.time()

            current_ai_msg_id = None

            # Use console.status instead of Live for automatic cleanup
            with console.status("[bold cyan]🧠 Thinking...[/bold cyan]", spinner="dots") as status:
                
                for chunk, metadata in agent.stream(
                    {"messages": [HumanMessage(content=task)]},
                    config=config,
                    stream_mode="messages",
                ):
                    if isinstance(chunk, AIMessageChunk):
                    # 🚀 THE FIX: Check if this is a brand new AI message
                        if chunk.id and chunk.id != current_ai_msg_id:
                            response = ""  # Clear out the intermediate junk!
                            current_ai_msg_id = chunk.id  # Save the new ID
                            
                        # Append the actual response text for this specific message
                        if chunk.content:
                            response += chunk.content

                        # Update status if the agent is reasoning
                        reasoning = chunk.additional_kwargs.get("reasoning_content")
                        if reasoning:
                            status.update("[bold cyan]🧠 Thinking deeply...[/bold cyan]")

                        # Update status if the agent calls a tool
                        tool_calls = getattr(chunk, "tool_call_chunks", None)
                        if tool_calls:
                            tool = tool_calls[0].get("name")
                            if tool:
                                status.update(f"[bold yellow]🔧 Running tool: {tool}...[/bold yellow]")

                    elif isinstance(chunk, ToolMessage):
                        status.update(f"[bold green]✅ Finished: {chunk.name}[/bold green]")

                    elif isinstance(chunk, RemoveMessage):
                        pass

                    else:
                        status.update(f"[bold magenta]📨 Processing: {type(chunk).__name__}[/bold magenta]")

            # The spinner automatically disappears the moment we exit the 'with' block!
            
            # Stop the timer and calculate elapsed time
            end_time = time.time()
            elapsed_time = end_time - start_time

            # Print the duration cleanly
            console.print(f"[dim]⚡ Task completed in {elapsed_time:.2f}s[/dim]\n")

            # Render the final response beautifully with Markdown syntax highlighting
            if response:
                console.print(Markdown(response))

            console.print()
            console.rule()

        except KeyboardInterrupt:
            console.print("\n\n[bold red]Interrupted.[/bold red]")
            break
        except Exception as e:
            console.print(f"[bold red]✗ Error: {e}[/bold red]")


if __name__ == "__main__":
    main()