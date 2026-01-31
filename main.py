"""Main CLI entry point for the multi-agent system."""

import argparse
import asyncio
import sys
import uuid

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from config import settings
from core.orchestrator import Orchestrator
from utils.logging_config import setup_logging
from utils.validators import Validators

console = Console()


async def interactive_mode(orchestrator: Orchestrator) -> None:
    """Run in interactive mode.

    Args:
        orchestrator: Orchestrator instance
    """
    session_id = str(uuid.uuid4())[:8]

    console.print(Panel.fit(
        "[bold cyan]Multi-Agent Development Assistant[/bold cyan]\n\n"
        "Available agents: coder, test_writer, requirement_analyzer, qa_checker, docs_agent\n"
        "Type 'exit' or 'quit' to end the session.",
        title="Welcome"
    ))

    console.print(f"\n[dim]Session ID: {session_id}[/dim]\n")

    while True:
        try:
            # Get user input
            user_input = console.input("[bold green]You:[/bold green] ").strip()

            if not user_input:
                continue

            # Check for exit commands
            if user_input.lower() in ['exit', 'quit', 'q']:
                console.print("\n[yellow]Goodbye![/yellow]")
                break

            # Process request
            console.print("\n[cyan]Processing...[/cyan]\n")
            response = await orchestrator.process_request(user_input, session_id)

            # Display response
            console.print(Panel(
                Markdown(response),
                title="[bold blue]Assistant[/bold blue]",
                border_style="blue"
            ))
            console.print()

        except KeyboardInterrupt:
            console.print("\n\n[yellow]Session interrupted. Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"\n[red]Error: {str(e)}[/red]\n")


async def single_query_mode(orchestrator: Orchestrator, query: str) -> None:
    """Process a single query and exit.

    Args:
        orchestrator: Orchestrator instance
        query: User query
    """
    session_id = str(uuid.uuid4())[:8]

    console.print(f"\n[cyan]Processing query...[/cyan]\n")
    response = await orchestrator.process_request(query, session_id)

    # Display response
    console.print(Panel(
        Markdown(response),
        title="[bold blue]Response[/bold blue]",
        border_style="blue"
    ))
    console.print()


async def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Development Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python main.py

  # Single query
  python main.py -q "Write a function to calculate factorial"

  # Specify session
  python main.py -s my-session -q "Continue from previous context"
        """
    )

    parser.add_argument(
        "-q", "--query",
        type=str,
        help="Single query to process (non-interactive mode)"
    )

    parser.add_argument(
        "-s", "--session",
        type=str,
        help="Session ID to use/resume"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    parser.add_argument(
        "--list-agents",
        action="store_true",
        help="List available agents and exit"
    )

    args = parser.parse_args()

    # Override log level if verbose
    if args.verbose:
        settings.log_level = "DEBUG"

    # Setup logging with configuration
    setup_logging(
        use_rich_console=settings.log_use_rich_console,
        enable_rotation=settings.log_rotation_enabled,
        max_bytes=settings.log_max_bytes,
        backup_count=settings.log_backup_count
    )

    # Initialize orchestrator
    try:
        console.print(settings.model_dump(mode="json"))
        console.print("[cyan]Initializing multi-agent system...[/cyan]")
        orchestrator = Orchestrator()
        await orchestrator.initialize()
        console.print("[green]✓ System ready[/green]\n")

    except Exception as e:
        console.print(f"[red]Failed to initialize: {str(e)}[/red]")
        console.print("\n[yellow]Please check:[/yellow]")
        console.print("  1. ANTHROPIC_API_KEY is set in .env file")
        console.print("  2. All dependencies are installed (pip install -r requirements.txt)")
        console.print("  3. Configuration is valid")
        sys.exit(1)

    try:
        # List agents mode
        if args.list_agents:
            agents = orchestrator.agent_registry.list_agents()
            console.print(Panel(
                "\n".join([
                    f"[bold]{name}[/bold]: {', '.join(caps)}"
                    for name, caps in agents.items()
                ]),
                title="Available Agents"
            ))
            return

        # Single query mode
        if args.query:
            query = Validators.sanitize_input(args.query)
            await single_query_mode(orchestrator, query)

        # Interactive mode
        else:
            await interactive_mode(orchestrator)

    finally:
        # Cleanup
        await orchestrator.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
        sys.exit(0)
