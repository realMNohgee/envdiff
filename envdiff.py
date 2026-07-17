#!/usr/bin/env python3
"""envdiff — Diff two .env files. Zero dependencies, pure Python stdlib."""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Dict, List, Optional, Tuple


def parse_env(lines: List[str]) -> Tuple[Dict[str, str], List[str]]:
    """Parse .env lines into a dict and ordered keys list (including blanks/comments)."""
    result: Dict[str, str] = {}
    errors: List[str] = []
    for lineno, raw in enumerate(lines, 1):
        line = raw.rstrip("\n\r")
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            errors.append(f"line {lineno}: no '=' separator: {stripped}")
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip()
        if key in result:
            errors.append(f"line {lineno}: duplicate key '{key}'")
        result[key] = value
    return result, errors


def read_file_or_stdin(path: str) -> List[str]:
    if path == "-":
        return sys.stdin.readlines()
    with open(path) as f:
        return f.readlines()


def emit_result(data: dict, fmt: str) -> None:
    if fmt == "json":
        json.dump(data, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        for k, v in data.items():
            print(f"{k}: {v}")


def cmd_compare(args: argparse.Namespace) -> int:
    lines1 = read_file_or_stdin(args.file1)
    lines2 = read_file_or_stdin(args.file2)
    env1, _ = parse_env(lines1)
    env2, _ = parse_env(lines2)

    keys1 = set(env1.keys())
    keys2 = set(env2.keys())

    only1 = sorted(keys1 - keys2)
    only2 = sorted(keys2 - keys1)
    common_keys = sorted(keys1 & keys2)
    diff_vals = {k: {"file1": env1[k], "file2": env2[k]} for k in common_keys if env1[k] != env2[k]}
    identical = sorted(k for k in common_keys if env1[k] == env2[k])

    result = {
        "only_in_file1": {k: env1[k] for k in only1},
        "only_in_file2": {k: env2[k] for k in only2},
        "different_values": diff_vals,
        "identical": identical,
    }

    if args.format == "json":
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        for header, items in [
            ("Keys only in file1", [(k, env1[k]) for k in only1]),
            ("Keys only in file2", [(k, env2[k]) for k in only2]),
            ("Keys with different values", [(k, diff_vals[k]) for k in sorted(diff_vals)]),
            ("Identical keys", [(k, env1[k]) for k in identical]),
        ]:
            if items:
                print(f"--- {header} ---")
                for k, v in items:
                    print(f"  {k}={v}")
    return 0 if not (only1 or only2 or diff_vals) else 1


def cmd_sort(args: argparse.Namespace) -> int:
    lines = read_file_or_stdin(args.file)
    env_lines: List[Tuple[str, str, str]] = []  # (key, "KEY=value", original raw)
    comment_lines: List[str] = []

    for raw in lines:
        line = raw.rstrip("\n\r")
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            comment_lines.append(line)
        else:
            if "=" in stripped:
                key = stripped.split("=", 1)[0].strip()
                env_lines.append((key.lower(), stripped, line))
            else:
                comment_lines.append(line)

    env_lines.sort(key=lambda x: x[0])
    for c in comment_lines:
        print(c)
    for _, _, orig in env_lines:
        print(orig)

    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    lines = read_file_or_stdin(args.file)
    issues: List[dict] = []
    seen_keys: Dict[str, int] = {}
    key_pattern = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

    for lineno, raw in enumerate(lines, 1):
        line = raw.rstrip("\n\r")
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            issues.append({"line": lineno, "type": "no_separator", "detail": stripped})
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip()

        # Check duplicate keys
        if key in seen_keys:
            issues.append({
                "line": lineno,
                "type": "duplicate_key",
                "detail": f"'{key}' also on line {seen_keys[key]}",
            })
        else:
            seen_keys[key] = lineno

        # Check invalid key name
        if not key_pattern.match(key):
            issues.append({
                "line": lineno,
                "type": "invalid_key",
                "detail": f"'{key}' contains invalid characters (use [A-Za-z0-9_])",
            })

        # Check unquoted values with spaces
        if " " in value and not (value.startswith('"') or value.startswith("'")):
            issues.append({
                "line": lineno,
                "type": "unquoted_spaces",
                "detail": f"key '{key}' has value with spaces but no quotes: {value}",
            })

    if args.format == "json":
        result = {"valid": len(issues) == 0, "issues": issues}
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        if not issues:
            print("File is valid.")
        else:
            for i in issues:
                print(f"  line {i['line']}: [{i['type']}] {i['detail']}")
            print(f"\n{len(issues)} issue(s) found.")

    return 1 if issues else 0


def main() -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--format", choices=["text", "json"], default="text")

    p = argparse.ArgumentParser(description="envdiff — Diff, sort, and validate .env files")
    sub = p.add_subparsers(dest="cmd", required=True)

    cmp_parser = sub.add_parser("compare", parents=[common], help="Compare two .env files")
    cmp_parser.add_argument("file1", help="First .env file (or - for stdin)")
    cmp_parser.add_argument("file2", help="Second .env file (or - for stdin)")
    cmp_parser.set_defaults(func=cmd_compare)

    srt_parser = sub.add_parser("sort", parents=[common], help="Sort a .env file alphabetically")
    srt_parser.add_argument("file", help=".env file to sort (or - for stdin)")
    srt_parser.set_defaults(func=cmd_sort)

    val_parser = sub.add_parser("validate", parents=[common], help="Validate a .env file")
    val_parser.add_argument("file", help=".env file to validate (or - for stdin)")
    val_parser.set_defaults(func=cmd_validate)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
