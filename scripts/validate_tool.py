#!/usr/bin/env python3
"""
Tool validation framework for automagik-tools

Validates MCP tool compliance, security, and performance.

Usage: python scripts/validate_tool.py <tool-name>
"""

import sys
import asyncio
import importlib
import importlib.metadata
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from fastmcp import FastMCP

console = Console()
app = typer.Typer()


class ValidationStatus(Enum):
    PASSED = "✅ PASSED"
    FAILED = "❌ FAILED"
    WARNING = "⚠️ WARNING"
    SKIPPED = "⏭️ SKIPPED"


@dataclass
class ValidationResult:
    """Result of a single validation check"""
    name: str
    status: ValidationStatus
    message: str
    details: Optional[str] = None


@dataclass
class ToolValidationReport:
    """Complete validation report for a tool"""
    tool_name: str
    overall_status: ValidationStatus
    mcp_compliance: List[ValidationResult] = field(default_factory=list)
    security_checks: List[ValidationResult] = field(default_factory=list)
    performance_checks: List[ValidationResult] = field(default_factory=list)
    openapi_validation: List[ValidationResult] = field(default_factory=list)


def discover_tool(tool_name: str) -> Optional[Any]:
    """Discover a tool by name from entry points"""
    try:
        entry_points = importlib.metadata.entry_points()
        if hasattr(entry_points, 'select'):
            # Python 3.10+
            tool_entry_points = entry_points.select(group='automagik_tools.plugins')
        else:
            # Python 3.9 and earlier
            tool_entry_points = entry_points.get('automagik_tools.plugins', [])
        
        for ep in tool_entry_points:
            if ep.name == tool_name:
                module_name = ep.value.split(':')[0]
                return importlib.import_module(module_name)
    except Exception as e:
        console.print(f"[red]Error discovering tool: {e}[/red]")
    
    return None


def validate_tool_structure(tool_module: Any) -> List[ValidationResult]:
    """Validate basic tool structure and required functions"""
    results = []
    
    # Check for required functions
    required_functions = [
        ('get_metadata', 'Returns tool metadata'),
        ('get_config_class', 'Returns configuration class'),
        ('create_server', 'Creates FastMCP server instance')
    ]
    
    for func_name, description in required_functions:
        if hasattr(tool_module, func_name):
            results.append(ValidationResult(
                name=f"{func_name} function",
                status=ValidationStatus.PASSED,
                message=f"Tool exports {func_name}",
                details=description
            ))
        else:
            # Check for legacy create_tool function
            if func_name == 'create_server' and hasattr(tool_module, 'create_tool'):
                results.append(ValidationResult(
                    name=f"{func_name} function",
                    status=ValidationStatus.WARNING,
                    message=f"Tool uses legacy 'create_tool' instead of 'create_server'",
                    details="Consider updating to 'create_server' for consistency"
                ))
            else:
                results.append(ValidationResult(
                    name=f"{func_name} function",
                    status=ValidationStatus.FAILED,
                    message=f"Tool missing required function: {func_name}",
                    details=description
                ))
    
    return results


def validate_mcp_compliance(tool_module: Any) -> List[ValidationResult]:
    """Validate MCP protocol compliance"""
    results = []
    
    try:
        # Get metadata
        if hasattr(tool_module, 'get_metadata'):
            metadata = tool_module.get_metadata()
            
            # Check metadata fields
            required_fields = ['name', 'version', 'description']
            for field in required_fields:
                if field in metadata:
                    results.append(ValidationResult(
                        name=f"Metadata field: {field}",
                        status=ValidationStatus.PASSED,
                        message=f"Has {field}: {metadata[field]}"
                    ))
                else:
                    results.append(ValidationResult(
                        name=f"Metadata field: {field}",
                        status=ValidationStatus.WARNING,
                        message=f"Missing recommended metadata field: {field}"
                    ))
        
        # Try to create server instance
        if hasattr(tool_module, 'get_config_class') and hasattr(tool_module, 'create_server'):
            try:
                config_class = tool_module.get_config_class()
                config = config_class()
                server = tool_module.create_server(config)
                
                if isinstance(server, FastMCP):
                    results.append(ValidationResult(
                        name="FastMCP instance",
                        status=ValidationStatus.PASSED,
                        message="Tool creates valid FastMCP server instance"
                    ))
                    
                    # Check for tools
                    if hasattr(server, '_tool_manager') and server._tool_manager._tools:
                        tool_count = len(server._tool_manager._tools)
                        results.append(ValidationResult(
                            name="MCP tools",
                            status=ValidationStatus.PASSED,
                            message=f"Tool exposes {tool_count} MCP tool(s)"
                        ))
                    else:
                        results.append(ValidationResult(
                            name="MCP tools",
                            status=ValidationStatus.WARNING,
                            message="No MCP tools found in server"
                        ))
                        
                else:
                    results.append(ValidationResult(
                        name="FastMCP instance",
                        status=ValidationStatus.FAILED,
                        message="Tool does not return FastMCP instance"
                    ))
                    
            except Exception as e:
                results.append(ValidationResult(
                    name="Server creation",
                    status=ValidationStatus.WARNING,
                    message="Could not create server instance",
                    details=f"This may be due to missing environment variables: {str(e)}"
                ))
    
    except Exception as e:
        results.append(ValidationResult(
            name="MCP compliance check",
            status=ValidationStatus.FAILED,
            message=f"Error during MCP validation: {str(e)}"
        ))
    
    return results


