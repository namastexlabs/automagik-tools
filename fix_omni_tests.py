#!/usr/bin/env python3
"""Fix FunctionTool callable issues in omni test files"""

import re

# Read test_omni.py
with open('tests/tools/test_omni.py', 'r') as f:
    content = f.read()

# Replace all manage_instances calls
content = re.sub(
    r'(from automagik_tools\.tools\.omni import .*manage_instances.*\n)',
    r'\1        manage_instances_fn = manage_instances.fn if hasattr(manage_instances, "fn") else manage_instances\n',
    content
)
content = re.sub(
    r'(\s+)(result = await manage_instances\()',
    r'\1result = await manage_instances_fn(',
    content
)
content = re.sub(
    r'(\s+)(await manage_instances\()',
    r'\1await manage_instances_fn(',
    content
)
content = re.sub(
    r'(\s+)(coro = manage_instances\()',
    r'\1coro = manage_instances_fn(',
    content
)
content = re.sub(
    r'(\s+)manage_instances\(operation',
    r'\1manage_instances_fn(operation',
    content
)

# Replace all send_message calls
content = re.sub(
    r'(from automagik_tools\.tools\.omni import .*send_message.*\n)',
    r'\1        send_message_fn = send_message.fn if hasattr(send_message, "fn") else send_message\n',
    content
)
content = re.sub(
    r'(\s+)(result = await send_message\()',
    r'\1result = await send_message_fn(',
    content
)
content = re.sub(
    r'(\s+)(await send_message\()',
    r'\1await send_message_fn(',
    content
)

# Replace all manage_traces calls
content = re.sub(
    r'(from automagik_tools\.tools\.omni import .*manage_traces.*\n)',
    r'\1        manage_traces_fn = manage_traces.fn if hasattr(manage_traces, "fn") else manage_traces\n',
    content
)
content = re.sub(
    r'(\s+)(result = await manage_traces\()',
    r'\1result = await manage_traces_fn(',
    content
)

# Replace all manage_profiles calls
content = re.sub(
    r'(from automagik_tools\.tools\.omni import .*manage_profiles.*\n)',
    r'\1        manage_profiles_fn = manage_profiles.fn if hasattr(manage_profiles, "fn") else manage_profiles\n',
    content
)
content = re.sub(
    r'(\s+)(result = await manage_profiles\()',
    r'\1result = await manage_profiles_fn(',
    content
)

# Write back test_omni.py
with open('tests/tools/test_omni.py', 'w') as f:
    f.write(content)

# Read test_omni_edge_cases.py
with open('tests/tools/test_omni_edge_cases.py', 'r') as f:
    content = f.read()

# Same replacements for edge cases file
content = re.sub(
    r'(from automagik_tools\.tools\.omni import .*manage_instances.*\n)',
    r'\1        manage_instances_fn = manage_instances.fn if hasattr(manage_instances, "fn") else manage_instances\n',
    content
)
content = re.sub(
    r'(\s+)(result = await manage_instances\()',
    r'\1result = await manage_instances_fn(',
    content
)
content = re.sub(
    r'(\s+)manage_instances\(operation',
    r'\1manage_instances_fn(operation',
    content
)

content = re.sub(
    r'(from automagik_tools\.tools\.omni import .*send_message.*\n)',
    r'\1        send_message_fn = send_message.fn if hasattr(send_message, "fn") else send_message\n',
    content
)
content = re.sub(
    r'(\s+)(result = await send_message\()',
    r'\1result = await send_message_fn(',
    content
)

content = re.sub(
    r'(from automagik_tools\.tools\.omni import .*manage_traces.*\n)',
    r'\1        manage_traces_fn = manage_traces.fn if hasattr(manage_traces, "fn") else manage_traces\n',
    content
)
content = re.sub(
    r'(\s+)(result = await manage_traces\()',
    r'\1result = await manage_traces_fn(',
    content
)

# Write back test_omni_edge_cases.py
with open('tests/tools/test_omni_edge_cases.py', 'w') as f:
    f.write(content)

print("Fixed omni test files")