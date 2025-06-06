#!/usr/bin/env python3
"""Fix all functions with x_api_key parameter to use it properly"""

import re

# Read the file
with open('automagik_tools/tools/automagik/__init__.py', 'r') as f:
    content = f.read()

# Pattern to find functions that need fixing
# This matches the pattern where we have x_api_key parameter but don't use extra_headers
pattern = r'(async def \w+\([^)]*x_api_key: Optional\[str\] = None[^)]*\)[^{]+?\{[^}]+?)(return await make_api_request\(\s*method="[^"]+",\s*endpoint=endpoint,\s*params=params,\s*json_data=json_data,\s*ctx=ctx\s*\))'

def replace_function(match):
    """Add extra_headers handling to functions with x_api_key"""
    func_def = match.group(1)
    return_stmt = match.group(2)
    
    # Add the extra_headers line before the return statement
    new_code = func_def + '''    
    # Use x_api_key if provided
    extra_headers = {"x-api-key": x_api_key} if x_api_key else None
    
    ''' + return_stmt.replace(
        'ctx=ctx',
        'ctx=ctx,\n        extra_headers=extra_headers'
    )
    
    return new_code

# Apply the fix to all matching functions
fixed_content = re.sub(pattern, replace_function, content, flags=re.DOTALL)

# Write the fixed content back
with open('automagik_tools/tools/automagik/__init__.py', 'w') as f:
    f.write(fixed_content)

print("Fixed x_api_key handling in all affected functions")