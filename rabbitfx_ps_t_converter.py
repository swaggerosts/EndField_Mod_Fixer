from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

RABBITFX_RUN = r"CommandList\RabbitFX\SetTextures"
RABBITFX_MAPS = (
    ("DiffuseMap", "Diffuse"),
    ("NormalMap", "Normalmap"),
    ("LightMap", "Lightmap"),
    ("HighLightMap", "HighLightmap"),
    ("RampMap", "Rampmap"),
    ("MaterialMap", "Materialmap"),
    ("StockingMap", "Stockingmap"),
)
RABBITFX_ROLES = tuple(role for _, role in RABBITFX_MAPS)
RABBITFX_PATTERNS = tuple(
    (re.compile(rf"(?<![A-Za-z]){re.escape(keyword)}(?![A-Za-z])", re.IGNORECASE), role)
    for keyword, role in RABBITFX_MAPS
)
RABBITFX_KEYWORDS = "/".join(
    keyword for keyword, _ in RABBITFX_MAPS
)
BACKUP_TOKEN = ".rabbitfx_backup."
BACKUP_RE = re.compile(
    r"(\.backup\.|\.after$|\.manual_before_restore\.|\.rabbitfx_backup\.)",
    re.IGNORECASE,
)
SECTION_RE = re.compile(r"^\s*\[(?P<name>[^\]]+)\]\s*$")
PS_T_RE = re.compile(r"^(?P<indent>\s*)ps-t(?P<slot>\d+)(?P<eq>\s*=\s*)(?P<res>\S+)(?P<tail>.*)$", re.IGNORECASE)
RABBITFX_RE = re.compile(r"^\s*Resource\\RabbitFX\\|^\s*run\s*=\s*CommandList\\RabbitFX\\SetTextures", re.IGNORECASE)


@dataclass
class Section:
    name: str
    start: int
    end: int


@dataclass
class Conversion:
    section: str
    slots: list[int]
    roles: list[str]


@dataclass
class FileResult:
    path: Path
    changed: bool
    conversions: list[Conversion]


def detect_newline(text: str) -> str:
    if "\r\n" in text:
        return "\r\n"
    if "\r" in text:
        return "\r"
    return "\n"


def decode_bytes(data: bytes) -> tuple[str, str]:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace"), "utf-8"


def read_ini(path: Path) -> tuple[str, str]:
    return decode_bytes(path.read_bytes())


def write_ini(path: Path, text: str, encoding: str) -> None:
    path.write_text(text, encoding=encoding, newline="")


def collect_sections(lines: list[str]) -> list[Section]:
    headers: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        match = SECTION_RE.match(line.rstrip("\r\n"))
        if match:
            headers.append((index, match.group("name").strip()))

    sections: list[Section] = []
    for index, (start, name) in enumerate(headers):
        end = headers[index + 1][0] if index + 1 < len(headers) else len(lines)
        sections.append(Section(name=name, start=start, end=end))
    return sections


def parse_slots(raw: str) -> set[int]:
    slots: set[int] = set()
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            slots.add(int(item))
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"invalid slot: {item!r}") from exc
    if not slots:
        raise argparse.ArgumentTypeError("at least one slot is required")
    return slots


def infer_role(resource: str) -> str | None:
    for pattern, role in RABBITFX_PATTERNS:
        if pattern.search(resource):
            return role
    return None


def make_rabbitfx_lines(indent: str, role_resources: dict[str, str]) -> list[str]:
    lines: list[str] = []
    for role in RABBITFX_ROLES:
        resource = role_resources.get(role)
        if resource:
            lines.append(f"{indent}Resource\\RabbitFX\\{role} = ref {resource}")
    lines.append(f"{indent}run = {RABBITFX_RUN}")
    return lines


