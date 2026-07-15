import unicodedata
from collections.abc import Sequence

WIDTH = 64


def display_width(text: str) -> int:
    """Counts wide characters (Hangul/CJK/fullwidth) as 2 columns so padding
    lines up in a monospace terminal -- len() alone undercounts Korean text
    by half, which throws off every center()/ljust() call in this module."""
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in text)


def pad(text: str, width: int) -> str:
    return text + " " * max(width - display_width(text), 0)


def centered(text: str, width: int = WIDTH) -> str:
    extra = max(width - display_width(text), 0)
    left = extra // 2
    right = extra - left
    return " " * left + text + " " * right


def divider(char: str = "-", width: int = WIDTH) -> str:
    return char * width


def blank() -> str:
    return ""


def title_block(title: str, width: int = WIDTH) -> list[str]:
    """Heavy '=' banner for the top-level app header."""
    return [divider("=", width), centered(title, width), divider("=", width)]


def section_title(title: str, width: int = WIDTH) -> list[str]:
    """Lighter '-' banner for a submenu's own section header."""
    return [divider("-", width), centered(title, width), divider("-", width)]


def render_table(
    headers: Sequence[str], rows: Sequence[Sequence[object]], widths: Sequence[int]
) -> list[str]:
    """Box-drawn table (header + separator + data rows). `widths` is the
    per-column content width, in display columns (not counting the padding
    space or border characters this function adds)."""

    def border(left: str, mid: str, right: str) -> str:
        return left + mid.join("─" * (w + 2) for w in widths) + right

    def row(cells: Sequence[object]) -> str:
        return (
            "│"
            + "│".join(f" {pad(str(cell), w)} " for cell, w in zip(cells, widths))
            + "│"
        )

    lines = [border("┌", "┬", "┐"), row(headers), border("├", "┼", "┤")]
    lines.extend(row(data_row) for data_row in rows)
    lines.append(border("└", "┴", "┘"))
    return lines
