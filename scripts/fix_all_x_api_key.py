#!/usr/bin/env python3
"""Fix all functions with x_api_key parameter to use it properly"""

import re

# List of functions that need fixing (from our earlier analysis)
functions_to_fix = [
    'list_mcp_servers',
    'create_mcp_server', 
    'get_mcp_server',
    'update_mcp_server',
    'delete_mcp_server',
    'start_mcp_server',
    'stop_mcp_server',
    'restart_mcp_server',
    'call_mcp_tool',
    'access_mcp_resource',
    'list_mcp_server_tools',
    'list_mcp_server_resources',
    'list_agent_mcp_tools',
    'run_claude_code_workflow',
    'get_claude_code_run_status',
    'list_claude_code_workflows',
    'get_claude_code_health'
]

# Read the file
with open('automagik_tools/tools/automagik/__init__.py', 'r') as f:
    lines = f.readlines()

# Process line by line
i = 0
while i < len(lines):
    line = lines[i]
    
    # Check if this line defines one of our target functions
    for func_name in functions_to_fix:
        if f'async def {func_name}(' in line and 'x_api_key: Optional[str]' in line:
            # Find the return statement
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith('return await make_api_request'):
                j += 1
            
            if j < len(lines):
                # Check if extra_headers is already added
                already_fixed = False
                for k in range(i, j):
                    if 'extra_headers' in lines[k]:
                        already_fixed = True
                        break
                
                if not already_fixed:
                    # Find the line before return statement
                    insert_line = j
                    while insert_line > i and lines[insert_line-1].strip() == '':
                        insert_line -= 1
                    
                    # Insert the extra_headers code
                    indent = '    '
                    lines.insert(insert_line, f'{indent}# Use x_api_key if provided\n')
                    lines.insert(insert_line + 1, f'{indent}extra_headers = {{"x-api-key": x_api_key}} if x_api_key else None\n')
                    lines.insert(insert_line + 2, f'{indent}\n')
                    
                    # Update the return statement to include extra_headers
                    # Find the closing parenthesis
                    return_start = j + 3  # Adjusted for inserted lines
                    paren_count = 1
                    k = return_start + 1
                    while k < len(lines) and paren_count > 0:
                        for char in lines[k]:
                            if char == '(':
                                paren_count += 1
                            elif char == ')':
                                paren_count -= 1
                                if paren_count == 0:
                                    # Insert extra_headers before the closing paren
                                    lines[k] = lines[k].replace(
                                        ')',
                                        ',\n        extra_headers=extra_headers\n    )',
                                        1
                                    )
                                    break
                        k += 1
                    
                    # Skip ahead to avoid reprocessing
                    i = k
                    break
    i += 1

# Write the fixed content back
with open('automagik_tools/tools/automagik/__init__.py', 'w') as f:
    f.writelines(lines)

print("Fixed x_api_key handling in all affected functions")