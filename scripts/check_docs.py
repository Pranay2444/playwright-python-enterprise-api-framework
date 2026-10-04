"""Check local Markdown file targets without network requests or secret-file reads."""

import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
folders = [root / name for name in ("docs", "agents", ".agents", "src", "tests", "lab")]
paths = [root / "README.md", root / "AGENTS.md"]
for folder in folders:
    paths.extend(folder.rglob("*.md"))
checked = 0
missing = []
for path in paths:
    if not path.exists():
        continue
    for target in re.findall(r"\[[^\]]*\]\(([^\s)]+)\)", path.read_text()):
        if target.startswith(("https://", "http://", "mailto:", "#")):
            continue
        relative = target.split("#")[0]
        checked += 1
        if not (path.parent / relative).exists():
            missing.append(f"{path.relative_to(root)}: {relative}")
if missing:
    raise SystemExit("Missing Markdown file targets:\n" + "\n".join(missing))
print(f"Checked {checked} local Markdown file targets; anchors and remote URLs excluded")
