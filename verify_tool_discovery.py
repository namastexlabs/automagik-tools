#!/usr/bin/env python3
"""
Verify that all tools in ecosystem.config.cjs can be discovered and imported.
"""

import sys
import importlib
from pathlib import Path

# Tools configured in ecosystem.config.cjs (11k series)
ECOSYSTEM_TOOLS = {
    "namastex_oauth_server": {"port": 11000, "category": "OAuth"},
    "google_calendar_test": {"port": 11001, "category": "OAuth"},
    "google_calendar": {"port": 11002, "category": "Google Workspace"},
    "google_gmail": {"port": 11003, "category": "Google Workspace"},
    "google_drive": {"port": 11004, "category": "Google Workspace"},
    "google_docs": {"port": 11005, "category": "Google Workspace"},
    "google_sheets": {"port": 11006, "category": "Google Workspace"},
    "google_slides": {"port": 11007, "category": "Google Workspace"},
    "google_forms": {"port": 11008, "category": "Google Workspace"},
    "google_tasks": {"port": 11009, "category": "Google Workspace"},
    "google_chat": {"port": 11010, "category": "Google Workspace"},
    "google_workspace": {"port": 11011, "category": "Google Workspace"},
    "genie_omni": {"port": 11012, "category": "Genie & Messaging"},
    "evolution_api": {"port": 11013, "category": "Genie & Messaging"},
    "omni": {"port": 11014, "category": "Genie & Messaging"},
    "openapi": {"port": 11021, "category": "Universal Tools"},
    "wait": {"port": 11022, "category": "Universal Tools"},
    "json_to_google_docs": {"port": 11023, "category": "Universal Tools"},
    "genie_tool": {"port": 11031, "category": "Agent Tools"},
    "gemini_assistant": {"port": 11032, "category": "Agent Tools"},
    "spark": {"port": 11041, "category": "Experimental"},
    # "hive": {"port": 11042, "category": "Experimental"},  # Commented out in ecosystem
}


def check_tool(tool_name: str, tool_info: dict) -> dict:
    """Check if a tool can be discovered and imported."""
    result = {
        "name": tool_name,
        "port": tool_info["port"],
        "category": tool_info["category"],
        "directory_exists": False,
        "init_exists": False,
        "importable": False,
        "has_create_server": False,
        "has_get_metadata": False,
        "has_not_a_tool_flag": False,
        "error": None,
    }

    # Check directory exists
    tools_dir = Path(__file__).parent / "automagik_tools" / "tools"
    tool_dir = tools_dir / tool_name
    result["directory_exists"] = tool_dir.exists()

    if not result["directory_exists"]:
        result["error"] = f"Directory not found: {tool_dir}"
        return result

    # Check __init__.py exists
    init_file = tool_dir / "__init__.py"
    result["init_exists"] = init_file.exists()

    if not result["init_exists"]:
        result["error"] = f"__init__.py not found in {tool_dir}"
        return result

    # Try to import
    module_name = f"automagik_tools.tools.{tool_name}"
    try:
        module = importlib.import_module(module_name)
        result["importable"] = True

        # Check for __AUTOMAGIK_NOT_A_TOOL__ flag
        result["has_not_a_tool_flag"] = getattr(
            module, "__AUTOMAGIK_NOT_A_TOOL__", False
        )

        # Check for required functions
        result["has_create_server"] = hasattr(module, "create_server")
        result["has_get_metadata"] = hasattr(module, "get_metadata")

        if result["has_not_a_tool_flag"]:
            result["error"] = "Tool is marked with __AUTOMAGIK_NOT_A_TOOL__"
        elif not result["has_create_server"]:
            result["error"] = "Missing create_server() function"
        elif not result["has_get_metadata"]:
            result["error"] = "Missing get_metadata() function"

    except Exception as e:
        result["error"] = f"Import failed: {str(e)}"

    return result


def main():
    """Run verification on all ecosystem tools."""
    print("=" * 80)
    print("TOOL DISCOVERY VERIFICATION")
    print("=" * 80)
    print()

    results = []
    for tool_name, tool_info in ECOSYSTEM_TOOLS.items():
        print(f"Checking {tool_name}...", end=" ")
        result = check_tool(tool_name, tool_info)
        results.append(result)

        if result["error"]:
            print(f"❌ FAILED: {result['error']}")
        else:
            print("✅ OK")

    # Summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()

    by_category = {}
    for result in results:
        category = result["category"]
        if category not in by_category:
            by_category[category] = {"total": 0, "passed": 0, "failed": 0}
        by_category[category]["total"] += 1
        if result["error"]:
            by_category[category]["failed"] += 1
        else:
            by_category[category]["passed"] += 1

    for category, stats in sorted(by_category.items()):
        status = "✅" if stats["failed"] == 0 else "⚠️"
        print(
            f"{status} {category}: {stats['passed']}/{stats['total']} passed, {stats['failed']} failed"
        )

    # Detailed failures
    failures = [r for r in results if r["error"]]
    if failures:
        print()
        print("=" * 80)
        print("FAILED TOOLS")
        print("=" * 80)
        print()
        for result in failures:
            print(f"❌ {result['name']} (port {result['port']})")
            print(f"   Category: {result['category']}")
            print(f"   Error: {result['error']}")
            print()

    # Exit code
    total_failed = sum(1 for r in results if r["error"])
    if total_failed > 0:
        print(f"⚠️  {total_failed} tools failed verification")
        return 1
    else:
        print("✅ All tools passed verification!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
