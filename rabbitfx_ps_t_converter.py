from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

RABBITFX_SET_TEXTURES_RUN = r"CommandList\RabbitFX\SetTextures"
RABBITFX_EFFECTS_RUN = r"CommandList\RabbitFX\Run"
RABBITFX_MAPS = (
    ("DiffuseMap", "Diffuse"),
    ("LightMap", "Lightmap"),
    ("NormalMap", "Normalmap"),
    ("DiscardMap", "DiscardMap"),
    ("RainMap", "Rainmap"),
    ("GlowMap", "GlowMap"),
    ("FXMap", "FXMap"),
)
RABBITFX_ROLES = tuple(role for _, role in RABBITFX_MAPS)
RABBITFX_SET_TEXTURE_ROLES = ("Diffuse", "Lightmap", "Normalmap", "DiscardMap", "Rainmap")
RABBITFX_EFFECT_ROLES = ("GlowMap", "FXMap")
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
COMMENTED_PS_T_RE = re.compile(
    r"^(?P<indent>\s*);(?P<body>\s*ps-t\d+\s*=.*)$",
    re.IGNORECASE,
)
RABBITFX_RE = re.compile(
    r"^\s*Resource\\RabbitFX\\|^\s*run\s*=\s*CommandList\\RabbitFX\\(?:SetTextures|Run)",
    re.IGNORECASE,
)


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
    action: str
    slot_offset: int = 0


@dataclass
class TextureBinding:
    index: int
    slot: int
    role: str
    resource: str
    comment_line: str
    commented: bool = False


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


