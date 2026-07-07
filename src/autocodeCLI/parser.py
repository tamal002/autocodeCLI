import argparse



def setup_cli_parser() -> argparse.ArgumentParser:
    """
    Configures and returns the main argument parser with all subcommands.
    Add any new global CLI subcommands here.
    """
    parser = argparse.ArgumentParser(
        description="Auto-code CLI: An autonomous software engineering agent."
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Define the 'set-model' command configuration
    set_model_cmd = subparsers.add_parser("set-model", help="Configure the global model credentials")
    set_model_cmd.add_argument("provider", help="The AI provider (e.g., openai, anthropic)")
    set_model_cmd.add_argument("model", help="The model name (e.g., gpt-4o)")
    

    # OPTIONAL: The user can leave these blank. 
    # If left blank, they default to an empty string.
    set_model_cmd.add_argument("api_key", nargs="?", default="not_required", help="Your API key")
    set_model_cmd.add_argument("base_url", nargs="?", default="", help="Optional base URL")
    
    return parser