def convert_content(
    content: str,
    slots: set[int] | None,
    comment_originals: bool,
    force: bool,
) -> tuple[str, list[Conversion]]:
    lines = content.splitlines()
    had_final_newline = content.endswith(("\n", "\r"))
    newline = detect_newline(content)
    output = list(lines)
    conversions: list[Conversion] = []

    for section in reversed(collect_sections(lines)):
        section_lines = lines[section.start:section.end]
        if not force and any(RABBITFX_RE.search(line) and not line.lstrip().startswith(";") for line in section_lines):
            continue

        target_indexes: list[int] = []
        role_resources: dict[str, str] = {}
        role_slots: dict[str, int] = {}
        first_indent = ""

        for index in range(section.start + 1, section.end):
            line = lines[index]
            stripped = line.lstrip()
            if stripped.startswith(";") or "CheckTextureOverride" in line:
                continue

            match = PS_T_RE.match(line)
            if not match:
                continue

            slot = int(match.group("slot"))
            if slots is not None and slot not in slots:
                continue

            role = infer_role(match.group("res"))
            if not role:
                continue

            if not first_indent:
                first_indent = match.group("indent")
            target_indexes.append(index)
            role_resources[role] = match.group("res")
            role_slots[role] = slot

        if not target_indexes or not role_resources:
            continue

        first = min(target_indexes)
        replacement = make_rabbitfx_lines(first_indent, role_resources)
        if comment_originals:
            replacement.extend(";" + lines[index] for index in target_indexes)

        for index in sorted(target_indexes, reverse=True):
            del output[index]

        insert_at = first
        for line in reversed(replacement):
            output.insert(insert_at, line)

        conversions.append(
            Conversion(
                section=section.name,
                slots=sorted(role_slots.values()),
                roles=[role for role in RABBITFX_ROLES if role in role_resources],
            )
        )

    if not conversions:
        return content, []

    new_content = newline.join(output)
    if had_final_newline:
        new_content += newline
    return new_content, list(reversed(conversions))


def is_disabled_path(path: Path) -> bool:
    return any(part.upper().startswith("DISABLED") for part in path.parts)


def iter_ini_files(target: Path, include_backups: bool, include_disabled: bool) -> list[Path]:
    if target.is_file():
        if not include_disabled and is_disabled_path(target):
            return []
        return [target] if target.suffix.lower() == ".ini" or include_backups else [target]

    files: list[Path] = []
    for path in target.rglob("*.ini"):
        if not path.is_file():
            continue
        if not include_backups and BACKUP_RE.search(path.name):
            continue
        if not include_disabled and is_disabled_path(path.relative_to(target)):
            continue
        files.append(path)
    return sorted(files, key=lambda p: str(p).lower())


def backup_file(path: Path, stamp: str) -> Path:
    backup = path.with_name(path.name + BACKUP_TOKEN + stamp)
    backup.write_bytes(path.read_bytes())
    return backup


def process_file(
    path: Path,
    slots: set[int] | None,
    comment_originals: bool,
    force: bool,
    dry_run: bool,
    stamp: str,
) -> FileResult:
    content, encoding = read_ini(path)
    new_content, conversions = convert_content(
        content=content,
        slots=slots,
        comment_originals=comment_originals,
        force=force,
    )
    changed = new_content != content
    if changed and not dry_run:
        backup_file(path, stamp)
        write_ini(path, new_content, encoding)
    return FileResult(path=path, changed=changed, conversions=conversions)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=f"Convert ps-t {RABBITFX_KEYWORDS} bindings to RabbitFX SetTextures entries.",
    )
    parser.add_argument("target", help="INI file or mod directory to scan.")
    parser.add_argument(
        "--slots",
        type=parse_slots,
        default=None,
        help=f"Optional comma-separated ps-t slot numbers to limit conversion. Default: convert any slot with {RABBITFX_KEYWORDS}.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing files.")
    parser.add_argument("--force", action="store_true", help="Convert sections even if RabbitFX entries already exist.")
    parser.add_argument("--include-backups", action="store_true", help="Include backup-looking files when scanning a directory.")
    parser.add_argument("--include-disabled", action="store_true", help="Also process paths whose folder name starts with DISABLED.")
    parser.add_argument(
        "--delete-originals",
        action="store_true",
        help="Delete converted ps-t lines instead of commenting them out.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    target = Path(args.target)
    if not target.exists():
        print(f"Target not found: {target}", file=sys.stderr)
        return 2

    files = iter_ini_files(target, include_backups=args.include_backups, include_disabled=args.include_disabled)
    if not files:
        print("No INI files found.")
        return 0

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    changed_count = 0
    for path in files:
        result = process_file(
            path=path,
            slots=args.slots,
            comment_originals=not args.delete_originals,
            force=args.force,
            dry_run=args.dry_run,
            stamp=stamp,
        )
        if not result.changed:
            continue

        changed_count += 1
        prefix = "[DRY-RUN]" if args.dry_run else "[UPDATED]"
        print(f"{prefix} {path}")
        for conversion in result.conversions:
            slots = ",".join(f"ps-t{slot}" for slot in conversion.slots)
            roles = ",".join(conversion.roles)
            print(f"  - {conversion.section}: {slots} -> RabbitFX {roles}")

    if changed_count == 0:
        print(f"No {RABBITFX_KEYWORDS} ps-t bindings found. Skipped.")
    elif args.dry_run:
        print(f"Dry run complete. {changed_count} file(s) would be changed.")
    else:
        print(f"Done. {changed_count} file(s) changed. Backups use suffix {BACKUP_TOKEN}{stamp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
