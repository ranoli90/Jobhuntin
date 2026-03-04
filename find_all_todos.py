import json
import os
from pathlib import Path

def find_todos(directory):
    todos = []
    for root, dirs, files in os.walk(directory):
        # Skip node_modules and other irrelevant directories
        dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', 'dist', 'build', '__pycache__']]
        
        for file in files:
            if file.endswith(('.ts', '.tsx', '.js', '.jsx', '.py')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines, 1):
                            if 'TODO' in line.upper():
                                todos.append(f"{file_path}:{i} - {line.strip()}")
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    return todos

# Search in the main source directory
todos = find_todos('c:/Users/Administrator/Desktop/main jobhuntin/sorce')

print(f"Found {len(todos)} TODO comments:")
for todo in todos:
    print(f"  {todo}")
