#!/usr/bin/env python3
"""
Script to fix E501 line length violations by breaking long lines.
"""

import os


def fix_long_lines(file_path, max_length=120):
    """Fix long lines in a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')
        fixed_lines = []

        for line in lines:
            if len(line) <= max_length:
                fixed_lines.append(line)
                continue

            # Handle different types of long lines
            if line.strip().startswith('#'):
                # Comment line - break at sentence boundaries
                fixed_lines.extend(break_comment_line(line, max_length))
            elif '(' in line and ')' in line:
                # Function call or definition
                fixed_lines.extend(break_function_call(line, max_length))
            elif '=' in line and not line.strip().startswith('#'):
                # Assignment line
                fixed_lines.extend(break_assignment_line(line, max_length))
            else:
                # Generic line break
                fixed_lines.extend(break_generic_line(line, max_length))

        # Write back the fixed content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(fixed_lines))

        return True
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

def break_comment_line(line, max_length):
    """Break a comment line at sentence boundaries."""
    lines = []
    current_line = line

    while len(current_line) > max_length:
        # Find the last sentence boundary before max_length
        break_point = max_length
        for i in range(max_length - 1, max_length // 2, -1):
            if current_line[i] in '.!?':
                break_point = i + 1
                break
            elif current_line[i] == ',' and i > max_length - 20:
                break_point = i + 1
                break

        lines.append(current_line[:break_point].rstrip())
        current_line = '# ' + current_line[break_point:].lstrip()

    if current_line.strip():
        lines.append(current_line)

    return lines

def break_function_call(line, max_length):
    """Break a function call line."""
    if '(' in line and ')' in line:
        # Find the opening parenthesis
        paren_start = line.find('(')
        if paren_start > 0 and len(line) > max_length:
            # Break after the function name
            lines = [line[:paren_start + 1]]
            args = line[paren_start + 1:]

            # Handle arguments
            while len(args) > max_length - 4:
                # Find a comma to break at
                comma_pos = args[:max_length - 4].rfind(',')
                if comma_pos == -1:
                    break

                lines.append('    ' + args[:comma_pos + 1])
                args = args[comma_pos + 1:].strip()

            if args.strip():
                lines.append('    ' + args)

            return lines

    return [line]

def break_assignment_line(line, max_length):
    """Break an assignment line."""
    if '=' in line:
        eq_pos = line.find('=')
        if eq_pos > 0 and len(line) > max_length:
            # Break at the equals sign
            var_part = line[:eq_pos].rstrip()
            value_part = line[eq_pos + 1:].strip()

            lines = [var_part + ' =']

            # Handle the value part
            while len(value_part) > max_length - 4:
                # Find a good break point
                break_point = max_length - 4
                for i in range(break_point - 1, break_point // 2, -1):
                    if value_part[i] in ',+|&':
                        break_point = i + 1
                        break

                lines.append('    ' + value_part[:break_point].rstrip())
                value_part = value_part[break_point:].strip()

            if value_part.strip():
                lines.append('    ' + value_part)

            return lines

    return [line]

def break_generic_line(line, max_length):
    """Generic line breaking."""
    lines = []
    remaining = line

    while len(remaining) > max_length:
        # Find a good break point
        break_point = max_length
        for i in range(max_length - 1, max_length // 2, -1):
            if remaining[i] in ' ,;|&':
                break_point = i + 1
                break

        lines.append(remaining[:break_point].rstrip())
        remaining = remaining[break_point:].lstrip()

    if remaining.strip():
        lines.append(remaining)

    return lines

def main():
    """Main function to fix line length issues."""
    # Get Python files from the current directory and subdirectories
    python_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith(
    '.py') and not any(skip in root for skip in ['.git', '__pycache__', '.venv', 'node_modules']):
                python_files.append(os.path.join(root, file))

    fixed_count = 0
    error_count = 0

    for file_path in python_files:
        if fix_long_lines(file_path):
            fixed_count += 1
        else:
            error_count += 1

    print(f"Fixed {fixed_count} files, {error_count} errors")

if __name__ == '__main__':
    main()
