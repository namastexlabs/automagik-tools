#!/usr/bin/env python3
"""Fix FunctionTool callable issues in more test files"""

import re
import os

# Fix test_wait.py
if os.path.exists('tests/tools/test_wait.py'):
    with open('tests/tools/test_wait.py', 'r') as f:
        content = f.read()
    
    # Replace wait_minutes calls
    content = re.sub(
        r'(from automagik_tools\.tools\.wait import .*wait_minutes.*\n)',
        r'\1        wait_minutes_fn = wait_minutes.fn if hasattr(wait_minutes, "fn") else wait_minutes\n',
        content
    )
    content = re.sub(
        r'(\s+)(result = await wait_minutes\()',
        r'\1result = await wait_minutes_fn(',
        content
    )
    content = re.sub(
        r'(\s+)(await wait_minutes\()',
        r'\1await wait_minutes_fn(',
        content
    )
    
    with open('tests/tools/test_wait.py', 'w') as f:
        f.write(content)

# Fix test_automagik_workflows_edge_cases.py
if os.path.exists('tests/tools/test_automagik_workflows_edge_cases.py'):
    with open('tests/tools/test_automagik_workflows_edge_cases.py', 'r') as f:
        content = f.read()
    
    # Add import extraction at the top
    import_section = """from automagik_tools.tools.automagik_workflows import (
    run_workflow as run_workflow_tool,
    list_recent_runs as list_recent_runs_tool,
    get_health_status as get_health_status_tool,
    list_runs_by_status as list_runs_by_status_tool,
    list_runs_by_workflow as list_runs_by_workflow_tool,
    list_runs_by_time_range as list_runs_by_time_range_tool,
)

# Extract actual functions from FunctionTool wrappers
run_workflow = run_workflow_tool.fn if hasattr(run_workflow_tool, 'fn') else run_workflow_tool
list_recent_runs = list_recent_runs_tool.fn if hasattr(list_recent_runs_tool, 'fn') else list_recent_runs_tool
get_health_status = get_health_status_tool.fn if hasattr(get_health_status_tool, 'fn') else get_health_status_tool
list_runs_by_status = list_runs_by_status_tool.fn if hasattr(list_runs_by_status_tool, 'fn') else list_runs_by_status_tool
list_runs_by_workflow = list_runs_by_workflow_tool.fn if hasattr(list_runs_by_workflow_tool, 'fn') else list_runs_by_workflow_tool
list_runs_by_time_range = list_runs_by_time_range_tool.fn if hasattr(list_runs_by_time_range_tool, 'fn') else list_runs_by_time_range_tool"""
    
    # Replace the imports
    content = re.sub(
        r'from automagik_tools\.tools\.automagik_workflows import \([^)]+\)',
        import_section,
        content,
        count=1
    )
    
    with open('tests/tools/test_automagik_workflows_edge_cases.py', 'w') as f:
        f.write(content)

# Fix test_automagik_workflows_enhanced.py
if os.path.exists('tests/tools/test_automagik_workflows_enhanced.py'):
    with open('tests/tools/test_automagik_workflows_enhanced.py', 'r') as f:
        content = f.read()
    
    # Add import extraction at the top
    import_section = """from automagik_tools.tools.automagik_workflows import (
    run_workflow as run_workflow_tool,
    list_recent_runs as list_recent_runs_tool,
    get_health_status as get_health_status_tool,
    list_runs_by_status as list_runs_by_status_tool,
    list_runs_by_workflow as list_runs_by_workflow_tool,
    list_runs_by_time_range as list_runs_by_time_range_tool,
)

# Extract actual functions from FunctionTool wrappers
run_workflow = run_workflow_tool.fn if hasattr(run_workflow_tool, 'fn') else run_workflow_tool
list_recent_runs = list_recent_runs_tool.fn if hasattr(list_recent_runs_tool, 'fn') else list_recent_runs_tool
get_health_status = get_health_status_tool.fn if hasattr(get_health_status_tool, 'fn') else get_health_status_tool
list_runs_by_status = list_runs_by_status_tool.fn if hasattr(list_runs_by_status_tool, 'fn') else list_runs_by_status_tool
list_runs_by_workflow = list_runs_by_workflow_tool.fn if hasattr(list_runs_by_workflow_tool, 'fn') else list_runs_by_workflow_tool
list_runs_by_time_range = list_runs_by_time_range_tool.fn if hasattr(list_runs_by_time_range_tool, 'fn') else list_runs_by_time_range_tool"""
    
    # Replace the imports
    content = re.sub(
        r'from automagik_tools\.tools\.automagik_workflows import \([^)]+\)',
        import_section,
        content,
        count=1
    )
    
    with open('tests/tools/test_automagik_workflows_enhanced.py', 'w') as f:
        f.write(content)

print("Fixed more test files")