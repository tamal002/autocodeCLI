import sys
from pathlib import Path
from autocodeCLI.model_comfig import save_settings



# Using a structured directory for model-agnostic profiles
SETTINGS_DIR = Path.home() / ".autocode"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"


def execute_set_model(args, console):
    """Executes the set-model command and exits the application."""

    
    save_settings(args.provider, args.model, args.api_key, args.base_url)
    
    console.print("[bold green]✅ Success:[/] Global configuration updated successfully.")
    console.print(f"[dim]Saved profile to:[/] {SETTINGS_FILE}")
    console.print(f"[dim]Active Driver:[/] {args.provider} ({args.model})")
    if args.base_url:
        console.print(f"[dim]Endpoint Target:[/] {args.base_url}")
        
    sys.exit(0)  # Terminate immediately after configuring