#!/usr/bin/env python3
"""
Python 2 to Python 3 Migration Script for CRITs

This script automates common Python 2 to 3 syntax transformations.
Run with: python3 scripts/migrate_py2_to_py3.py

Transformations:
1. print statements → print() functions
2. except E, e: → except E as e:
3. .iteritems() → .items()
4. .itervalues() → .values()
5. .iterkeys() → .keys()
6. xrange() → range()
7. unicode() → str()
8. basestring → str
9. .has_key(x) → x in dict
10. Remove from __future__ imports
"""

import re
import os
import sys
from pathlib import Path


def fix_print_statements(content: str) -> str:
    """Convert print statements to print() functions."""
    # Match print followed by space and content (not already a function call)
    # Be careful not to match 'print(' which is already correct

    lines = content.split('\n')
    fixed_lines = []

    for line in lines:
        # Skip comments and strings that might contain 'print '
        stripped = line.lstrip()
        if stripped.startswith('#'):
            fixed_lines.append(line)
            continue

        # Match: print "..." or print '...' or print variable
        # But not: print( or print  # (comment after print)
        match = re.match(r'^(\s*)(print)\s+(?!\()(.*?)(\s*#.*)?$', line)
        if match:
            indent = match.group(1)
            args = match.group(3).rstrip()
            comment = match.group(4) or ''

            # Handle print >> sys.stderr, "msg" (redirect syntax)
            redirect_match = re.match(r'^>>\s*(\S+)\s*,\s*(.+)$', args)
            if redirect_match:
                target = redirect_match.group(1)
                message = redirect_match.group(2)
                line = f'{indent}print({message}, file={target}){comment}'
            else:
                # Simple print with arguments
                line = f'{indent}print({args}){comment}'

        fixed_lines.append(line)

    return '\n'.join(fixed_lines)


def fix_except_syntax(content: str) -> str:
    """Convert 'except E, e:' to 'except E as e:'"""
    # Match except ExceptionType, variable:
    pattern = r'except\s+(\w+(?:\.\w+)*)\s*,\s*(\w+)\s*:'
    replacement = r'except \1 as \2:'
    content = re.sub(pattern, replacement, content)

    # Also handle parenthesized exceptions: except (E1, E2), e: → except (E1, E2) as e:
    pattern_paren = r'except\s+(\([^)]+\))\s*,\s*(\w+)\s*:'
    replacement_paren = r'except \1 as \2:'
    content = re.sub(pattern_paren, replacement_paren, content)

    return content


def fix_dict_iterators(content: str) -> str:
    """Convert .iteritems/itervalues/iterkeys to .items/values/keys"""
    content = re.sub(r'\.iteritems\(\)', '.items()', content)
    content = re.sub(r'\.itervalues\(\)', '.values()', content)
    content = re.sub(r'\.iterkeys\(\)', '.keys()', content)
    return content


def fix_xrange(content: str) -> str:
    """Convert xrange() to range()"""
    return re.sub(r'\bxrange\(', 'range(', content)


def fix_raise_syntax(content: str) -> str:
    """Convert 'raise E, msg' to 'raise E(msg)'"""
    # Match: raise ExceptionType, message
    pattern = r'raise\s+(\w+)\s*,\s*(.+?)(\s*#.*)?$'

    def replace_raise(match):
        exc_type = match.group(1)
        message = match.group(2).rstrip()
        comment = match.group(3) or ''
        return f'raise {exc_type}({message}){comment}'

    lines = content.split('\n')
    fixed_lines = []
    for line in lines:
        if re.search(pattern, line):
            line = re.sub(pattern, replace_raise, line)
        fixed_lines.append(line)
    return '\n'.join(fixed_lines)


def fix_unicode(content: str) -> str:
    """Convert unicode() to str()"""
    return re.sub(r'\bunicode\(', 'str(', content)


def fix_basestring(content: str) -> str:
    """Convert basestring to str"""
    return re.sub(r'\bbasestring\b', 'str', content)


def fix_has_key(content: str) -> str:
    """Convert dict.has_key(x) to x in dict"""
    # This is tricky - we need to handle: some_dict.has_key(key) → key in some_dict
    # Pattern: identifier.has_key(something)
    pattern = r'(\w+(?:\[.*?\])?(?:\.\w+)*?)\.has_key\(([^)]+)\)'

    def replace_has_key(match):
        dict_name = match.group(1)
        key = match.group(2).strip()
        return f'{key} in {dict_name}'

    return re.sub(pattern, replace_has_key, content)


def remove_future_imports(content: str) -> str:
    """Remove from __future__ import statements (not needed in Py3)"""
    lines = content.split('\n')
    fixed_lines = []
    for line in lines:
        if not re.match(r'^\s*from\s+__future__\s+import', line):
            fixed_lines.append(line)
    return '\n'.join(fixed_lines)


def fix_file(filepath: Path, dry_run: bool = False) -> tuple[bool, list[str]]:
    """Apply all fixes to a single file."""
    changes = []

    try:
        content = filepath.read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return False, [f"Error reading {filepath}: {e}"]

    original = content

    # Apply fixes in order
    fixes = [
        ('print statements', fix_print_statements),
        ('except syntax', fix_except_syntax),
        ('raise syntax', fix_raise_syntax),
        ('dict iterators', fix_dict_iterators),
        ('xrange', fix_xrange),
        ('unicode', fix_unicode),
        ('basestring', fix_basestring),
        ('has_key', fix_has_key),
        ('__future__ imports', remove_future_imports),
    ]

    for fix_name, fix_func in fixes:
        new_content = fix_func(content)
        if new_content != content:
            changes.append(fix_name)
            content = new_content

    if content != original:
        if not dry_run:
            try:
                filepath.write_text(content, encoding='utf-8')
            except Exception as e:
                return False, [f"Error writing {filepath}: {e}"]
        return True, changes

    return False, []


def main():
    dry_run = '--dry-run' in sys.argv
    verbose = '-v' in sys.argv or '--verbose' in sys.argv

    if dry_run:
        print("DRY RUN - no files will be modified\n")

    crits_dir = Path(__file__).parent.parent / 'crits'
    if not crits_dir.exists():
        print(f"Error: {crits_dir} does not exist")
        sys.exit(1)

    py_files = list(crits_dir.rglob('*.py'))
    print(f"Found {len(py_files)} Python files to process\n")

    modified_count = 0
    change_summary = {}

    for filepath in sorted(py_files):
        modified, changes = fix_file(filepath, dry_run=dry_run)
        if modified:
            modified_count += 1
            rel_path = filepath.relative_to(crits_dir.parent)
            if verbose or dry_run:
                print(f"{'Would modify' if dry_run else 'Modified'}: {rel_path}")
                for change in changes:
                    print(f"  - {change}")
            for change in changes:
                change_summary[change] = change_summary.get(change, 0) + 1

    print(f"\n{'Would modify' if dry_run else 'Modified'} {modified_count} files")
    print("\nChange summary:")
    for change, count in sorted(change_summary.items(), key=lambda x: -x[1]):
        print(f"  {change}: {count} files")


if __name__ == '__main__':
    main()
