
import os
import sys
import google.generativeai as genai
from rich.console import Console
from rich.table import Table

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import config
    api_key = getattr(config, "GOOGLE_API_KEY", None)
except ImportError:
    api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("Error: GOOGLE_API_KEY not found in config.py or environment variables.")
    sys.exit(1)

genai.configure(api_key=api_key)

console = Console()

def check_limits():
    console.print("[bold blue]Checking Gemini Model Limits...[/bold blue]")
    
    table = Table(title="Available Gemini Models & Limits")
    table.add_column("Model Name", style="cyan")
    table.add_column("Input Limit", style="green")
    table.add_column("Output Limit", style="green")
    table.add_column("Description", style="white")

    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                table.add_row(
                    m.name,
                    str(m.input_token_limit),
                    str(m.output_token_limit),
                    m.description
                )
        
        console.print(table)
        
        console.print("\n[bold yellow]Note:[/bold yellow] Real-time rate limits (RPM, RPD) are not available via the API and must be checked in the Google AI Studio console.")

    except Exception as e:
        console.print(f"[bold red]Error querying models:[/bold red] {e}")

if __name__ == "__main__":
    check_limits()
