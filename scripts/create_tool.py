#!/usr/bin/env python3
"""
Tool creation script for automagik-tools

Usage: python scripts/create_tool.py --name "My Tool" --description "Tool description"
"""

import os
import shutil
import re
from pathlib import Path
import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm

console = Console()
app = typer.Typer()


def to_snake_case(name: str) -> str:
    """Convert a name to snake_case"""
    # Replace spaces and hyphens with underscores
    name = re.sub(r'[\s\-]+', '_', name)
    # Insert underscore before uppercase letters
    name = re.sub(r'(?<!^)(?=[A-Z])', '_', name)
    return name.lower()


def to_class_case(name: str) -> str:
    """Convert a name to ClassCase"""
    # Split by spaces, hyphens, or underscores
    parts = re.split(r'[\s\-_]+', name)
    # Capitalize each part
    return ''.join(word.capitalize() for word in parts)


def to_kebab_case(name: str) -> str:
    """Convert a name to kebab-case"""
    # Replace spaces and underscores with hyphens
    name = re.sub(r'[\s_]+', '-', name)
    # Insert hyphen before uppercase letters
    name = re.sub(r'(?<!^)(?=[A-Z])', '-', name)
    return name.lower()


@app.command()
def create(
    name: str = typer.Option(None, "--name", "-n", help="Tool name (e.g., 'GitHub API')"),
    description: str = typer.Option(None, "--description", "-d", help="Tool description"),
    interactive: bool = typer.Option(True, "--interactive/--no-interactive", "-i/-I", help="Interactive mode")
):
    """Create a new tool from template"""
    
    # Interactive mode
    if interactive and not name:
        name = Prompt.ask("[cyan]Tool name (e.g., 'GitHub API')[/cyan]")
    
    if not name:
        console.print("[red]Tool name is required![/red]")
        raise typer.Exit(1)
    
    if interactive and not description:
        description = Prompt.ask(
            "[cyan]Tool description[/cyan]",
            default=f"MCP tool for {name} integration"
        )
    
    if not description:
        description = f"MCP tool for {name} integration"
    
    # Generate variations of the name
    tool_name = name
    tool_name_lower = to_snake_case(name)
    tool_name_kebab = to_kebab_case(name)
    tool_name_class = to_class_case(name)
    tool_name_upper = tool_name_lower.upper()
    
    console.print(f"\n[green]Creating tool:[/green] {tool_name}")
    console.print(f"[dim]Snake case:[/dim] {tool_name_lower}")
    console.print(f"[dim]Kebab case:[/dim] {tool_name_kebab}")
    console.print(f"[dim]Class case:[/dim] {tool_name_class}")
    console.print(f"[dim]Upper case:[/dim] {tool_name_upper}\n")
    
    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    template_dir = project_root / "templates" / "tool_template"
    target_dir = project_root / "automagik_tools" / "tools" / tool_name_lower
    test_file = project_root / "tests" / "tools" / f"test_{tool_name_lower}.py"
    
    # Check if tool already exists
    if target_dir.exists():
        if not Confirm.ask(f"[yellow]Tool '{tool_name_lower}' already exists. Overwrite?[/yellow]"):
            console.print("[yellow]Aborted.[/yellow]")
            raise typer.Exit(0)
        shutil.rmtree(target_dir)
    
    # Create tool directory
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy and process template files
    replacements = {
        "{TOOL_NAME}": tool_name,
        "{TOOL_NAME_LOWER}": tool_name_lower,
        "{TOOL_NAME_UPPER}": tool_name_upper,
        "{TOOL_NAME_CLASS}": tool_name_class,
        "{TOOL_NAME_KEBAB}": tool_name_kebab,
        "{TOOL_DESCRIPTION}": description,
    }
    
    # Copy main files
    for template_file in ["__init__.py", "config.py", "README.md"]:
        if (template_dir / template_file).exists():
            with open(template_dir / template_file, "r") as f:
                content = f.read()
            
            # Replace placeholders
            for old, new in replacements.items():
                content = content.replace(old, new)
            
            target_file = target_dir / template_file
            with open(target_file, "w") as f:
                f.write(content)
            
            console.print(f"[green]✓[/green] Created {target_file.relative_to(project_root)}")
    
    # Copy test file
    if (template_dir / "test_template.py").exists():
        with open(template_dir / "test_template.py", "r") as f:
            content = f.read()
        
        # Replace placeholders
        for old, new in replacements.items():
            content = content.replace(old, new)
        
        test_file.parent.mkdir(parents=True, exist_ok=True)
        with open(test_file, "w") as f:
            f.write(content)
        
        console.print(f"[green]✓[/green] Created {test_file.relative_to(project_root)}")
    
    # No need to update pyproject.toml - tools are auto-discovered!
    
    # Update CLI config
    cli_path = project_root / "automagik_tools" / "cli.py"
    console.print(f"\n[yellow]Note:[/yellow] Add configuration class to {cli_path.relative_to(project_root)}:")
    console.print(f"\n[dim]from automagik_tools.tools.{tool_name_lower}.config import {tool_name_class}Config[/dim]")
    console.print(f"\n[dim]In create_config_for_tool():[/dim]")
    console.print(f"[dim]    elif tool_name == '{tool_name_kebab}':[/dim]")
    console.print(f"[dim]        return {tool_name_class}Config()[/dim]")
    
    # Update .env.example
    console.print(f"\n[yellow]Note:[/yellow] Add configuration to .env.example:")
    console.print(f"\n[dim]# {tool_name} Configuration[/dim]")
    console.print(f"[dim]{tool_name_upper}_API_KEY=your-api-key-here[/dim]")
    console.print(f"[dim]{tool_name_upper}_BASE_URL=https://api.example.com[/dim]")
    console.print(f"[dim]{tool_name_upper}_TIMEOUT=30[/dim]")
    
    console.print(f"\n[green]✨ Tool '{tool_name}' created successfully![/green]")
    console.print(f"\nNext steps:")
    console.print(f"1. Implement your tool logic in {target_dir / '__init__.py'}")
    console.print(f"2. Update the configuration class in {cli_path.name}")
    console.print(f"3. Add your configuration to .env.example")
    console.print(f"4. Run tests: [dim]pytest {test_file.relative_to(project_root)} -v[/dim]")
    console.print(f"5. Test your tool: [dim]automagik-tools serve {tool_name_kebab}[/dim]")


if __name__ == "__main__":
    app()