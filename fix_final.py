#!/usr/bin/env python3
"""Final fix for FunctionTool callable issues"""

import re

# Fix test_omni_edge_cases.py indentation
with open('tests/tools/test_omni_edge_cases.py', 'r') as f:
    lines = f.readlines()

fixed_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    fixed_lines.append(line)
    
    # Fix indentation issues - look for lines that are indented wrong
    if i + 1 < len(lines):
        next_line = lines[i + 1]
        # Check if the next line has incorrect indentation for _fn extraction
        if '_fn = ' in next_line and not next_line.startswith('        '):
            # Skip the incorrectly indented line
            i += 1
            # Add it with correct indentation
            fixed_lines.append('        ' + next_line.strip() + '\n')
        
    i += 1

with open('tests/tools/test_omni_edge_cases.py', 'w') as f:
    f.writelines(fixed_lines)

print("Fixed indentation in test_omni_edge_cases.py")

# Fix test_wait.py - add module-level import and extraction
with open('tests/tools/test_wait.py', 'r') as f:
    content = f.read()

# Check if we need to add the import
if 'from automagik_tools.tools.wait import' in content:
    # Find the existing import line and update it
    if ', wait_minutes' not in content:
        content = re.sub(
            r'(from automagik_tools\.tools\.wait import[^\n]+)',
            r'\1, wait_minutes',
            content
        )
    
    # Add the extraction at module level right after imports
    if 'wait_minutes_fn = wait_minutes.fn' not in content:
        # Find the end of imports section
        import_end = content.find('\n\n\nclass ')
        if import_end == -1:
            import_end = content.find('\n\nclass ')
        if import_end == -1:
            import_end = content.find('\nclass ')
        
        if import_end != -1:
            # Insert the extraction before the first class
            content = content[:import_end] + '\n\n# Extract actual function from FunctionTool wrapper\nwait_minutes_fn = wait_minutes.fn if hasattr(wait_minutes, "fn") else wait_minutes\n' + content[import_end:]

with open('tests/tools/test_wait.py', 'w') as f:
    f.write(content)

print("Fixed test_wait.py")

# Also fix test_automagik_workflows_enhanced.py properly
with open('tests/tools/test_automagik_workflows_enhanced.py', 'r') as f:
    content = f.read()

# Check if create_server is imported at module level
if 'from automagik_tools.tools.automagik_workflows import' in content:
    # Make sure create_server is in the imports
    if 'create_server' not in content:
        content = re.sub(
            r'(from automagik_tools\.tools\.automagik_workflows import[^\n]+)',
            r'\1, create_server',
            content
        )

with open('tests/tools/test_automagik_workflows_enhanced.py', 'w') as f:
    f.write(content)

print("Fixed test_automagik_workflows_enhanced.py")