def validate_security(tool_module: Any) -> List[ValidationResult]:
    """Validate security best practices"""
    results = []
    
    # Check configuration handling
    if hasattr(tool_module, 'get_config_class'):
        try:
            config_class = tool_module.get_config_class()
            
            # Check for sensitive field handling
            if hasattr(config_class, 'model_fields'):
                for field_name, field_info in config_class.model_fields.items():
                    if 'key' in field_name.lower() or 'token' in field_name.lower() or 'secret' in field_name.lower():
                        # Check if field is marked as secret
                        if hasattr(field_info, 'json_schema_extra') and field_info.json_schema_extra.get('secret'):
                            results.append(ValidationResult(
                                name=f"Sensitive field: {field_name}",
                                status=ValidationStatus.PASSED,
                                message=f"Field {field_name} properly marked as secret"
                            ))
                        else:
                            results.append(ValidationResult(
                                name=f"Sensitive field: {field_name}",
                                status=ValidationStatus.WARNING,
                                message=f"Field {field_name} may contain sensitive data but not marked as secret"
                            ))
            
            # Check for environment variable usage
            if hasattr(config_class, 'model_config') and hasattr(config_class.model_config, 'env_prefix'):
                results.append(ValidationResult(
                    name="Environment variables",
                    status=ValidationStatus.PASSED,
                    message=f"Uses environment prefix: {config_class.model_config.env_prefix}"
                ))
            else:
                results.append(ValidationResult(
                    name="Environment variables",
                    status=ValidationStatus.WARNING,
                    message="No environment variable prefix configured"
                ))
                
        except Exception as e:
            results.append(ValidationResult(
                name="Configuration security",
                status=ValidationStatus.WARNING,
                message="Could not validate configuration security",
                details=str(e)
            ))
    
    return results


def validate_performance(tool_module: Any) -> List[ValidationResult]:
    """Basic performance checks"""
    results = []
    
    # Check for async support
    if hasattr(tool_module, 'create_server'):
        results.append(ValidationResult(
            name="Async support",
            status=ValidationStatus.PASSED,
            message="Tool uses FastMCP which supports async operations"
        ))
    
    # Check for timeout configuration
    if hasattr(tool_module, 'get_config_class'):
        try:
            config_class = tool_module.get_config_class()
            if hasattr(config_class, 'model_fields') and 'timeout' in config_class.model_fields:
                results.append(ValidationResult(
                    name="Timeout configuration",
                    status=ValidationStatus.PASSED,
                    message="Tool supports timeout configuration"
                ))
            else:
                results.append(ValidationResult(
                    name="Timeout configuration",
                    status=ValidationStatus.WARNING,
                    message="No timeout configuration found"
                ))
        except:
            pass
    
    return results


def validate_openapi(tool_module: Any) -> List[ValidationResult]:
    """Validate OpenAPI-specific features if applicable"""
    results = []
    
    # Check if this is an OpenAPI-based tool
    if hasattr(tool_module, 'get_metadata'):
        metadata = tool_module.get_metadata()
        if metadata.get('category') == 'openapi' or 'openapi' in metadata.get('tags', []):
            results.append(ValidationResult(
                name="OpenAPI tool",
                status=ValidationStatus.PASSED,
                message="Tool is marked as OpenAPI-based"
            ))
            
            # Check for OpenAPI URL configuration
            if hasattr(tool_module, 'get_config_class'):
                try:
                    config_class = tool_module.get_config_class()
                    if hasattr(config_class, 'model_fields') and 'openapi_url' in config_class.model_fields:
                        results.append(ValidationResult(
                            name="OpenAPI URL config",
                            status=ValidationStatus.PASSED,
                            message="Tool has OpenAPI URL configuration"
                        ))
                except:
                    pass
    
    return results


