#!/usr/bin/env python3
"""Fix FunctionTool callable issues in edge case test files"""

import re

# Fix test_omni_edge_cases.py
with open('tests/tools/test_omni_edge_cases.py', 'r') as f:
    content = f.read()

# First, add the imports at the top
if "from automagik_tools.tools.omni import" in content and "manage_instances" not in content:
    # Add imports after create_server import
    content = re.sub(
        r'(from automagik_tools.tools.omni import create_server)',
        r'\1, manage_instances, send_message, manage_traces',
        content
    )

# Within test functions, extract the actual function from FunctionTool
# For send_message_fn references
content = re.sub(
    r'(\s+tools = await server\.get_tools\(\)\n\s+send_message = tools\["send_message"\])',
    r'\1\n        send_message_fn = send_message.fn if hasattr(send_message, "fn") else send_message',
    content
)

# For manage_instances_fn references  
content = re.sub(
    r'(\s+tools = await server\.get_tools\(\)\n\s+manage_instances = tools\["manage_instances"\])',
    r'\1\n        manage_instances_fn = manage_instances.fn if hasattr(manage_instances, "fn") else manage_instances',
    content
)

# For manage_traces_fn references
content = re.sub(
    r'(\s+tools = await server\.get_tools\(\)\n\s+manage_traces = tools\["manage_traces"\])',
    r'\1\n        manage_traces_fn = manage_traces.fn if hasattr(manage_traces, "fn") else manage_traces',
    content
)

# Add imports of functions directly from the module where they're not accessed through tools
import_line = "from automagik_tools.tools.omni import create_server, manage_instances, send_message, manage_traces"
if "from automagik_tools.tools.omni import create_server" in content and import_line not in content:
    content = re.sub(
        r'from automagik_tools.tools.omni import create_server',
        import_line,
        content
    )

# Fix direct function calls that don't use tools dict
# Find test methods that directly call manage_instances_fn without getting it from tools
content = re.sub(
    r'(\n    @pytest\.mark\.asyncio\n    async def test_[^(]+\([^)]+\):.*?\n        """[^"]+"""\n)(?!.*tools = await server\.get_tools)',
    lambda m: m.group(1) + '        from automagik_tools.tools.omni import manage_instances\n        manage_instances_fn = manage_instances.fn if hasattr(manage_instances, "fn") else manage_instances\n',
    content,
    flags=re.DOTALL
)

with open('tests/tools/test_omni_edge_cases.py', 'w') as f:
    f.write(content)

print("Fixed test_omni_edge_cases.py")

# Fix test_wait.py properly
with open('tests/tools/test_wait.py', 'r') as f:
    content = f.read()

# Make sure wait_minutes is imported at module level
if "from automagik_tools.tools.wait import" in content and "wait_minutes" not in content:
    content = re.sub(
        r'(from automagik_tools.tools.wait import[^)]+)',
        r'\1, wait_minutes',
        content
    )

# Add extraction right after imports at module level
if "wait_minutes_fn = wait_minutes.fn" not in content:
    # Find the import section and add extraction
    content = re.sub(
        r'(from automagik_tools\.tools\.wait import[^\n]+\n)',
        r'\1\n# Extract actual function from FunctionTool wrapper\nwait_minutes_fn = wait_minutes.fn if hasattr(wait_minutes, "fn") else wait_minutes\n',
        content
    )

with open('tests/tools/test_wait.py', 'w') as f:
    f.write(content)

print("Fixed test_wait.py")