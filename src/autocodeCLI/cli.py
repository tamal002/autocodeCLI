import os
import uuid
import questionary
import autocodeCLI.agent as agent_module
from rich.console import Console
from rich.markdown import Markdown
import time
from autocodeCLI.model_comfig import load_settings
from autocodeCLI.parser import setup_cli_parser
from autocodeCLI.commands import execute_set_model
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

    # 1. SETUP TERMINAL ARGUMENT PARSING (Delegated to parser.py)
    parser = setup_cli_parser()
    args = parser.parse_args()

    # 2. RUNTIME CONFIGURATION MODE BOUNDARY
    if args.command == "set-model":
        execute_set_model(args, console)

    # 3. RUNTIME INTERACTIVE CHAT MODE BOUNDARY
    settings = load_settings()

    # 3.1 Dynamically inject configuration parameters into environment memory
    if settings["api_key"] or settings["api_key"] != "":
        os.environ[f"{settings['provider'].upper()}_API_KEY"] = settings["api_key"]
    os.environ["AUTOCODE_PROVIDER"] = settings.get("provider", "openai")
    os.environ["AUTOCODE_MODEL"] = settings.get("model", "gpt-4o")
    if settings.get("base_url"):
        os.environ["AUTOCODE_BASE_URL"] = settings["base_url"]


    # 3.2 Display a welcome banner and current configuration state
    console.print(banner, style="cyan")
    console.print("[bold cyan]🚀 Auto-code CLI[/bold cyan]")
    console.print(f"[dim]Active Directory:[/] {WORKING_DIR}")
    console.rule()


    # 3.3 Determine runtime provider state
    provider = os.environ.get("AUTOCODE_PROVIDER", "openai")
    model_name = os.environ.get("AUTOCODE_MODEL", "gpt-4o")
    current_key_env = f"{provider.upper()}_API_KEY"

    chat_enable = bool(os.environ.get(current_key_env))


    # 3.4 Greet user dynamically based on active configuration data
    if not chat_enable:
        console.print(f"[bold yellow]⚠️  No API Key detected for provider: {provider}[/bold yellow]")
        console.print("To configure your engine out of chat, run this in your terminal:")
        console.print("[bold white]autocode set-model <provider> <model_name> <api_key>\nfor provider 'ollama', no API key is required[/bold white]\n")
    else:
        console.print(f"[bold green]✅ Engine Operational:[/] {provider} ({model_name})")
        console.print("[dim]Use the system shell command 'set-model' to redirect backend targets outside of chat.[/]")

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

    while chat_enable:
        try:
            task = console.input("[bold green]❯[/] ").strip()

            if not task:
                continue

            if task.lower() in {"exit", "quit"}:
                console.print("\n👋 Goodbye!\n")
                break

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