def generate_report(report: ToolValidationReport) -> None:
    """Generate and display the validation report"""
    # Create summary panel
    summary_color = "green" if report.overall_status == ValidationStatus.PASSED else "red"
    console.print(Panel(
        f"[bold {summary_color}]Tool Validation Report: {report.tool_name}[/bold {summary_color}]\n"
        f"Overall Status: {report.overall_status.value}",
        title="Validation Summary"
    ))
    
    # Create results table
    sections = [
        ("MCP Compliance", report.mcp_compliance),
        ("Security Checks", report.security_checks),
        ("Performance Checks", report.performance_checks),
        ("OpenAPI Validation", report.openapi_validation)
    ]
    
    for section_name, results in sections:
        if results:
            console.print(f"\n[bold cyan]{section_name}[/bold cyan]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Check", style="cyan", width=30)
            table.add_column("Status", width=12)
            table.add_column("Message", style="white")
            
            for result in results:
                status_style = {
                    ValidationStatus.PASSED: "green",
                    ValidationStatus.FAILED: "red",
                    ValidationStatus.WARNING: "yellow",
                    ValidationStatus.SKIPPED: "gray"
                }.get(result.status, "white")
                
                table.add_row(
                    result.name,
                    f"[{status_style}]{result.status.value}[/{status_style}]",
                    result.message
                )
                
                if result.details:
                    table.add_row("", "", f"[dim]{result.details}[/dim]")
            
            console.print(table)
    
    # Print summary statistics
    all_results = (
        report.mcp_compliance + 
        report.security_checks + 
        report.performance_checks + 
        report.openapi_validation
    )
    
    passed = sum(1 for r in all_results if r.status == ValidationStatus.PASSED)
    failed = sum(1 for r in all_results if r.status == ValidationStatus.FAILED)
    warnings = sum(1 for r in all_results if r.status == ValidationStatus.WARNING)
    
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Total checks: {len(all_results)}")
    console.print(f"  [green]Passed: {passed}[/green]")
    console.print(f"  [red]Failed: {failed}[/red]")
    console.print(f"  [yellow]Warnings: {warnings}[/yellow]")


@app.command()
def validate(tool_name: str):
    """Validate a specific tool for MCP compliance"""
    console.print(f"[blue]Validating tool: {tool_name}[/blue]\n")
    
    # Discover the tool
    tool_module = discover_tool(tool_name)
    if not tool_module:
        console.print(f"[red]Tool '{tool_name}' not found![/red]")
        console.print("[yellow]Make sure the tool is installed and registered in pyproject.toml[/yellow]")
        sys.exit(1)
    
    # Create validation report
    report = ToolValidationReport(tool_name=tool_name, overall_status=ValidationStatus.PASSED)
    
    # Run validations
    console.print("[cyan]Running validation checks...[/cyan]\n")
    
    # Structure validation
    structure_results = validate_tool_structure(tool_module)
    report.mcp_compliance.extend(structure_results)
    
    # MCP compliance
    mcp_results = validate_mcp_compliance(tool_module)
    report.mcp_compliance.extend(mcp_results)
    
    # Security checks
    security_results = validate_security(tool_module)
    report.security_checks.extend(security_results)
    
    # Performance checks
    performance_results = validate_performance(tool_module)
    report.performance_checks.extend(performance_results)
    
    # OpenAPI validation
    openapi_results = validate_openapi(tool_module)
    report.openapi_validation.extend(openapi_results)
    
    # Determine overall status
    all_results = (
        report.mcp_compliance + 
        report.security_checks + 
        report.performance_checks + 
        report.openapi_validation
    )
    
    if any(r.status == ValidationStatus.FAILED for r in all_results):
        report.overall_status = ValidationStatus.FAILED
    elif any(r.status == ValidationStatus.WARNING for r in all_results):
        report.overall_status = ValidationStatus.WARNING
    
    # Generate report
    generate_report(report)
    
    # Exit with appropriate code
    if report.overall_status == ValidationStatus.FAILED:
        sys.exit(1)
    elif report.overall_status == ValidationStatus.WARNING:
        sys.exit(0)  # Warnings don't fail the validation
    else:
        sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        console.print("[red]Usage: python scripts/validate_tool.py <tool-name>[/red]")
        sys.exit(1)
    
    tool_name = sys.argv[1]
    validate(tool_name)