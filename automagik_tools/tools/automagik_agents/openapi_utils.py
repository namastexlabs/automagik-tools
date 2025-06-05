"""
OpenAPI utilities for automagik_agents

This module provides utilities for working with OpenAPI specifications
and preventing naming issues in MCP integrations.
"""

import re
import httpx
from typing import Dict, List, Tuple, Any, Optional


def analyze_openapi_names(openapi_spec: Dict[str, Any], max_length: int = 56) -> Dict[str, Any]:
    """
    Analyze OpenAPI specification for naming issues.
    
    Args:
        openapi_spec: The OpenAPI specification dictionary
        max_length: Maximum allowed component name length
        
    Returns:
        Dictionary with analysis results
    """
    results = {
        "total_operations": 0,
        "long_names": [],
        "suggested_mappings": {},
        "name_conflicts": [],
        "statistics": {
            "avg_length": 0,
            "max_length_found": 0,
            "min_length_found": float('inf')
        }
    }
    
    operation_ids = []
    
    for path, path_item in openapi_spec.get("paths", {}).items():
        for method, operation in path_item.items():
            if method.lower() in ["get", "post", "put", "delete", "patch", "options", "head"]:
                operation_id = operation.get("operationId")
                if operation_id:
                    results["total_operations"] += 1
                    operation_ids.append(operation_id)
                    
                    length = len(operation_id)
                    results["statistics"]["max_length_found"] = max(results["statistics"]["max_length_found"], length)
                    results["statistics"]["min_length_found"] = min(results["statistics"]["min_length_found"], length)
                    
                    if length > max_length:
                        suggested_name = suggest_short_name(operation_id, path, method)
                        results["long_names"].append({
                            "operation_id": operation_id,
                            "length": length,
                            "path": path,
                            "method": method.upper(),
                            "suggested_name": suggested_name
                        })
                        results["suggested_mappings"][operation_id] = suggested_name
    
    if operation_ids:
        results["statistics"]["avg_length"] = sum(len(op_id) for op_id in operation_ids) / len(operation_ids)
    
    # Check for name conflicts in suggested names
    suggested_names = list(results["suggested_mappings"].values())
    name_counts = {}
    for name in suggested_names:
        name_counts[name] = name_counts.get(name, 0) + 1
    
    results["name_conflicts"] = [name for name, count in name_counts.items() if count > 1]
    
    return results


def suggest_short_name(operation_id: str, path: str, method: str) -> str:
    """
    Suggest a shorter, meaningful name for a long operationId.
    
    Args:
        operation_id: The original operationId
        path: The API path
        method: The HTTP method
        
    Returns:
        Suggested shorter name
    """
    name = operation_id
    
    # Remove common API prefixes and suffixes
    prefixes_to_remove = [
        "api_v1_", "api_v2_", "api_", 
        "endpoint_", "route_", "_endpoint", "_route"
    ]
    
    suffixes_to_remove = [
        "_get", "_post", "_put", "_delete", "_patch", "_head", "_options"
    ]
    
    # Remove prefixes
    for prefix in prefixes_to_remove:
        if name.startswith(prefix):
            name = name[len(prefix):]
            break
    
    # Remove suffixes
    for suffix in suffixes_to_remove:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
            break
    
    # Extract meaningful part before first double underscore (path parameters)
    name = name.split("__")[0]
    
    # Clean up common patterns to make names more natural
    replacements = {
        "_api_v1_": "_",
        "_api_": "_",
        "mcp_servers": "server",
        "mcp_agents": "agent", 
        "claude_code": "workflow",
        "session_route": "session",
        "memory_endpoint": "memory",
    }
    
    for old, new in replacements.items():
        name = name.replace(old, new)
    
    # Remove duplicate underscores
    while "__" in name:
        name = name.replace("__", "_")
    
    # Remove leading/trailing underscores
    name = name.strip("_")
    
    # Extract meaningful parts for intelligent shortening
    parts = name.split('_')
    
    # Common action words and resources
    action_words = ['get', 'list', 'create', 'update', 'delete', 'run', 'start', 'stop', 'restart', 'approve', 'activate', 'deactivate']
    resource_words = ['agent', 'user', 'session', 'memory', 'prompt', 'workflow', 'server', 'epic', 'step']
    
    # Try to identify action and resource
    action = None
    resource = None
    
    for part in parts:
        if part in action_words and not action:
            action = part
        elif part in resource_words and not resource:
            resource = part
    
    # Build suggested name intelligently
    if action and resource:
        suggested = f"{action}_{resource}"
    elif action:
        # Look for a meaningful noun after the action
        action_index = parts.index(action)
        if action_index + 1 < len(parts):
            next_part = parts[action_index + 1]
            if len(next_part) > 2:  # Meaningful word
                suggested = f"{action}_{next_part}"
            else:
                suggested = action
        else:
            suggested = action
    elif resource:
        # Look for a meaningful verb before the resource
        resource_index = parts.index(resource)
        if resource_index > 0:
            prev_part = parts[resource_index - 1]
            if len(prev_part) > 2:  # Meaningful word
                suggested = f"{prev_part}_{resource}"
            else:
                suggested = resource
        else:
            suggested = resource
    else:
        # Fallback: take first few meaningful parts
        meaningful_parts = [p for p in parts if len(p) > 2 and p not in ['api', 'v1', 'v2']]
        suggested = '_'.join(meaningful_parts[:2]) if meaningful_parts else parts[0] if parts else "operation"
    
    # Ensure it's not too long
    if len(suggested) > 50:
        suggested = suggested[:50]
    
    return suggested


