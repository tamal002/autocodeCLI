import os
import uuid
import questionary
import autocodeCLI.agent as agent_module
# from pathlib import Path
# from dotenv import load_dotenv
from rich.console import Console
# from rich.live import Live
# from rich.spinner import Spinner
# from rich.text import Text
from rich.markdown import Markdown
import time
from autocodeCLI.model_comfig import load_settings, save_settings
from langgraph.stream.transformers import AIMessageChunk
from langchain_core.messages import HumanMessage, ToolMessage, RemoveMessage
from autocodeCLI.agent import get_agent, WORKING_DIR
from autocodeCLI.banner import banner


settings = load_settings()



if settings["api_key"] or settings["api_key"] != "":
    os.environ[f"{settings['provider'].upper()}_API_KEY"] = settings["api_key"]
os.environ["AUTOCODE_PROVIDER"] = settings.get("provider", "openai")
os.environ["AUTOCODE_MODEL"] = settings.get("model", "gpt-4o")





def main():
    console = Console()
    console.print(banner, style="cyan")
    console.print("[bold cyan]🚀 Auto-code CLI[/bold cyan]")
    console.print(f"[dim]Active Directory:[/] {WORKING_DIR}")
    console.rule()

    # Determine runtime provider state
    provider = os.environ.get("AUTOCODE_PROVIDER", "openai")
    model_name = os.environ.get("AUTOCODE_MODEL", "gpt-4o")
    current_key_env = f"{provider.upper()}_API_KEY"
    has_valid_key = bool(os.environ.get(current_key_env))

    # Greet user dynamically based on active configuration data
    if not has_valid_key:
        console.print(f"[bold yellow]⚠️  No API Key detected for runtime provider: {provider}[/bold yellow]")
        console.print("To configure your engine, issue the setup command:")
        console.print("[bold white]/set-model <provider> <model_name> <api_key>[/bold white]")
        console.print("Example: /set-model anthropic claude-sonnet-5 sk-ant-...\n")
    else:
        console.print(f"[bold green]✅ Engine Operational:[/] {provider} ({model_name})")
        console.print("[dim]Use /set-model to modify your core infrastructure environment at any time.[/]")

    console.print("[dim]Type 'exit' or 'quit' to leave.[/]\n")

    config = {
        "configurable": {
            "thread_id": str(uuid.uuid4())
        }
    }

    status = console.status("[bold cyan]🧠 Thinking...[/bold cyan]", spinner="dots")
    

    def cli_approval_hook(action_description: str) -> bool:
        status.stop() # Pause the spinner
        console.print() 
        
        # Launch the interactive arrow-key menu
        choice = questionary.select(
            f"⚠️ The agent wants to {action_description}. Proceed?",
            choices=["Allow", "Reject"],
            default="Reject"
        ).ask()
        
        approved = (choice == "Allow")
        
        if not approved:
            console.print("[dim]Action denied. Returning control to agent...[/dim]\n")
            
        status.start() # Resume the spinner
        return approved

    agent_module.ask_user_approval = cli_approval_hook

    while True:
        try:
            task = console.input("[bold green]❯[/] ").strip()

            if not task:
                continue

            if task.lower() in {"exit", "quit"}:
                console.print("\n👋 Goodbye!\n")
                break

            # Handle model re-configuration profiles dynamically
            if task.startswith("/set-model "):
                parts = task.split()
                if len(parts) == 4:
                    _, new_provider, new_model, new_key = parts
                    save_settings(new_provider, new_model, new_key)
                    
                    # Refresh local loop states instantly
                    provider = os.environ.get("AUTOCODE_PROVIDER")
                    model_name = os.environ.get("AUTOCODE_MODEL")
                    console.print(f"[bold green]✅ Core engine migrated to {new_provider} ({new_model}) successfully![/bold green]\n")
                else:
                    console.print("[bold red]❌ Invalid usage pattern.[/bold red]")
                    console.print("Required syntax: [bold white]/set-model <provider> <model_name> <api_key>[/bold white]\n")
                continue


            # Core Blocker Rule: Guard loop execution against unassigned keys matching active providers
            provider = os.environ.get("AUTOCODE_PROVIDER", "openai")
            current_key_env = f"{provider.upper()}_API_KEY"
            if not os.environ.get(current_key_env):
                console.print(f"[bold red]❌ Execution halted. API Key for '{provider}' is completely blank.[/bold red]")
                console.print("Provision credentials using: [bold yellow]/set-model <provider> <model_name> <api_key>[/bold yellow]\n")
                continue

            # Fetch a fresh graph instance updated via backend factory
            agent = get_agent()

            console.print()
            response = ""
            start_time = time.time()
            current_ai_msg_id = None

            status.update("[bold cyan]🧠 Thinking...[/bold cyan]")

            with status:
                
                for chunk, metadata in agent.stream(
                    {"messages": [HumanMessage(content=task)]},
                    config=config,
                    stream_mode="messages",
                ):
                    if isinstance(chunk, AIMessageChunk):
                        if chunk.id and chunk.id != current_ai_msg_id:
                            response = ""  
                            current_ai_msg_id = chunk.id  
                            
                        if chunk.content:
                            response += chunk.content

                        reasoning = chunk.additional_kwargs.get("reasoning_content")
                        if reasoning:
                            status.update("[bold cyan]🧠 Thinking deeply...[/bold cyan]")

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

            elapsed_time = time.time() - start_time
            console.print(f"[dim]⚡ Task completed in {elapsed_time:.2f}s[/dim]\n")

            if response:
                console.print(Markdown(response))

            console.print()
            console.rule()

        except KeyboardInterrupt:
            console.print("\n\n[bold red]Interrupted.[/bold red]")
            break
        except Exception as e:
            console.print(f"[bold red]✗ Error encountered: {e}[/bold red]")

if __name__ == "__main__":
    main()