def parse_slot_offset(raw: str) -> int:
    try:
        value = int(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid slot offset: {raw!r}") from exc
    if value < -2 or value > 2:
        raise argparse.ArgumentTypeError("slot offset must be one of -2, -1, 0, 1, 2")
    return value


def infer_role(resource: str) -> str | None:
    lowered = resource.lower()
    if "highlight" in lowered:
        return None

    flexible_roles = (
        ("discard", "DiscardMap"),
        ("rain", "Rainmap"),
        ("glow", "GlowMap"),
        ("fxmap", "FXMap"),
        ("fx_map", "FXMap"),
        ("fx-map", "FXMap"),
        ("diffuse", "Diffuse"),
        ("light", "Lightmap"),
        ("normal", "Normalmap"),
    )
    for token, role in flexible_roles:
        if token in lowered:
            return role

    for pattern, role in RABBITFX_PATTERNS:
        if pattern.search(resource):
            return role
    return None


def unique_role_resources(
    bindings: list[TextureBinding],
    roles: tuple[str, ...],
    merge_same: bool = True,
) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for role in roles:
        for binding in bindings:
            pair = (binding.role, binding.resource)
            if binding.role != role:
                continue
            if merge_same and pair in seen:
                continue
            seen.add(pair)
            pairs.append(pair)
    return pairs


def make_rabbitfx_group_lines(
    indent: str,
    bindings: list[TextureBinding],
    roles: tuple[str, ...],
    run_command: str,
    merge_same: bool = True,
) -> list[str]:
    lines: list[str] = []
    for role, resource in unique_role_resources(bindings, roles, merge_same=merge_same):
        lines.append(f"{indent}Resource\\RabbitFX\\{role} = ref {resource}")
    if lines:
        lines.append(f"{indent}run = {run_command}")
    return lines


def make_rabbitfx_lines(indent: str, bindings: list[TextureBinding], merge_same: bool = True) -> list[str]:
    lines: list[str] = []
    lines.extend(
        make_rabbitfx_group_lines(
            indent,
            bindings,
            RABBITFX_SET_TEXTURE_ROLES,
            RABBITFX_SET_TEXTURES_RUN,
            merge_same=merge_same,
        )
    )
    lines.extend(
        make_rabbitfx_group_lines(
            indent,
            bindings,
            RABBITFX_EFFECT_ROLES,
            RABBITFX_EFFECTS_RUN,
            merge_same=merge_same,
        )
    )
    return lines


def uncomment_generated_ps_t_line(line: str) -> str | None:
    match = COMMENTED_PS_T_RE.match(line)
    if not match:
        return None
    return f"{match.group('indent')}{match.group('body').lstrip()}"


def parse_texture_binding(
    index: int,
    line: str,
    slots: set[int] | None,
    slot_offset: int,
    commented: bool = False,
) -> TextureBinding | None:
    source_line = uncomment_generated_ps_t_line(line) if commented else line
    if source_line is None or "CheckTextureOverride" in source_line:
        return None

    match = PS_T_RE.match(source_line)
    if not match:
        return None

    slot = int(match.group("slot"))
    if slots is not None and slot not in slots:
        return None

    role = infer_role(match.group("res"))
    if not role:
        return None

    if commented:
        comment_line = source_line
        effective_slot = slot
    else:
        comment_line, effective_slot = offset_ps_t_line(source_line, slot_offset)
    if effective_slot is None:
        return None

    return TextureBinding(
        index=index,
        slot=effective_slot,
        role=role,
        resource=match.group("res"),
        comment_line=comment_line,
        commented=commented,
    )


def offset_label(offset: int) -> str:
    return f"{offset:+d}"


def has_cross_ib(content: str) -> bool:
    return bool(re.search(r"CustomShader_ExtractCB1|cross\s*[-_ ]?\s*ib", content, flags=re.IGNORECASE))


def section_has_conditional_texture_bindings(lines: list[str]) -> bool:
    depth = 0
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith(";"):
            continue

        keyword = stripped.split(None, 1)[0].lower()
        if keyword == "endif":
            depth = max(0, depth - 1)

        match = PS_T_RE.match(line)
        if match and depth > 0 and int(match.group("slot")) >= 2 and infer_role(match.group("res")):
            return True

        if keyword == "if":
            depth += 1

    return False


def offset_ps_t_line(line: str, offset: int) -> tuple[str, int | None]:
    match = PS_T_RE.match(line)
    if not match:
        return line, None

    slot = int(match.group("slot"))
    shifted_slot = slot + offset
    if shifted_slot < 0:
        return line, None

    shifted = (
        f"{match.group('indent')}ps-t{shifted_slot}"
        f"{match.group('eq')}{match.group('res')}{match.group('tail')}"
    )
    return shifted, shifted_slot


def shift_ps_t_line(line: str, slots: set[int] | None, offset: int = 2) -> tuple[str, int | None, str | None]:
    stripped = line.lstrip()
    if stripped.startswith(";") or "CheckTextureOverride" in line:
        return line, None, None

    match = PS_T_RE.match(line)
    if not match:
        return line, None, None

    slot = int(match.group("slot"))
    if slot < 2 or (slots is not None and slot not in slots):
        return line, None, None

    role = infer_role(match.group("res"))
    if not role:
        return line, None, None

    shifted, shifted_slot = offset_ps_t_line(line, offset)
    if shifted_slot is None or shifted == line:
        return line, None, None
    return shifted, slot, role


def convert_content(
    content: str,
    slots: set[int] | None,
    comment_originals: bool,
    force: bool,
    strategy: str = "auto",
    slot_offset: int = 0,
    merge_same: bool = True,
) -> tuple[str, list[Conversion]]:
    lines = content.splitlines()
    had_final_newline = content.endswith(("\n", "\r"))
    newline = detect_newline(content)
    output = list(lines)
    conversions: list[Conversion] = []
    cross_ib = has_cross_ib(content)

    for section in reversed(collect_sections(lines)):
        section_lines = output[section.start:section.end]
        section_strategy = strategy
        if strategy == "auto":
            section_strategy = "shift" if cross_ib or section_has_conditional_texture_bindings(section_lines) else "rabbitfx"

        if section_strategy == "shift":
            shifted_slots: list[int] = []
            shifted_roles: set[str] = set()
            for index in range(section.start + 1, section.end):
                new_line, slot, role = shift_ps_t_line(output[index], slots)
                if slot is None or role is None:
                    continue
                output[index] = new_line
                shifted_slots.append(slot)
                shifted_roles.add(role)

            if shifted_slots:
                conversions.append(
                    Conversion(
                        section=section.name,
                        slots=sorted(set(shifted_slots)),
                        roles=[role for role in RABBITFX_ROLES if role in shifted_roles],
                        action="shift+2",
                    )
                )
            continue

        active_rabbitfx_indexes = [
            index
            for index in range(section.start + 1, section.end)
            if RABBITFX_RE.search(output[index]) and not output[index].lstrip().startswith(";")
        ]
        active_bindings: list[TextureBinding] = []
        commented_bindings: list[TextureBinding] = []
        first_indent = ""

        for index in range(section.start + 1, section.end):
            line = output[index]
            stripped = line.lstrip()
            if "CheckTextureOverride" in line:
                continue

            if stripped.startswith(";"):
                if active_rabbitfx_indexes:
                    binding = parse_texture_binding(index, line, slots, slot_offset, commented=True)
                    if binding is not None:
                        commented_bindings.append(binding)
                        if not first_indent:
                            first_indent = uncomment_generated_ps_t_line(line) or ""
                            first_indent = PS_T_RE.match(first_indent).group("indent") if PS_T_RE.match(first_indent) else ""
                continue

            binding = parse_texture_binding(index, line, slots, slot_offset, commented=False)
            if binding is not None:
                active_bindings.append(binding)
                if not first_indent:
                    first_indent = PS_T_RE.match(line).group("indent") if PS_T_RE.match(line) else ""

        restore_from_generated_comments = bool(active_rabbitfx_indexes and commented_bindings)
        if active_rabbitfx_indexes and not restore_from_generated_comments and not force:
            continue

        bindings = commented_bindings if restore_from_generated_comments else active_bindings
        if not bindings:
            continue

        target_indexes = [binding.index for binding in bindings]
        if restore_from_generated_comments:
            target_indexes.extend(active_rabbitfx_indexes)

        first = min(target_indexes)
        replacement = make_rabbitfx_lines(first_indent, bindings, merge_same=merge_same)
        if not replacement:
            continue
        if comment_originals:
            replacement.extend(";" + binding.comment_line for binding in bindings)

        for index in sorted(target_indexes, reverse=True):
            del output[index]

        insert_at = first
        for line in reversed(replacement):
            output.insert(insert_at, line)

        conversions.append(
            Conversion(
                section=section.name,
                slots=sorted({binding.slot for binding in bindings}),
                roles=[role for role in RABBITFX_ROLES if any(binding.role == role for binding in bindings)],
                action="rabbitfx",
                slot_offset=slot_offset,
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
    strategy: str,
    slot_offset: int,
    merge_same: bool,
    dry_run: bool,
    stamp: str,
) -> FileResult:
    content, encoding = read_ini(path)
    new_content, conversions = convert_content(
        content=content,
        slots=slots,
        comment_originals=comment_originals,
        force=force,
        strategy=strategy,
        slot_offset=slot_offset,
        merge_same=merge_same,
    )
    changed = new_content != content
    if changed and not dry_run:
        backup_file(path, stamp)
        write_ini(path, new_content, encoding)
    return FileResult(path=path, changed=changed, conversions=conversions)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=f"Directly fix ps-t {RABBITFX_KEYWORDS} bindings without running Endfield_mod_fixer.py first.",
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
    parser.add_argument(
        "--strategy",
        choices=("auto", "rabbitfx", "shift"),
        default="auto",
        help="Fix strategy. auto uses +2 shift for cross-IB/conditional sections and RabbitFX otherwise.",
    )
    parser.add_argument(
        "--slot-offset",
        type=parse_slot_offset,
        default=0,
        help="RabbitFX mode ps-t slot offset before replacement. Valid values: -2, -1, 0, 1, 2. Default: 0.",
    )
    parser.add_argument(
        "--no-merge-same-resources",
        action="store_true",
        help="Keep repeated RabbitFX role/resource entries instead of merging exact duplicates. SetTextures still emits one run line.",
    )
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
            strategy=args.strategy,
            slot_offset=args.slot_offset,
            merge_same=not args.no_merge_same_resources,
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
            if conversion.action == "shift+2":
                print(f"  - {conversion.section}: {slots} shifted +2 ({roles})")
            else:
                offset = f" offset {offset_label(conversion.slot_offset)}" if conversion.slot_offset else ""
                print(f"  - {conversion.section}: {slots} -> RabbitFX {roles}{offset}")

    if changed_count == 0:
        print("No files changed. Skipped.")
    elif args.dry_run:
        print(f"Dry run complete. {changed_count} file(s) would be changed.")
    else:
        print(f"Done. {changed_count} file(s) changed. Backups use suffix {BACKUP_TOKEN}{stamp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
