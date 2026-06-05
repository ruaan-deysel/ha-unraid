#!/usr/bin/env python3
"""
Enforce the unraid-api boundary.

Scans custom_components/unraid/ for patterns that indicate direct network I/O
to the Unraid server, bypassing the unraid-api library (UnraidClient).

Any AI agent (Claude Code, Codex, Copilot, Gemini, etc.) that introduces code
matching these patterns is violating the project's core architectural rule.
If the needed functionality is not available in unraid-api, open an issue at
https://github.com/ruaan-deysel/unraid-api — do NOT add a workaround here.

Exit 0 = clean, Exit 1 = violations found.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "custom_components" / "unraid"

# Each entry is (regex_pattern, violation_description).
# Patterns are matched against individual source lines (stripped).
BANNED: list[tuple[str, str]] = [
    # Synchronous HTTP
    (r"\bimport requests\b", "sync HTTP via 'requests' — use UnraidClient"),
    (r"\bfrom requests\b", "sync HTTP via 'requests' — use UnraidClient"),
    # Async HTTP alternatives
    (r"\bimport httpx\b", "HTTP via 'httpx' — use UnraidClient"),
    (r"\bfrom httpx\b", "HTTP via 'httpx' — use UnraidClient"),
    # stdlib HTTP modules
    (
        r"\bimport urllib\.request\b",
        "stdlib HTTP via 'urllib.request' — use UnraidClient",
    ),
    (
        r"\bfrom urllib\.request\b",
        "stdlib HTTP via 'urllib.request' — use UnraidClient",
    ),
    (r"\bimport urllib3\b", "HTTP via 'urllib3' — use UnraidClient"),
    (r"\bfrom urllib3\b", "HTTP via 'urllib3' — use UnraidClient"),
    (r"\bimport http\.client\b", "stdlib HTTP via 'http.client' — use UnraidClient"),
    (r"\bfrom http\.client\b", "stdlib HTTP via 'http.client' — use UnraidClient"),
    # Raw WebSocket libraries
    (r"\bimport websockets\b", "raw websockets — use UnraidClient"),
    (r"\bfrom websockets\b", "raw websockets — use UnraidClient"),
    # SSH
    (r"\bimport paramiko\b", "SSH via 'paramiko' — use UnraidClient"),
    (r"\bimport asyncssh\b", "SSH via 'asyncssh' — use UnraidClient"),
    # Raw GraphQL clients (gql, python-graphql-client, etc.)
    (r"\bfrom gql\b", "raw GraphQL client 'gql' — use UnraidClient"),
    (r"\bimport gql\b", "raw GraphQL client 'gql' — use UnraidClient"),
    (r"\bfrom python_graphql_client\b", "raw GraphQL client — use UnraidClient"),
    (r"\bimport python_graphql_client\b", "raw GraphQL client — use UnraidClient"),
    # Direct aiohttp session creation — HA's async_get_clientsession() is fine
    # when its result is passed to UnraidClient, but creating a bare ClientSession
    # for direct use bypasses the library.
    (
        r"aiohttp\.ClientSession\s*\(",
        "direct aiohttp.ClientSession() — pass HA's session to UnraidClient instead",
    ),
]

_COMPILED = [(re.compile(pat), desc) for pat, desc in BANNED]


def check_file(path: Path) -> list[tuple[int, str, str]]:
    """Return list of (line_no, line_text, violation_desc) for a file."""
    violations: list[tuple[int, str, str]] = []
    text = path.read_text(encoding="utf-8")
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        for pattern, desc in _COMPILED:
            if pattern.search(line):
                violations.append((lineno, line.rstrip(), desc))
                break  # one report per line
    return violations


def main() -> int:
    if not TARGET.is_dir():
        print(f"ERROR: target directory not found: {TARGET}", file=sys.stderr)
        return 1

    py_files = sorted(TARGET.rglob("*.py"))
    all_violations: list[tuple[Path, int, str, str]] = []

    for path in py_files:
        for lineno, line, desc in check_file(path):
            all_violations.append((path, lineno, line, desc))

    if not all_violations:
        print(
            f"✓ API boundary check passed — scanned {len(py_files)} file(s), "
            "no direct network I/O found."
        )
        return 0

    print(
        "✗ API boundary violations detected!\n"
        "  All communication with the Unraid server MUST go through UnraidClient\n"
        "  (unraid-api library). If the needed feature is missing from unraid-api,\n"
        "  open an issue at https://github.com/ruaan-deysel/unraid-api — do NOT\n"
        "  add a workaround in this repository.\n",
        file=sys.stderr,
    )
    for path, lineno, line, desc in all_violations:
        rel = path.relative_to(ROOT)
        print(f"  {rel}:{lineno}: {desc}", file=sys.stderr)
        print(f"    {line}", file=sys.stderr)

    print(
        f"\n{len(all_violations)} violation(s) in "
        f"{len({v[0] for v in all_violations})} file(s).",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
