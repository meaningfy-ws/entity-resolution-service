"""Post-process generated AsciiDoc to fix broken cross-references.

The openapi-generator asciidoc backend sanitizes model names for anchors
(stripping dashes, underscores, etc.) but leaves $ref-derived xrefs
unsanitized. This script reconciles the two by rewriting <<xref>> targets
to match their corresponding [#anchor] ids.

Additionally, every model xref is given explicit display text
(``<<id,Title>>``) so that Asciidoctor does not fall back to
"Section X.X" rendering when ``:numbered:`` / ``:sectnums:`` is active.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Primitive / built-in type names that should never be rendered as xrefs.
PRIMITIVE_TYPES = frozenset(
    {
        "string",
        "String",
        "integer",
        "Integer",
        "number",
        "Number",
        "boolean",
        "Boolean",
        "object",
        "Object",
        "Map",
        "AnyType",
        "Date",
        "BigDecimal",
        "oas_any_type_not_mapped",
        "anyOf",
    }
)

ANCHOR_RE = re.compile(r"\[#(\w+)\]")
HEADING_AFTER_ANCHOR_RE = re.compile(r"\[#(\w+)\]\n=== (.+)")
XREF_RE = re.compile(r"<<([^,>]*?)(?:,([^>]*?))?>>")


def _sanitize(name: str) -> str:
    """Reproduce the generator's classname sanitization: strip non-alnum."""
    return re.sub(r"[^a-zA-Z0-9]", "", name)


def fix_file(path: Path) -> int:
    text = path.read_text(encoding="utf-8")

    anchors = set(ANCHOR_RE.findall(text))

    # Build anchor → display-title lookup from ``[#Id]\n=== Title`` pairs.
    anchor_titles: dict[str, str] = {}
    for m in HEADING_AFTER_ANCHOR_RE.finditer(text):
        anchor_titles[m.group(1)] = m.group(2).strip()

    # Build a lookup: sanitized form → actual anchor id.
    anchor_lookup: dict[str, str] = {}
    for a in anchors:
        anchor_lookup[a] = a
        anchor_lookup[_sanitize(a)] = a

    fixes = 0

    def _replace_xref(m: re.Match) -> str:
        nonlocal fixes
        ref = m.group(1)
        existing_label = m.group(2)

        # Empty xref → dash (bodyless response).
        if not ref.strip():
            fixes += 1
            return "-"

        # HTML-encoded refs (e.g. anyOf<>).
        clean_ref = ref.replace("&lt;", "").replace("&gt;", "")

        # Primitive types → render as inline code, not xref.
        if clean_ref in PRIMITIVE_TYPES or _sanitize(clean_ref) in PRIMITIVE_TYPES:
            fixes += 1
            return f"`{clean_ref}`"

        # Resolve the target anchor id.
        target = None
        if ref in anchors:
            target = ref
        else:
            sanitized = _sanitize(ref)
            if sanitized in anchor_lookup:
                target = anchor_lookup[sanitized]

        if target is None:
            return m.group(0)  # No match — leave untouched.

        # Determine display text: keep existing, or derive from heading title.
        label = existing_label or anchor_titles.get(target, target)

        changed = target != ref or (not existing_label and label)
        if changed:
            fixes += 1
        return f"<<{target},{label}>>"

    text = XREF_RE.sub(_replace_xref, text)
    path.write_text(text, encoding="utf-8")
    return fixes


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file.adoc> [file2.adoc ...]", file=sys.stderr)
        sys.exit(1)

    for arg in sys.argv[1:]:
        p = Path(arg)
        if not p.exists():
            print(f"  SKIP {p} (not found)", file=sys.stderr)
            continue
        n = fix_file(p)
        print(f"  {p.name}: {n} xrefs fixed")


if __name__ == "__main__":
    main()
