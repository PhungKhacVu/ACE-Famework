"""Terminal UI helpers for the ACE Framework CLI.

Provides ANSI-colour formatting, banner, table, and separator utilities
that degrade gracefully when colours are not supported — e.g. when stdout
is redirected to a pipe/file, or when the ``NO_COLOR`` environment variable
is set (see https://no-color.org/).

Designed for narrow mobile terminals such as a-Shell on iOS (~54 chars).
"""
from __future__ import annotations

import os
import sys
from typing import Sequence

# ---------------------------------------------------------------------------
# Colour-support detection
# ---------------------------------------------------------------------------

def _colour_enabled() -> bool:
    """Return True when ANSI colour codes should be emitted."""
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


# ANSI escape codes
_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_GREEN = "\033[32m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_CYAN = "\033[36m"


def _c(code: str, text: str) -> str:
    """Wrap *text* with *code* (and reset) when colours are enabled."""
    if _colour_enabled():
        return f"{code}{text}{_RESET}"
    return text


def bold(text: str) -> str:
    return _c(_BOLD, text)


def dim(text: str) -> str:
    return _c(_DIM, text)


def green(text: str) -> str:
    return _c(_GREEN, text)


def red(text: str) -> str:
    return _c(_RED, text)


def yellow(text: str) -> str:
    return _c(_YELLOW, text)


def cyan(text: str) -> str:
    return _c(_CYAN, text)


# ---------------------------------------------------------------------------
# Box / banner
# ---------------------------------------------------------------------------

# Width chosen to fit comfortably on a mobile (iPhone) terminal
_WIDTH = 54


def banner(title: str) -> None:
    """Print a titled box banner to stdout."""
    inner = _WIDTH - 2  # characters inside the side borders
    top = "┌" + "─" * inner + "┐"
    mid = "│  " + title.ljust(inner - 2) + "│"
    bot = "└" + "─" * inner + "┘"
    print(bold(top))
    print(bold(mid))
    print(bold(bot))


def separator() -> None:
    """Print a thin horizontal rule."""
    print(dim("  " + "─" * (_WIDTH - 2)))


# ---------------------------------------------------------------------------
# Table
# ---------------------------------------------------------------------------

def table(
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    col_widths: Sequence[int],
) -> None:
    """Print a simple fixed-width aligned table."""
    header_parts = [bold(h.ljust(w)) for h, w in zip(headers, col_widths)]
    print("  " + "  ".join(header_parts))
    dividers = [dim("─" * w) for w in col_widths]
    print("  " + "  ".join(dividers))
    for row in rows:
        cells = [str(cell).ljust(w) for cell, w in zip(row, col_widths)]
        print("  " + "  ".join(cells))
