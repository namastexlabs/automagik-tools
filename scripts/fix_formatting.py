#!/usr/bin/env python3
"""Fix formatting issues from the previous script"""

# Read the file
with open('automagik_tools/tools/automagik/__init__.py', 'r') as f:
    content = f.read()

# Fix the ctx\n    , pattern
content = content.replace('ctx\n    ,', 'ctx,')

# Write back
with open('automagik_tools/tools/automagik/__init__.py', 'w') as f:
    f.write(content)

print("Fixed formatting issues")