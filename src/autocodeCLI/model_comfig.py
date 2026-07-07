import json
import os
from pathlib import Path
from autocodeCLI.agent import reset_agent


SETTINGS_DIR = Path.home() / ".autocode"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"



def load_settings():
    """Loads the model configuration profile. Defaults to OpenAI if empty."""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"provider": "openai", "model": "gpt-4o", "api_key": ""}




def save_settings(provider: str, model_name: str, key: str, base_url: str):
    """Saves the settings to disk, exports them to environment variables, and resets the agent machine."""
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    
    settings_data = {
        "provider": provider.lower().strip(),
        "model": model_name.strip(),
        "api_key": key.strip(),
        "base_url": base_url.strip()
    }
    
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings_data, f, indent=4)
        
    # Dynamically inject configuration parameters into environment memory
    os.environ["AUTOCODE_PROVIDER"] = settings_data["provider"]
    os.environ["AUTOCODE_MODEL"] = settings_data["model"]
    
    # Map the general key to the provider's standard environment variable convention
    env_var_name = f"{settings_data['provider'].upper()}_API_KEY"
    os.environ[env_var_name] = settings_data["api_key"]
    
    # Evict cached agent instance to build a fresh graph using the updated configuration
    reset_agent()