def generate_mcp_names_mapping(openapi_url: str, max_length: int = 56) -> Dict[str, str]:
    """
    Generate MCP names mapping for a given OpenAPI URL.
    
    Args:
        openapi_url: URL to fetch OpenAPI specification
        max_length: Maximum allowed component name length
        
    Returns:
        Dictionary mapping operationId to suggested short names
    """
    try:
        response = httpx.get(openapi_url, timeout=30)
        response.raise_for_status()
        openapi_spec = response.json()
        
        analysis = analyze_openapi_names(openapi_spec, max_length)
        return analysis["suggested_mappings"]
        
    except Exception as e:
        print(f"Error fetching OpenAPI spec from {openapi_url}: {e}")
        return {}


def validate_mcp_names(names_mapping: Dict[str, str], max_length: int = 56) -> Tuple[bool, List[str]]:
    """
    Validate that all names in the mapping are within the length limit.
    
    Args:
        names_mapping: Dictionary of operationId -> name mappings
        max_length: Maximum allowed length
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    for operation_id, name in names_mapping.items():
        if len(name) > max_length:
            issues.append(f"Name '{name}' ({len(name)} chars) exceeds limit ({max_length} chars)")
    
    # Check for duplicates
    name_counts = {}
    for name in names_mapping.values():
        name_counts[name] = name_counts.get(name, 0) + 1
    
    duplicates = [name for name, count in name_counts.items() if count > 1]
    for duplicate in duplicates:
        issues.append(f"Duplicate name '{duplicate}' found")
    
    return len(issues) == 0, issues


def print_analysis_report(openapi_url: str, max_length: int = 56):
    """
    Print a detailed analysis report for an OpenAPI specification.
    
    Args:
        openapi_url: URL to fetch OpenAPI specification
        max_length: Maximum allowed component name length
    """
    try:
        response = httpx.get(openapi_url, timeout=30)
        response.raise_for_status()
        openapi_spec = response.json()
        
        analysis = analyze_openapi_names(openapi_spec, max_length)
        
        print(f"\n=== OpenAPI Naming Analysis Report ===")
        print(f"URL: {openapi_url}")
        print(f"Max allowed length: {max_length} characters")
        print(f"\nStatistics:")
        print(f"  Total operations: {analysis['total_operations']}")
        print(f"  Average name length: {analysis['statistics']['avg_length']:.1f}")
        print(f"  Longest name: {analysis['statistics']['max_length_found']} chars")
        print(f"  Shortest name: {analysis['statistics']['min_length_found']} chars")
        
        if analysis['long_names']:
            print(f"\n⚠️  Found {len(analysis['long_names'])} names exceeding {max_length} characters:")
            for item in analysis['long_names']:
                print(f"  • {item['operation_id']} ({item['length']} chars)")
                print(f"    Path: {item['method']} {item['path']}")
                print(f"    Suggested: {item['suggested_name']}")
                print()
        else:
            print(f"\n✅ All operation names are within the {max_length} character limit!")
        
        if analysis['name_conflicts']:
            print(f"\n⚠️  Name conflicts found in suggestions:")
            for conflict in analysis['name_conflicts']:
                print(f"  • {conflict}")
        
        print(f"\n=== Suggested MCP Names Mapping ===")
        if analysis['suggested_mappings']:
            print("Add this to your get_custom_mcp_names() function:")
            print("{")
            for op_id, suggested in analysis['suggested_mappings'].items():
                print(f'    "{op_id}": "{suggested}",')
            print("}")
        else:
            print("No custom mappings needed - all names are within limits!")
            
    except Exception as e:
        print(f"Error analyzing OpenAPI spec: {e}")


if __name__ == "__main__":
    # Example usage
    openapi_url = "http://192.168.112.148:8881/api/v1/openapi.json"
    print_analysis_report(openapi_url) 