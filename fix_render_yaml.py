#!/usr/bin/env python3
"""Fix PYTHONPATH conflicts in render.yaml"""

import re
from pathlib import Path

def fix_render_yaml():
    """Remove PYTHONPATH from startCommand lines in render.yaml"""
    yaml_file = Path("c:/Users/Administrator/Desktop/main jobhuntin/render.yaml")
    
    if not yaml_file.exists():
        print("render.yaml not found")
        return
    
    content = yaml_file.read_text(encoding='utf-8')
    original_content = content
    
    # Replace all occurrences of PYTHONPATH=apps:packages:. in startCommand
    # This pattern looks for startCommand lines with PYTHONPATH
    pattern = r'(startCommand:\s*)PYTHONPATH=apps:packages:\s*(.+)'
    replacement = r'\1\2'
    
    content = re.sub(pattern, replacement, content)
    
    # Save if changed
    if content != original_content:
        yaml_file.write_text(content, encoding='utf-8')
        print("✅ Fixed PYTHONPATH conflicts in render.yaml")
        
        # Count changes
        changes = len(re.findall(pattern, original_content))
        print(f"📝 Removed {changes} PYTHONPATH conflicts from startCommand lines")
    else:
        print("ℹ️  No PYTHONPATH conflicts found in render.yaml")

if __name__ == "__main__":
    fix_render_yaml()
