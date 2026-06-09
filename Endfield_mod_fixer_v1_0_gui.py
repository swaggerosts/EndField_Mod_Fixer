#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import contextlib
import ctypes
import hashlib
import io
import json
import locale
import math
import os
import queue
import re
import sys
import threading
import time
import traceback
import urllib.error
import urllib.request
from pathlib import Path
from tkinter import filedialog, messagebox
from tkinter import font as tkfont
import tkinter as tk

try:
    from PIL import Image, ImageEnhance, ImageOps, ImageTk
except ImportError:
    Image = ImageEnhance = ImageOps = ImageTk = None  # type: ignore[assignment]

import Endfield_mod_fixer_v1_0 as fixer
import rabbitfx_ps_t_converter as stable_texture_converter

APP_VERSION = "1.3.0"
APP_TITLE = "Endfield mods fixer v1.3"
APP_FONT_FAMILY = "猫啃什锦黑"
APP_FONT_FILE = Path("MaoKenShiJinHei") / "MaoKenShiJinHei-2.ttf"
UI_FONT_FAMILY = APP_FONT_FAMILY
SYMBOL_FONT_FAMILY = "Segoe UI Symbol"
LOG_FONT_FAMILY = APP_FONT_FAMILY
FONT_FALLBACK_FAMILY = "Microsoft YaHei UI"
PANEL_RADIUS = 8
SELECTED_LIGHTNESS_DELTA = 0
UI_TITLE_FONT_SIZE = 16
UI_SECTION_FONT_SIZE = 14
UI_BODY_FONT_SIZE = 14
UI_SMALL_FONT_SIZE = 13
MIN_WINDOW_WIDTH = 1260
DEFAULT_WINDOW_WIDTH = 1324
MIN_COLLAPSED_WINDOW_HEIGHT = 620
COLLAPSED_BOTTOM_PADDING = 8
EXPANDED_WINDOW_HEIGHT = 770
DEFAULT_LOG_AREA_HEIGHT = 220
LOG_AREA_TOP_GAP = 8
LANGUAGE_FADE_FRAMES = 9
LANGUAGE_FADE_INTERVAL_MS = 16
LANGUAGE_FADE_PANEL_TARGET = 0.92
CONTOUR_REDRAW_DELAY_MS = 180
PANEL_REDRAW_DELAY_MS = 32
LOG_ANIMATION_DURATION_MS = 220
LOG_ANIMATION_INTERVAL_MS = 4
LOG_ANIMATION_TIMER_RESOLUTION_MS = 1
LOG_ANIMATION_SLIDE_OFFSET = 28
ROOT_RESIZE_SYNC_DELAY_MS = 45
CONTOUR_TOP_OFFSET = 42
CONTOUR_SOURCE_IMAGE_NAME = "\u65e0\u7f1d\u5730\u5f62\u7b49\u9ad8\u7ebf_\u7231\u7ed9\u7f51_aigei_com.png"
PRIMARY_UPDATE_MANIFEST_URL = ""
SECONDARY_UPDATE_REPO = ""
SECONDARY_UPDATE_API = ""
UPDATE_REQUEST_TIMEOUT = 15
UPDATE_CHECK_DELAY_MS = 1400
UPDATE_ASSET_SUFFIXES = (".exe", ".zip", ".7z", ".rar")


def app_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


APP_DIR = app_base_dir()
UPDATE_DIR = APP_DIR / "updates"
APP_ICON_NAME = "favicon.ico"
STRIP_CYAN = "#00ffff"
STRIP_MAGENTA = "#ff00ff"
STRIP_YELLOW = "#ffff00"
ROLLBACK_CYAN = "#0aebeb"
ROLLBACK_MAGENTA = "#eb0aeb"
ROLLBACK_YELLOW = "#ebeb0a"
ROLLBACK_BUTTON_TEXT = "#3F3F3D"
LOG_SWITCH_ON_YELLOW = "#e1e100"
LOG_SWITCH_KNOB_ON = "#252b30"
ROLLBACK_WINDOW_BASE_WIDTH = 760
ROLLBACK_WINDOW_BASE_HEIGHT = 430
FR_PRIVATE = 0x10
LOADED_FONT_PATHS: set[Path] = set()


def configure_process_dpi_awareness() -> None:
    if sys.platform != "win32":
        return

    with contextlib.suppress(AttributeError, OSError, ValueError):
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        return

    with contextlib.suppress(AttributeError, OSError, ValueError):
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        return

    with contextlib.suppress(AttributeError, OSError, ValueError):
        ctypes.windll.user32.SetProcessDPIAware()


def app_resource_path(name: str | Path) -> Path:
    name_path = Path(name)
    bundle_dir = getattr(sys, "_MEIPASS", None)
    if bundle_dir:
        bundled = Path(bundle_dir) / name_path
        if bundled.exists():
            return bundled

    app_local = APP_DIR / name_path
    if app_local.exists():
        return app_local

    cwd_local = Path.cwd() / name_path
    if cwd_local.exists():
        return cwd_local

    return app_local


def set_window_icon(window: tk.Toplevel) -> None:
    icon_path = app_resource_path(APP_ICON_NAME)
    if not icon_path.exists():
        return
    try:
        resolved_icon = str(icon_path.resolve())
        window.iconbitmap(resolved_icon)
        window.iconbitmap(default=resolved_icon)
    except tk.TclError:
        pass


def load_private_font() -> None:
    if sys.platform != "win32":
        return

    font_path = app_resource_path(APP_FONT_FILE)
    if not font_path.exists():
        return

    resolved = font_path.resolve()
    if resolved in LOADED_FONT_PATHS:
        return

    try:
        added_count = ctypes.windll.gdi32.AddFontResourceExW(str(resolved), FR_PRIVATE, None)
    except (AttributeError, OSError, ValueError):
        return

    if added_count:
        LOADED_FONT_PATHS.add(resolved)


def resolve_font_family(root: tk.Tk, preferred: str, fallback: str) -> str:
    with contextlib.suppress(tk.TclError):
        families = {family.lower(): family for family in tkfont.families(root)}
        if preferred.lower() in families:
            return families[preferred.lower()]
        if fallback.lower() in families:
            return families[fallback.lower()]
    return fallback


def configure_app_fonts(root: tk.Tk) -> None:
    global UI_FONT_FAMILY, LOG_FONT_FAMILY

    load_private_font()
    resolved_family = resolve_font_family(root, APP_FONT_FAMILY, FONT_FALLBACK_FAMILY)
    UI_FONT_FAMILY = resolved_family
    LOG_FONT_FAMILY = resolved_family
    for name in (
        "TkDefaultFont",
        "TkTextFont",
        "TkMenuFont",
        "TkHeadingFont",
        "TkCaptionFont",
        "TkSmallCaptionFont",
        "TkIconFont",
        "TkTooltipFont",
        "TkFixedFont",
    ):
        with contextlib.suppress(tk.TclError):
            tkfont.nametofont(name).configure(family=resolved_family)


THEMES = {
    "dark": {
        "bg": "#15191d",
        "panel": "#1b2024",
        "panel_2": "#252b30",
        "border": "#46515a",
        "text": "#f2f4ef",
        "muted": "#aab2b7",
        "blue": STRIP_YELLOW,
        "blue_dark": STRIP_YELLOW,
        "check_on": STRIP_YELLOW,
        "check_mark": "#ffffff",
        "green": STRIP_YELLOW,
        "green_dark": STRIP_YELLOW,
        "soft_button": "#22282d",
        "soft_button_active": "#303840",
        "log_bg": "#15191d",
        "log_text": "#ffffff",
        "switch_track": "#2b3136",
        "switch_knob": STRIP_YELLOW,
        "switch_text": "#f2f4ef",
        "accent": STRIP_YELLOW,
        "accent_dim": STRIP_YELLOW,
        "card": "#eeefeb",
        "card_2": "#d9dbd5",
        "card_text": "#2a2d2f",
        "card_muted": "#666b6f",
        "warning": "#e8c11a",
    },
    "light": {
        "bg": "#f3f4f8",
        "panel": "#ffffff",
        "panel_2": "#f8f9fb",
        "border": "#d8dce4",
        "text": "#2b3038",
        "muted": "#6f7785",
        "blue": "#58aee6",
        "blue_dark": "#3186bf",
        "check_on": "#6272f4",
        "check_mark": "#ffffff",
        "green": "#45cf76",
        "green_dark": "#31a95b",
        "soft_button": "#ffffff",
        "soft_button_active": "#e8ebf2",
        "log_bg": "#fbfcfe",
        "log_text": "#242933",
        "switch_track": "#ffffff",
        "switch_knob": "#f5c84b",
        "switch_text": "#2b3038",
    },
}


UI_COPY = {
    "zh": {
        "app_header": "EFMI 模组修复终端",
        "target_title": "目标文件夹",
        "target_sub": "",
        "choose_mod": "选择 Mod 文件夹",
        "target_hint": "将选择包含 .ini 文件的 Mod 目录",
        "repair_title": "修复选项",
        "repair_sub": "",
        "stable_texture": "稳定纹理",
        "stable_texture_desc": "把材质转换为Rabbitfx稳定纹理，修复后mod异常时可尝试启用，部分mod可用",
        "fix_menu": "修复菜单",
        "fix_menu_desc": "当菜单无法呼出时，修复菜单丢失问题",
        "task_title": "任务操作",
        "task_sub": "",
        "fix_title": "一键修复",
        "fix_tip": "执行完整扫描与修复\n开始全面修复流程",
        "fix_action": "执行",
        "preview_title": "预览扫描",
        "preview_tip": "仅扫描不修改文件\n检查问题与潜在修复项",
        "preview_action": "扫描",
        "rollback_title": "回滚管理",
        "rollback_tip": "查看与恢复备份\n管理备份与回滚",
        "rollback_action": "管理",
        "log_title": "▷ 诊断日志",
        "clear_log": "清空日志",
        "export_log": "导出日志",
        "check_update": "检查更新",
        "debug_log": "调试日志",
        "log_switch_on": "开",
        "log_switch_off": "关",
        "update_check_start": "检查更新开始",
        "update_download_start": "下载更新开始",
        "update_save_location": "保存位置",
        "update_current_message": "当前已是最新版本：v{version}",
        "update_current_log": "检查更新：当前版本 v{local}，最新版本 {remote}。",
        "update_no_file_log": "检查更新：发现新版本 {remote}，但暂时没有可下载文件。",
        "update_no_file_message": "发现新版本 {remote}，但暂时没有可下载文件。",
        "update_available_title": "发现新版本",
        "update_available_log": "检查更新：发现新版本。",
        "update_current_version": "当前版本",
        "update_remote_version": "云端版本",
        "update_file": "文件",
        "update_required": "强制更新",
        "update_notes": "更新说明",
        "yes": "是",
        "no": "否",
        "none": "无",
        "update_available_prompt": "发现新版本 {remote}。\n\n文件：{asset}\n\n更新说明：\n{notes}\n\n是否选择保存位置并下载？",
        "update_choose_save_title": "选择更新文件保存位置",
        "update_file_type": "更新文件",
        "overwrite_file_title": "覆盖文件",
        "overwrite_file_message": "文件已存在，是否覆盖？\n{path}",
        "update_cancel_save": "检查更新：用户取消选择保存位置。",
        "update_cancel_overwrite": "检查更新：用户取消覆盖已有文件。",
        "update_cancel_download": "检查更新：用户取消下载。",
        "update_downloaded_title": "更新已下载",
        "update_downloaded_log": "检查更新：发现新版本并已下载。",
        "update_version": "版本",
        "update_location": "位置",
        "update_downloaded_message": "新版本 {remote} 已下载到：\n{path}\n\n更新说明：\n{notes}",
        "update_unknown_status": "检查更新：收到未知更新状态。",
        "update_error_log": "检查更新失败：{message}",
        "update_error_title": "检查更新失败",
        "enabled": "启用",
        "disabled": "停用",
        "ready": "终端已就绪，等待操作指令...",
        "target_path": "目标路径",
        "repair_status": "修复选项",
        "click_start": "点击「预览扫描」或「一键修复」开始处理",
        "command_args": "命令参数",
        "stable_args": "稳定纹理参数",
        "stable_start": "稳定纹理开始",
        "stable_end": "稳定纹理结束，退出码",
        "fix_start": "一键修复开始",
        "preview_start": "预览扫描开始",
        "rollback_name": "回滚",
        "process_end": "结束，退出码",
        "fixer_skipped_newer": "已跳过 {count} 个较新版本文件。",
        "fixer_no_changes": "完成。无需修改。{skipped}",
        "fixer_dry_run_complete": "预览扫描完成。将修改/删除 {count} 个文件。{skipped} 未创建备份。",
        "fixer_run_complete": "完成。已修改 {modified} 个文件，已硬删除 {deleted} 个热修复文件。",
        "invalid_target_title": "目标文件夹无效",
        "invalid_target_msg": "请选择一个存在的 Mod 文件夹。",
        "export_done": "导出完成",
        "export_done_msg": "日志已导出到：",
        "text_files": "文本文件",
        "all_files": "所有文件",
        "rollback_window": "回滚管理",
        "backup_list": "-- 备份列表 --",
        "refresh_backups": "刷新备份",
        "restore_selected": "恢复选中版本",
        "restore_before": "恢复到修复前",
        "confirm_rollback": "确认回滚",
        "rollback_before_state": "修复前状态",
        "rollback_after_state": "修复后状态",
        "confirm_rollback_msg": "确定要恢复 {session_id} 的{mode}吗？当前状态会先自动保存为备份。",
    },
    "en": {
        "app_header": "EFMI MOD FIXER TERMINAL",
        "target_title": "Target Folder",
        "target_sub": "",
        "choose_mod": "Choose Mod Folder",
        "target_hint": "Choose the Mod directory containing .ini files",
        "repair_title": "Repair Options",
        "repair_sub": "",
        "stable_texture": "Stable Texture",
        "stable_texture_desc": "Convert materials to Rabbitfx stable textures. Try this when repaired mods behave abnormally.",
        "fix_menu": "Fix Menu",
        "fix_menu_desc": "Repair lost menu entries when the in-game menu cannot be opened.",
        "task_title": "Task Operations",
        "task_sub": "",
        "fix_title": "Auto Fix",
        "fix_tip": "Run a full scan and repair\nStart the complete repair workflow",
        "fix_action": "Run",
        "preview_title": "Preview Scan",
        "preview_tip": "Scan only and do not modify files\nCheck issues and possible repair items",
        "preview_action": "Scan",
        "rollback_title": "Rollback Manager",
        "rollback_tip": "View and restore backups\nManage backups and rollback",
        "rollback_action": "Manage",
        "log_title": "▷ Diagnostic Log",
        "clear_log": "Clear Log",
        "export_log": "Export Log",
        "check_update": "Check Update",
        "debug_log": "Debug Log",
        "log_switch_on": "ON",
        "log_switch_off": "OFF",
        "update_check_start": "Update Check Started",
        "update_download_start": "Update Download Started",
        "update_save_location": "Save location",
        "update_current_message": "You are already on the latest version: v{version}",
        "update_current_log": "Update check: current version v{local}, latest version {remote}.",
        "update_no_file_log": "Update check: version {remote} is available, but no downloadable file is available yet.",
        "update_no_file_message": "Version {remote} is available, but no downloadable file is available yet.",
        "update_available_title": "New Version Available",
        "update_available_log": "Update check: new version available.",
        "update_current_version": "Current version",
        "update_remote_version": "Remote version",
        "update_file": "File",
        "update_required": "Required update",
        "update_notes": "Release notes",
        "yes": "Yes",
        "no": "No",
        "none": "None",
        "update_available_prompt": "Version {remote} is available.\n\nFile: {asset}\n\nRelease notes:\n{notes}\n\nChoose a save location and download it?",
        "update_choose_save_title": "Choose Update File Save Location",
        "update_file_type": "Update file",
        "overwrite_file_title": "Overwrite File",
        "overwrite_file_message": "The file already exists. Overwrite it?\n{path}",
        "update_cancel_save": "Update check: save location selection canceled.",
        "update_cancel_overwrite": "Update check: overwrite canceled.",
        "update_cancel_download": "Update check: download canceled.",
        "update_downloaded_title": "Update Downloaded",
        "update_downloaded_log": "Update check: new version found and downloaded.",
        "update_version": "Version",
        "update_location": "Location",
        "update_downloaded_message": "Version {remote} has been downloaded to:\n{path}\n\nRelease notes:\n{notes}",
        "update_unknown_status": "Update check: received an unknown update status.",
        "update_error_log": "Update check failed: {message}",
        "update_error_title": "Update Check Failed",
        "enabled": "On",
        "disabled": "Off",
        "ready": "Terminal ready. Waiting for commands...",
        "target_path": "Target path",
        "repair_status": "Repair options",
        "click_start": "Click Preview Scan or One-click Fix to start",
        "command_args": "Command args",
        "stable_args": "Stable texture args",
        "stable_start": "Stable texture started",
        "stable_end": "Stable texture finished, exit code",
        "fix_start": "One-click Fix started",
        "preview_start": "Preview Scan started",
        "rollback_name": "Rollback",
        "process_end": "finished, exit code",
        "fixer_skipped_newer": "Skipped {count} newer-version file(s).",
        "fixer_no_changes": "Done. No changes needed.{skipped}",
        "fixer_dry_run_complete": "Preview scan complete. {count} file(s) would be modified/deleted.{skipped} No backup was created.",
        "fixer_run_complete": "Done. Modified {modified} file(s), hard-deleted {deleted} hotfix file(s).",
        "invalid_target_title": "Invalid Target Folder",
        "invalid_target_msg": "Please choose an existing Mod folder.",
        "export_done": "Export Complete",
        "export_done_msg": "Log exported to:",
        "text_files": "Text files",
        "all_files": "All files",
        "rollback_window": "Rollback Manager",
        "backup_list": "-- Backup List --",
        "refresh_backups": "Refresh Backups",
        "restore_selected": "Restore Selected",
        "restore_before": "Restore Before Fix",
        "confirm_rollback": "Confirm Rollback",
        "rollback_before_state": "before-fix state",
        "rollback_after_state": "after-fix state",
        "confirm_rollback_msg": "Restore {session_id} to the {mode}? The current state will be backed up first.",
    },
}


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    cleaned = value.strip().lstrip("#")
    return int(cleaned[0:2], 16), int(cleaned[2:4], 16), int(cleaned[4:6], 16)


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def mix_color(start: str, end: str, progress: float) -> str:
    progress = clamp01(progress)
    start_rgb = hex_to_rgb(start)
    end_rgb = hex_to_rgb(end)
    return rgb_to_hex(
        tuple(
            round(start_value + (end_value - start_value) * progress)
            for start_value, end_value in zip(start_rgb, end_rgb)
        )
    )


def adjust_color_lightness(value: str, delta: int) -> str:
    red, green, blue = hex_to_rgb(value)
    return rgb_to_hex(
        (
            max(0, min(255, red + delta)),
            max(0, min(255, green + delta)),
            max(0, min(255, blue + delta)),
        )
    )


def invert_color(value: str) -> str:
    red, green, blue = hex_to_rgb(value)
    return rgb_to_hex((255 - red, 255 - green, 255 - blue))


def mix_theme(start: dict[str, str], end: dict[str, str], progress: float) -> dict[str, str]:
    return {key: mix_color(start[key], end[key], progress) for key in start}


def ease_in_out(progress: float) -> float:
    progress = clamp01(progress)
    return progress * progress * (3 - 2 * progress)


def parse_version(value: str) -> tuple[int, ...]:
    parts = re.findall(r"\d+", value)
    if not parts:
        return (0,)
    return tuple(int(part) for part in parts[:4])


def remote_version_is_newer(local_version: str, remote_tag: str) -> bool:
    local = parse_version(local_version)
    remote = parse_version(remote_tag)
    length = max(len(local), len(remote))
    local += (0,) * (length - len(local))
    remote += (0,) * (length - len(remote))
    return remote > local


def system_region_is_china() -> bool:
    geo_names: list[str] = []

    if sys.platform == "win32":
        with contextlib.suppress(AttributeError, OSError, ValueError):
            buffer = ctypes.create_unicode_buffer(16)
            count = ctypes.windll.kernel32.GetUserDefaultGeoName(buffer, len(buffer))
            if count:
                geo_names.append(buffer.value)

    with contextlib.suppress(Exception):
        default_locale = locale.getdefaultlocale()[0]
        if default_locale:
            geo_names.append(default_locale)
    with contextlib.suppress(Exception):
        current_locale = locale.getlocale()[0]
        if current_locale:
            geo_names.append(current_locale)
    geo_names.extend(time.tzname)

    normalized = " ".join(str(value).upper().replace("-", "_") for value in geo_names)
    return any(token in normalized for token in ("_CN", "CN_", "ZH_CN", "CHINA", "中国"))


def ordered_update_sources() -> list[dict[str, str]]:
    sources = {
        "primary": {
            "name": "更新服务",
            "kind": "manifest",
            "url": PRIMARY_UPDATE_MANIFEST_URL,
        },
        "secondary_release": {
            "name": "更新服务",
            "kind": "secondary_release",
            "url": SECONDARY_UPDATE_API,
        },
    }

    override = os.environ.get("EFMI_UPDATE_SOURCE", "").strip().lower()
    if override == "primary":
        return [sources["primary"], sources["secondary_release"]]
    if override == "secondary":
        return [sources["secondary_release"], sources["primary"]]

    if system_region_is_china():
        return [sources["primary"], sources["secondary_release"]]
    return [sources["secondary_release"], sources["primary"]]


def update_request(url: str, api: bool = False) -> urllib.request.Request:
    headers = {"User-Agent": f"Endfield-Mod-Fixer/{APP_VERSION}"}
    if api:
        headers["Accept"] = "application/vnd.github+json"
    elif url == PRIMARY_UPDATE_MANIFEST_URL:
        headers["Accept"] = "application/json"
    return urllib.request.Request(
        url,
        headers=headers,
    )


def system_proxy_opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(urllib.request.ProxyHandler())


def open_update_url(url: str, api: bool = False) -> object:
    return system_proxy_opener().open(update_request(url, api=api), timeout=UPDATE_REQUEST_TIMEOUT)


def fetch_json_url(url: str, api: bool = False) -> dict[str, object]:
    with open_update_url(url, api=api) as response:
        data = response.read().decode("utf-8")
    payload = json.loads(data)
    if not isinstance(payload, dict):
        raise RuntimeError("更新数据不是有效的 JSON 对象。")
    return payload


def latest_update_info(manifest: dict[str, object]) -> dict[str, object]:
    latest = manifest.get("latest")
    if isinstance(latest, dict):
        return latest
    return manifest


def manifest_update_info(url: str, source_name: str) -> dict[str, object]:
    manifest = fetch_json_url(url)
    info = latest_update_info(manifest)
    remote_tag = str(info.get("version") or "").strip()
    if not remote_tag:
        raise RuntimeError("更新清单缺少 version。")

    download_url = str(info.get("download_url") or "").strip()
    return {
        "source": source_name,
        "source_url": url,
        "remote_tag": remote_tag,
        "asset_name": str(info.get("file_name") or Path(download_url).name or "release_asset"),
        "download_url": download_url,
        "sha256": str(info.get("sha256") or ""),
        "required": bool(info.get("required") or False),
        "release_notes": info.get("release_notes") if isinstance(info.get("release_notes"), list) else [],
    }


def choose_secondary_release_asset(release: dict[str, object]) -> dict[str, object] | None:
    assets = release.get("assets")
    if not isinstance(assets, list):
        return None

    valid_assets = [
        asset
        for asset in assets
        if isinstance(asset, dict) and asset.get("browser_download_url") and asset.get("name")
    ]
    preferred = [
        asset
        for asset in valid_assets
        if str(asset.get("name", "")).lower().endswith(UPDATE_ASSET_SUFFIXES)
    ]
    return (preferred or valid_assets)[0] if valid_assets else None


def release_asset_sha256(asset: dict[str, object]) -> str:
    digest = str(asset.get("digest") or "").strip()
    if digest.lower().startswith("sha256:"):
        return digest.split(":", 1)[1].strip()
    return ""


def release_notes_from_body(body: object) -> list[str]:
    text = str(body or "").strip()
    if not text:
        return []
    lines = [line.strip(" -\t") for line in text.splitlines() if line.strip(" -\t")]
    return lines[:8] if lines else [text]


def secondary_update_info(url: str, source_name: str) -> dict[str, object]:
    release = fetch_json_url(url, api=True)
    remote_tag = str(release.get("tag_name") or "").strip()
    if not remote_tag:
        raise RuntimeError("更新数据缺少版本号。")

    asset = choose_secondary_release_asset(release)
    download_url = str(asset.get("browser_download_url") or "").strip() if asset else ""
    return {
        "source": source_name,
        "source_url": str(release.get("html_url") or url),
        "remote_tag": remote_tag,
        "asset_name": str(asset.get("name") or "release_asset") if asset else "",
        "download_url": download_url,
        "sha256": release_asset_sha256(asset) if asset else "",
        "required": False,
        "release_notes": release_notes_from_body(release.get("body")),
    }


def fetch_update_info_from_source(source: dict[str, str]) -> dict[str, object]:
    if source["kind"] == "manifest":
        return manifest_update_info(source["url"], source["name"])
    if source["kind"] == "secondary_release":
        return secondary_update_info(source["url"], source["name"])
    raise RuntimeError("未知更新服务配置。")


def sanitize_update_error_message(message: str) -> str:
    cleaned = re.sub(r"https?://[^\s)）]+", "[更新地址已隐藏]", str(message))
    replacements = {
        "Release Service": "更新服务",
        "Publish Service": "更新服务",
        "secondary": "更新服务",
        "云端服务": "更新服务",
        "CloudProvider": "更新服务",
        "primary": "更新服务",
        "cloud.example": "更新服务",
        "publish.example": "更新服务",
        "publish-api.example": "更新服务",
    }
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)
    return cleaned


def safe_download_name(name: str) -> str:
    base_name = Path(name).name.strip() or "release_asset"
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", base_name)


def unique_download_path(directory: Path, filename: str) -> Path:
    candidate = directory / filename
    if not candidate.exists():
        return candidate
    stem = candidate.stem
    suffix = candidate.suffix
    counter = 1
    while True:
        next_candidate = directory / f"{stem}_{counter}{suffix}"
        if not next_candidate.exists():
            return next_candidate
        counter += 1


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def temp_download_path(destination: Path) -> Path:
    candidate = destination.with_name(f"{destination.name}.download")
    if not candidate.exists():
        return candidate

    counter = 1
    while True:
        next_candidate = destination.with_name(f"{destination.name}.{counter}.download")
        if not next_candidate.exists():
            return next_candidate
        counter += 1


def download_update_file(info: dict[str, object], destination_path: str | Path | None = None) -> Path:
    url = str(info.get("download_url") or "").strip()
    if not url:
        raise RuntimeError("更新清单缺少 download_url。")

    filename = safe_download_name(str(info.get("file_name") or Path(url).name or "release_asset"))
    if destination_path is None:
        UPDATE_DIR.mkdir(parents=True, exist_ok=True)
        destination = unique_download_path(UPDATE_DIR, filename)
    else:
        destination = Path(destination_path)
        destination.parent.mkdir(parents=True, exist_ok=True)

    temporary = temp_download_path(destination)

    with open_update_url(url) as response:
        with temporary.open("wb") as output:
            while True:
                chunk = response.read(1024 * 256)
                if not chunk:
                    break
                output.write(chunk)

    expected_sha256 = str(info.get("sha256") or "").strip().lower()
    if expected_sha256:
        actual_sha256 = file_sha256(temporary)
        if actual_sha256.lower() != expected_sha256:
            with contextlib.suppress(OSError):
                temporary.unlink()
            raise RuntimeError(
                "更新文件校验失败，下载内容可能已损坏。\n"
                f"期望：{expected_sha256}\n"
                f"实际：{actual_sha256}"
            )

    temporary.replace(destination)
    return destination


def check_and_download_update() -> dict[str, object]:
    errors: list[str] = []
    selected_info: dict[str, object] | None = None
    for source in ordered_update_sources():
        try:
            selected_info = fetch_update_info_from_source(source)
            break
        except Exception as exc:
            errors.append(sanitize_update_error_message(str(exc)))

    if selected_info is None:
        detail = "\n".join(f"- {error}" for error in errors if error)
        if detail:
            raise RuntimeError("暂时无法连接更新服务，请稍后再试。\n\n详细信息：\n" + detail)
        raise RuntimeError("暂时无法连接更新服务，请稍后再试。")

    remote_tag = str(selected_info.get("remote_tag") or "").strip()

    if not remote_version_is_newer(APP_VERSION, remote_tag):
        return {
            "status": "current",
            "remote_tag": remote_tag,
            "source": str(selected_info.get("source") or ""),
        }

    download_url = str(selected_info.get("download_url") or "").strip()
    if not download_url:
        return {
            "status": "no_file",
            "remote_tag": remote_tag,
            "source": str(selected_info.get("source") or ""),
            "source_url": str(selected_info.get("source_url") or ""),
        }

    return {
        "status": "available",
        "remote_tag": remote_tag,
        "source": str(selected_info.get("source") or ""),
        "source_url": str(selected_info.get("source_url") or ""),
        "asset_name": str(selected_info.get("asset_name") or Path(download_url).name or "release_asset"),
        "download_url": download_url,
        "sha256": str(selected_info.get("sha256") or ""),
        "required": bool(selected_info.get("required") or False),
        "release_notes": selected_info.get("release_notes") if isinstance(selected_info.get("release_notes"), list) else [],
    }


def download_update_from_result(result: dict[str, object], destination_path: str | Path | None = None) -> dict[str, object]:
    info = {
        "download_url": str(result.get("download_url") or ""),
        "file_name": str(result.get("asset_name") or ""),
        "sha256": str(result.get("sha256") or ""),
    }
    downloaded_path = download_update_file(info, destination_path=destination_path)
    return {
        **result,
        "status": "downloaded",
        "downloaded_path": str(downloaded_path),
    }


def default_target_dir() -> Path:
    seen: set[Path] = set()

    for base in (APP_DIR, Path.cwd().resolve()):
        for current in (base, *base.parents):
            if current in seen:
                continue
            seen.add(current)

            if current.name.lower() == "mods":
                return current

            sibling_mods = current / "Mods"
            if sibling_mods.is_dir():
                return sibling_mods

            efmi_mods = current / "EFMI" / "Mods"
            if efmi_mods.is_dir():
                return efmi_mods

            if current.parent.name == "修复工具" and current.parent.parent.name.lower() == "mods":
                return current.parent.parent

    return APP_DIR


def round_rect(canvas: tk.Canvas, x1: int, y1: int, x2: int, y2: int, radius: int, **kwargs: object) -> int:
    radius = max(0, min(radius, (x2 - x1) // 2, (y2 - y1) // 2))
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, splinesteps=24, **kwargs)


def draw_capsule(
    canvas: tk.Canvas,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    fill: str,
    outline: str,
    width: int = 1,
) -> None:
    radius = (y2 - y1) // 2
    canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=fill, outline="")
    canvas.create_oval(x1, y1, x1 + radius * 2, y2, fill=fill, outline="")
    canvas.create_oval(x2 - radius * 2, y1, x2, y2, fill=fill, outline="")
    canvas.create_arc(x1, y1, x1 + radius * 2, y2, start=90, extent=180, style=tk.ARC, outline=outline, width=width)
    canvas.create_arc(x2 - radius * 2, y1, x2, y2, start=-90, extent=180, style=tk.ARC, outline=outline, width=width)
    canvas.create_line(x1 + radius, y1, x2 - radius, y1, fill=outline, width=width)
    canvas.create_line(x1 + radius, y2, x2 - radius, y2, fill=outline, width=width)


def draw_uniform_contours(
    canvas: tk.Canvas,
    width: int,
    height: int,
    colors: dict[str, str],
    phase_offset: int = 0,
    density: float = 1.0,
    origin_x: int = 0,
    origin_y: int = 0,
    tag: str = "contours",
) -> None:
    canvas.delete(tag)
    width = max(1, width)
    height = max(1, height)
    canvas.create_rectangle(0, 0, width, height, fill=colors["bg"], outline="", tags=tag)

    density = max(0.55, density)
    cell = max(78, int(150 / density))
    ring_gap = max(9.0, cell * 0.075)
    steps = 52
    thin_line = mix_color(colors["bg"], colors["muted"], 0.24)
    normal_line = mix_color(colors["bg"], colors["border"], 0.48)
    bold_line = mix_color(colors["bg"], colors["muted"], 0.42)
    palette = [normal_line, thin_line, normal_line, thin_line, bold_line]

    def noise(ix: int, iy: int, salt: int) -> float:
        value = math.sin(ix * 12.9898 + iy * 78.233 + salt * 37.719 + phase_offset * 0.173) * 43758.5453
        return value - math.floor(value)

    start_gx = math.floor(origin_x / cell) - 1
    end_gx = math.ceil((origin_x + width) / cell) + 1
    start_gy = math.floor(origin_y / cell) - 1
    end_gy = math.ceil((origin_y + height) / cell) + 1
    for gy in range(start_gy, end_gy + 1):
        for gx in range(start_gx, end_gx + 1):
            jitter_x = (noise(gx, gy, 1) - 0.5) * cell * 0.56
            jitter_y = (noise(gx, gy, 2) - 0.5) * cell * 0.56
            cx = gx * cell + cell * 0.5 + jitter_x - origin_x
            cy = gy * cell + cell * 0.5 + jitter_y - origin_y
            outer_radius = cell * (0.31 + noise(gx, gy, 3) * 0.22)
            ring_count = 2 + int(noise(gx, gy, 4) * 5)
            aspect = 0.58 + noise(gx, gy, 5) * 1.08
            max_extent = outer_radius * max(aspect, 1 / max(0.42, aspect)) * 1.18
            if cx + max_extent < -24 or cx - max_extent > width + 24 or cy + max_extent < -24 or cy - max_extent > height + 24:
                continue
            rotation = noise(gx, gy, 6) * math.tau
            phase_a = noise(gx, gy, 7) * math.tau
            phase_b = noise(gx, gy, 8) * math.tau
            draw_small_island = noise(gx, gy, 11) > 0.72

            for ring in range(ring_count):
                radius = outer_radius - ring * ring_gap
                if radius < 9:
                    continue
                wobble = radius * (0.08 + noise(gx, gy, 20 + ring) * 0.06)
                rx = radius * aspect
                ry = radius / max(0.42, aspect)
                cos_rot = math.cos(rotation)
                sin_rot = math.sin(rotation)
                points: list[float] = []
                for step in range(steps + 1):
                    angle = math.tau * step / steps
                    contour_noise = (
                        math.sin(angle * 3 + phase_a) * wobble
                        + math.sin(angle * 5 + phase_b) * wobble * 0.52
                        + math.sin(angle * 9 + phase_a * 0.7) * wobble * 0.22
                    )
                    local_rx = max(4.0, rx + contour_noise)
                    local_ry = max(4.0, ry + contour_noise * 0.72)
                    local_x = math.cos(angle) * local_rx
                    local_y = math.sin(angle) * local_ry
                    x = cx + local_x * cos_rot - local_y * sin_rot
                    y = cy + local_x * sin_rot + local_y * cos_rot
                    points.extend((x, y))
                line_width = 2 if ring == 0 and noise(gx, gy, 30) > 0.55 else 1
                canvas.create_line(
                    points,
                    fill=palette[(gx + gy + ring) % len(palette)],
                    width=line_width,
                    smooth=True,
                    splinesteps=8,
                    tags=tag,
                )

            if draw_small_island:
                island_radius = max(8.0, outer_radius * (0.18 + noise(gx, gy, 12) * 0.12))
                island_x = cx + (noise(gx, gy, 13) - 0.5) * outer_radius * 1.3
                island_y = cy + (noise(gx, gy, 14) - 0.5) * outer_radius * 1.3
                points = []
                for step in range(steps + 1):
                    angle = math.tau * step / steps
                    radius = island_radius + math.sin(angle * 4 + phase_b) * island_radius * 0.18
                    points.extend((island_x + math.cos(angle) * radius, island_y + math.sin(angle) * radius * 0.78))
                canvas.create_line(points, fill=normal_line, width=1, smooth=True, splinesteps=8, tags=tag)


class QueueWriter(io.TextIOBase):
    def __init__(self, output_queue: queue.Queue[object]) -> None:
        self.output_queue = output_queue

    def write(self, text: str) -> int:
        if text:
            self.output_queue.put(text)
        return len(text)

    def flush(self) -> None:
        pass


class RoundedPanel(tk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        colors: dict[str, str],
        padx: int = 16,
        pady: int = 16,
        radius: int = PANEL_RADIUS,
        min_height: int = 80,
        fill_key: str = "panel",
        stretch_content: bool = False,
    ) -> None:
        super().__init__(parent, bg=colors["bg"])
        self.colors = colors
        self.padx = padx
        self.pady = pady
        self.radius = radius
        self.min_height = min_height
        self.fill_key = fill_key
        self.stretch_content = stretch_content
        self.configure(height=min_height)
        self.canvas = tk.Canvas(self, bg=colors["bg"], highlightthickness=0, bd=0, height=min_height)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.content = tk.Frame(self.canvas, bg=colors[fill_key])
        self.window_id = self.canvas.create_window(padx, pady, anchor="nw", window=self.content)
        self.shape_id: int | None = None
        self.pack_propagate(False)
        self.content.bind("<Configure>", self.sync_size)
        self.bind("<Configure>", self.draw)

    def sync_size(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        if self.stretch_content:
            height = max(self.min_height, self.winfo_height(), 1)
            self.canvas.configure(height=height)
            self.after_idle(self.draw)
            return

        height = max(self.min_height, self.content.winfo_reqheight() + self.pady * 2)
        self.configure(height=height)
        self.canvas.configure(height=height)
        self.after_idle(self.draw)

    def draw(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        current_width = self.winfo_width()
        width = max(current_width if current_width > 1 else self.winfo_reqwidth(), 20)
        if self.stretch_content:
            height = max(self.winfo_height(), self.min_height, 20)
        else:
            height = max(self.winfo_height(), self.content.winfo_reqheight() + self.pady * 2, 20)
        self.canvas.delete("panel-bg")
        self.shape_id = round_rect(
            self.canvas,
            1,
            1,
            width - 1,
            height - 1,
            self.radius,
            fill=self.colors[self.fill_key],
            outline=self.colors["border"],
            width=1,
            tags="panel-bg",
        )
        self.canvas.tag_lower("panel-bg")
        item_options = {"width": max(1, width - self.padx * 2)}
        if self.stretch_content:
            item_options["height"] = max(1, height - self.pady * 2)
        self.canvas.itemconfigure(self.window_id, **item_options)

    def set_colors(self, colors: dict[str, str]) -> None:
        self.colors = colors
        self.configure(bg=colors["bg"])
        self.canvas.configure(bg=colors["bg"])
        self.content.configure(bg=colors[self.fill_key])
        self.draw()


class TechPanel(tk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        colors: dict[str, str],
        padx: int = 18,
        pady: int = 16,
        min_height: int = 120,
        fill_key: str = "panel",
        stretch_content: bool = False,
    ) -> None:
        super().__init__(parent, bg=colors["bg"])
        self.colors = colors
        self.padx = padx
        self.pady = pady
        self.min_height = min_height
        self.fill_key = fill_key
        self.stretch_content = stretch_content
        self.configure(height=min_height)
        self.canvas = tk.Canvas(self, bg=colors["bg"], highlightthickness=0, bd=0, height=min_height)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.content = tk.Frame(self.canvas, bg=colors[fill_key])
        self.window_id = self.canvas.create_window(padx, pady, anchor="nw", window=self.content)
        self._draw_after_id: str | None = None
        self._last_draw_signature: tuple[object, ...] | None = None
        self.pack_propagate(False)
        self.content.bind("<Configure>", self.sync_size)
        self.bind("<Configure>", self.schedule_draw)
        self.schedule_draw(delay_ms=1)

    def sync_size(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        if self.stretch_content:
            height = max(self.min_height, self.winfo_height(), 1)
        else:
            height = max(self.min_height, self.content.winfo_reqheight() + self.pady * 2)
            self.configure(height=height)
        self.canvas.configure(height=height)
        self.schedule_draw()

    def schedule_draw(
        self,
        _event: tk.Event[tk.Misc] | None = None,
        delay_ms: int = PANEL_REDRAW_DELAY_MS,
    ) -> None:
        if self._draw_after_id is not None:
            with contextlib.suppress(tk.TclError):
                self.after_cancel(self._draw_after_id)
        self._draw_after_id = self.after(delay_ms, self.draw)

    def draw(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        self._draw_after_id = None
        current_width = self.winfo_width()
        width = max(current_width if current_width > 1 else self.winfo_reqwidth(), 20)
        if self.stretch_content:
            height = max(self.winfo_height(), self.min_height, 20)
        else:
            height = max(self.winfo_height(), self.content.winfo_reqheight() + self.pady * 2, 20)
        colors = self.colors
        signature = (
            width,
            height,
            colors[self.fill_key],
            colors["border"],
            colors["accent"],
            colors["muted"],
        )
        item_options = {"width": max(1, width - self.padx * 2)}
        if self.stretch_content:
            item_options["height"] = max(1, height - self.pady * 2)
        self.canvas.itemconfigure(self.window_id, **item_options)
        if self._last_draw_signature == signature:
            return
        self._last_draw_signature = signature
        self.canvas.delete("panel")
        self.canvas.create_rectangle(1, 1, width - 1, height - 1, fill=colors[self.fill_key], outline="", tags="panel")
        hatch_color = mix_color(colors[self.fill_key], colors["border"], 0.25)
        for x in range(8, width, 18):
            self.canvas.create_line(x, 2, x + 11, 2, fill=hatch_color, tags="panel")
        self.canvas.create_line(1, 1, width - 15, 1, fill=colors["border"], tags="panel")
        self.canvas.create_line(1, 1, 1, height - 15, fill=colors["border"], tags="panel")
        self.canvas.create_line(15, height - 1, width - 1, height - 1, fill=colors["border"], tags="panel")
        self.canvas.create_line(width - 1, 15, width - 1, height - 1, fill=colors["border"], tags="panel")
        self.canvas.create_line(1, 1, 12, 1, fill=colors["accent"], width=2, tags="panel")
        self.canvas.create_line(1, 1, 1, 12, fill=colors["accent"], width=2, tags="panel")
        self.canvas.create_line(width - 14, height - 1, width - 1, height - 14, fill=colors["muted"], tags="panel")
        self.canvas.create_text(width - 42, 8, text="/////7/10", fill=colors["border"], font=(UI_FONT_FAMILY, 7), tags="panel")
        self.canvas.tag_lower("panel")

    def set_colors(self, colors: dict[str, str]) -> None:
        self.colors = colors
        self.configure(bg=colors["bg"])
        self.canvas.configure(bg=colors["bg"])
        self.content.configure(bg=colors[self.fill_key])
        self._last_draw_signature = None
        self.draw()


class SearchHeaderIcon(tk.Canvas):
    def __init__(self, parent: tk.Widget, colors: dict[str, str]) -> None:
        super().__init__(parent, width=18, height=18, bg=colors["panel"], highlightthickness=0, bd=0)
        self.colors = colors
        self.draw()

    def draw(self) -> None:
        self.delete("all")
        accent = self.colors["accent"]
        self.create_oval(3, 3, 12, 12, outline=accent, width=2)
        self.create_line(11, 11, 16, 16, fill=accent, width=2)

    def set_colors(self, colors: dict[str, str]) -> None:
        self.colors = colors
        self.configure(bg=colors["panel"])
        self.draw()


class TechOptionRow(tk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        variable: tk.BooleanVar,
        icon: str,
        title: str,
        desc: str,
        colors: dict[str, str],
    ) -> None:
        super().__init__(parent, bg=colors["panel_2"], cursor="hand2")
        self.variable = variable
        self.colors = colors
        self.desc = desc
        self.check = tk.Canvas(self, width=22, height=22, bg=colors["panel_2"], highlightthickness=0, bd=0, cursor="hand2")
        self.check.pack(side=tk.LEFT, padx=(10, 14))
        icon_bg = colors["panel"]
        self.icon_box = tk.Frame(self, bg=icon_bg, width=58, height=58, highlightthickness=1, highlightbackground=colors["border"])
        self.icon_box.pack(side=tk.LEFT, pady=10)
        self.icon_box.pack_propagate(False)
        self.icon_label = tk.Label(self.icon_box, text=icon, bg=icon_bg, fg=colors["accent"], font=(SYMBOL_FONT_FAMILY, 26))
        self.icon_label.pack(expand=True)
        self.text_area = tk.Frame(self, bg=colors["panel_2"])
        self.text_area.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(18, 10), pady=10)
        self.title_label = tk.Label(
            self.text_area,
            text=title,
            bg=colors["panel_2"],
            fg=colors["text"],
            font=(UI_FONT_FAMILY, UI_TITLE_FONT_SIZE),
            anchor="w",
            justify=tk.LEFT,
            width=1,
            wraplength=420,
        )
        self.title_label.pack(anchor="w", fill=tk.X)
        self.desc_label = tk.Label(
            self.text_area,
            text=desc,
            bg=colors["panel_2"],
            fg=colors["muted"],
            font=(UI_FONT_FAMILY, UI_SMALL_FONT_SIZE),
            anchor="w",
            justify=tk.LEFT,
            width=1,
            wraplength=420,
        )
        self.desc_label.pack(anchor="w", fill=tk.X, pady=(6, 0))
        for widget in (self, self.check, self.icon_box, self.icon_label, self.text_area, self.title_label, self.desc_label):
            widget.bind("<Button-1>", self.toggle)
        self.bind("<Configure>", self.update_wrap)
        self.variable.trace_add("write", lambda *_: self.draw())
        self.draw()

    def toggle(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        self.variable.set(not self.variable.get())

    def update_wrap(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        wrap = max(240, self.winfo_width() - 160)
        self.title_label.configure(wraplength=wrap, justify=tk.LEFT)
        self.desc_label.configure(wraplength=wrap, justify=tk.LEFT)

    def set_text(self, title: str, desc: str) -> None:
        self.title_label.configure(text=title)
        self.desc_label.configure(text=desc)
        self.update_wrap()

    def draw(self) -> None:
        self.check.delete("all")
        checked = self.variable.get()
        fill = self.colors["accent"] if checked else self.colors["panel"]
        outline = self.colors["accent"] if checked else self.colors["border"]
        round_rect(self.check, 2, 2, 20, 20, 4, fill=fill, outline=outline, width=1)
        if checked:
            self.check.create_line(6, 11, 10, 15, 17, 6, fill="#101317", width=2, capstyle=tk.ROUND, joinstyle=tk.ROUND)

    def set_colors(self, colors: dict[str, str]) -> None:
        self.colors = colors
        self.configure(bg=colors["panel_2"])
        self.check.configure(bg=colors["panel_2"])
        self.icon_box.configure(bg=colors["panel"], highlightbackground=colors["border"])
        self.icon_label.configure(bg=colors["panel"], fg=colors["accent"])
        self.text_area.configure(bg=colors["panel_2"])
        self.title_label.configure(bg=colors["panel_2"], fg=colors["text"])
        self.desc_label.configure(bg=colors["panel_2"], fg=colors["muted"])
        self.draw()


class TechTaskCard(tk.Canvas):
    def __init__(
        self,
        parent: tk.Widget,
        colors: dict[str, str],
        title: str,
        subtitle: str,
        hint: str,
        icon: str,
        action: str,
        command: object | None,
        height: int = 104,
    ) -> None:
        self.colors = colors
        self.title = title
        self.subtitle = subtitle
        self.hint = hint
        self.icon = icon
        self.action = action
        self.command = command
        self.state = tk.NORMAL
        self.tooltip_window: tk.Toplevel | None = None
        self._last_draw_signature: tuple[object, ...] | None = None
        super().__init__(parent, height=height, bg=colors["panel"], highlightthickness=0, bd=0, cursor="hand2")
        self.bind("<Configure>", self.draw)
        self.bind("<Button-1>", self.on_click)
        self.bind("<Enter>", self.show_tooltip)
        self.bind("<Motion>", self.move_tooltip)
        self.bind("<Leave>", self.hide_tooltip)
        self.draw()

    def on_click(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        if self.state == tk.DISABLED:
            return
        if callable(self.command):
            self.command()

    def tooltip_text(self) -> str:
        return f"{self.subtitle}\n{self.hint}".strip()

    def show_tooltip(self, event: tk.Event[tk.Misc]) -> None:
        if self.tooltip_window is not None or not self.tooltip_text():
            self.move_tooltip(event)
            return
        tooltip = tk.Toplevel(self)
        tooltip.overrideredirect(True)
        tooltip.configure(bg=self.colors["accent"])
        body = tk.Frame(tooltip, bg=self.colors["panel"], padx=12, pady=9)
        body.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        tk.Label(
            body,
            text=self.title,
            bg=self.colors["panel"],
            fg=self.colors["text"],
            font=(UI_FONT_FAMILY, UI_SMALL_FONT_SIZE),
            anchor="w",
        ).pack(anchor="w")
        tk.Label(
            body,
            text=self.tooltip_text(),
            bg=self.colors["panel"],
            fg=self.colors["muted"],
            font=(UI_FONT_FAMILY, 10),
            justify=tk.LEFT,
            wraplength=280,
        ).pack(anchor="w", pady=(5, 0))
        self.tooltip_window = tooltip
        self.move_tooltip(event)

    def move_tooltip(self, event: tk.Event[tk.Misc]) -> None:
        if self.tooltip_window is None:
            return
        self.tooltip_window.geometry(f"+{event.x_root + 16}+{event.y_root + 14}")

    def hide_tooltip(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        if self.tooltip_window is None:
            return
        with contextlib.suppress(tk.TclError):
            self.tooltip_window.destroy()
        self.tooltip_window = None

    def draw(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        width = max(1, self.winfo_width())
        height = max(1, self.winfo_height())
        colors = self.colors
        disabled = self.state == tk.DISABLED
        card_fill = colors["card_2"] if disabled else colors["card"]
        text_fill = colors["card_muted"] if disabled else colors["card_text"]
        accent = colors["accent_dim"] if disabled else colors["accent"]
        signature = (
            width,
            height,
            self.title,
            self.icon,
            self.action,
            self.state,
            card_fill,
            text_fill,
            accent,
            colors["border"],
            colors["panel_2"],
            colors["muted"],
        )
        if self._last_draw_signature == signature:
            return
        self._last_draw_signature = signature
        self.delete("all")
        round_rect(self, 2, 2, width - 2, height - 2, 4, fill=card_fill, outline=colors["border"], width=1)
        self.create_rectangle(24, 22, 88, height - 22, fill=colors["panel_2"], outline=colors["border"])
        self.draw_task_icon(56, height // 2, accent)
        self.create_text(
            116,
            height // 2,
            text=self.title,
            anchor="w",
            width=max(150, width - 295),
            fill=text_fill,
            font=(UI_FONT_FAMILY, 22),
        )
        self.create_line(width - 185, height // 2, width - 116, height // 2, fill=colors["border"])
        cx = width - 70
        cy = height // 2
        self.create_oval(cx - 32, cy - 32, cx + 32, cy + 32, outline=colors["border"], width=1)
        self.create_oval(cx - 25, cy - 25, cx + 25, cy + 25, outline=colors["muted"], width=1)
        self.create_text(cx - 8, cy, text=self.action, fill=text_fill, font=(UI_FONT_FAMILY, 13))
        self.create_text(cx + 22, cy, text="›", fill=text_fill, font=(UI_FONT_FAMILY, 18))

    def draw_task_icon(self, cx: int, cy: int, fill: str) -> None:
        if self.icon == "⚡":
            points = (
                cx + 6,
                cy - 27,
                cx - 17,
                cy + 0,
                cx - 3,
                cy - 1,
                cx - 10,
                cy + 27,
                cx + 17,
                cy - 5,
                cx + 2,
                cy - 4,
            )
            self.create_polygon(points, fill=fill, outline="")
            return

        if self.icon == "⌖":
            radius = 13
            self.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline=fill, width=4)
            self.create_line(cx - 20, cy, cx + 20, cy, fill=fill, width=4, capstyle=tk.BUTT)
            self.create_line(cx, cy - 20, cx, cy + 20, fill=fill, width=4, capstyle=tk.BUTT)
            self.create_oval(cx - 4, cy - 4, cx + 4, cy + 4, fill=fill, outline="")
            return

        self.create_text(cx, cy, text=self.icon, fill=fill, font=(SYMBOL_FONT_FAMILY, 30, "bold"))

    def configure(self, cnf: object | None = None, **kwargs: object) -> object:
        if cnf:
            if isinstance(cnf, dict):
                kwargs.update(cnf)
            else:
                return super().configure(cnf)
        redraw = False
        canvas_kwargs: dict[str, object] = {}
        for key, value in kwargs.items():
            if key == "state":
                self.state = str(value)
                super().configure(cursor="arrow" if self.state == tk.DISABLED else "hand2")
                if self.state == tk.DISABLED:
                    self.hide_tooltip()
                self._last_draw_signature = None
                redraw = True
            elif key == "command":
                self.command = value
            else:
                canvas_kwargs[key] = value
        if canvas_kwargs:
            super().configure(**canvas_kwargs)
        if redraw:
            self.draw()
        return None

    config = configure

    def set_text(self, title: str, subtitle: str, hint: str, action: str) -> None:
        self.title = title
        self.subtitle = subtitle
        self.hint = hint
        self.action = action
        self.hide_tooltip()
        self._last_draw_signature = None
        self.draw()

    def set_colors(self, colors: dict[str, str]) -> None:
        self.colors = colors
        self.configure(bg=colors["panel"])
        self.hide_tooltip()
        self._last_draw_signature = None
        self.draw()


class RoundedCheck(tk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        variable: tk.BooleanVar,
        title: str,
        desc: str | None,
        colors: dict[str, str],
        title_font: tuple[str, int, str] | None = None,
        compact: bool = False,
    ) -> None:
        super().__init__(parent, bg=colors["panel"])
        title_font = title_font or (UI_FONT_FAMILY, UI_TITLE_FONT_SIZE)
        self.variable = variable
        self.colors = colors
        self.compact = compact
        self.box_size = 20 if not compact else 18

        self.box = tk.Canvas(
            self,
            width=self.box_size,
            height=self.box_size,
            bg=colors["panel"],
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self.box.grid(row=0, column=0, sticky="n", pady=(3 if not compact else 2, 0))

        self.text_frame = tk.Frame(self, bg=colors["panel"])
        self.text_frame.grid(row=0, column=1, sticky="w", padx=(10, 0))

        self.title_label = tk.Label(
            self.text_frame,
            text=title,
            bg=colors["panel"],
            fg=colors["text"] if not compact else colors["muted"],
            font=title_font if not compact else (UI_FONT_FAMILY, UI_SMALL_FONT_SIZE),
            anchor="w",
        )
        self.title_label.pack(anchor="w")

        if desc:
            self.desc_label = tk.Label(
                self.text_frame,
                text=desc,
                bg=colors["panel"],
                fg=colors["muted"],
                font=(UI_FONT_FAMILY, UI_SMALL_FONT_SIZE),
                anchor="w",
            )
            self.desc_label.pack(anchor="w", pady=(5, 0))
        else:
            self.desc_label = None

        for widget in (self, self.box, self.title_label, self.desc_label):
            if widget is not None:
                widget.bind("<Button-1>", self.toggle)

        self.variable.trace_add("write", lambda *_: self.draw())
        self.draw()

    def toggle(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        self.variable.set(not self.variable.get())

    def draw(self) -> None:
        self.box.delete("all")
        inset = 1
        checked = self.variable.get()
        fill = self.colors["check_on"] if checked else self.colors["panel"]
        outline = self.colors["check_on"] if checked else self.colors["border"]
        round_rect(
            self.box,
            inset,
            inset,
            self.box_size - inset,
            self.box_size - inset,
            6,
            fill=fill,
            outline=outline,
            width=1,
        )
        if checked:
            self.box.create_line(
                5,
                self.box_size // 2,
                9,
                self.box_size - 6,
                self.box_size - 4,
                5,
                fill=self.colors["check_mark"],
                width=2,
                capstyle=tk.ROUND,
                joinstyle=tk.ROUND,
            )

    def set_colors(self, colors: dict[str, str]) -> None:
        self.colors = colors
        panel_bg = colors["panel"]
        self.configure(bg=panel_bg)
        self.box.configure(bg=panel_bg)
        self.text_frame.configure(bg=panel_bg)
        self.title_label.configure(
            bg=panel_bg,
            fg=colors["text"] if not self.compact else colors["muted"],
        )
        if self.desc_label is not None:
            self.desc_label.configure(bg=panel_bg, fg=colors["muted"])
        self.draw()


class ThemeSwitch(tk.Canvas):
    def __init__(self, parent: tk.Widget, app: "FixerGui") -> None:
        self.app = app
        self.progress = 0.0 if app.theme_name == "dark" else 1.0
        super().__init__(
            parent,
            width=92,
            height=34,
            bg=app.colors["bg"],
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self.app.theme_switches.append(self)
        self.bind("<Button-1>", lambda _event: app.start_theme_transition())
        self.draw()

    def draw(self) -> None:
        colors = self.app.colors
        self.delete("all")
        draw_capsule(
            self,
            1,
            1,
            91,
            33,
            fill=colors["switch_track"],
            outline=colors["border"],
            width=1,
        )
        progress = clamp01(self.progress)
        dark = progress < 0.5
        knob_x = 17 + (75 - 17) * progress
        icon_x = 57 + (32 - 57) * progress
        self.create_oval(knob_x - 10, 7, knob_x + 10, 27, fill=colors["switch_knob"], outline="")
        self.create_text(
            icon_x,
            17,
            text="☾" if dark else "☀",
            fill=colors["switch_text"],
            font=(SYMBOL_FONT_FAMILY, 18, "bold"),
        )

    def set_progress(self, progress: float, redraw: bool = True) -> None:
        self.progress = clamp01(progress)
        if redraw:
            self.draw()

    def set_colors(self, colors: dict[str, str]) -> None:
        self.configure(bg=colors["bg"])
        self.draw()


class LanguageSwitch(tk.Canvas):
    def __init__(self, parent: tk.Widget, app: "FixerGui") -> None:
        self.app = app
        self.progress = 0.0 if app.language == "zh" else 1.0
        super().__init__(
            parent,
            width=94,
            height=30,
            bg=app.colors["bg"],
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self.app.language_switches.append(self)
        self.bind("<Button-1>", lambda _event: app.start_language_transition())
        self.draw()

    def draw(self) -> None:
        colors = self.app.colors
        self.delete("all")
        draw_capsule(self, 1, 1, 93, 29, fill=colors["switch_track"], outline=colors["border"], width=1)
        progress = clamp01(self.progress)
        knob_x = 4 + 45 * progress
        draw_capsule(self, knob_x, 4, knob_x + 41, 26, fill=colors["accent"], outline=colors["accent"], width=1)
        zh_active = progress < 0.5
        en_active = not zh_active
        self.create_text(
            25,
            15,
            text="中",
            fill=colors["bg"] if zh_active else colors["muted"],
            font=(UI_FONT_FAMILY, 11),
        )
        self.create_text(
            69,
            15,
            text="ENG",
            fill=colors["bg"] if en_active else colors["muted"],
            font=(UI_FONT_FAMILY, 10),
        )

    def set_progress(self, progress: float, redraw: bool = True) -> None:
        self.progress = clamp01(progress)
        if redraw:
            self.draw()

    def set_colors(self, colors: dict[str, str]) -> None:
        self.configure(bg=colors["bg"])
        self.draw()


class LogPowerSwitch(tk.Frame):
    def __init__(self, parent: tk.Widget, app: "FixerGui", text: str, command: object) -> None:
        self.app = app
        self.command = command
        self.progress = 1.0 if app.debug_log.get() else 0.0
        bg = str(parent.cget("bg")) if "bg" in parent.keys() else app.colors["panel"]
        self.base_bg = bg
        super().__init__(parent, bg=bg, cursor="hand2")
        self.label = tk.Label(
            self,
            text=text,
            bg=bg,
            fg=app.colors["text"],
            font=(UI_FONT_FAMILY, UI_SMALL_FONT_SIZE),
            cursor="hand2",
        )
        self.label.pack(side=tk.LEFT, padx=(0, 8))
        self.canvas = tk.Canvas(
            self,
            width=58,
            height=24,
            bg=bg,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self.canvas.pack(side=tk.LEFT)
        for widget in (self, self.label, self.canvas):
            widget.bind("<Button-1>", self.on_click)
        self.draw()

    def on_click(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        if callable(self.command):
            self.command()

    def draw(self) -> None:
        colors = self.app.colors
        self.canvas.delete("all")
        progress = clamp01(self.progress)
        track_fill = mix_color(colors["switch_track"], LOG_SWITCH_ON_YELLOW, progress)
        draw_capsule(self.canvas, 1, 2, 57, 22, fill=track_fill, outline=colors["border"], width=1)
        knob_x = 12 + 32 * progress
        knob_fill = mix_color(colors["accent"], LOG_SWITCH_KNOB_ON, progress)
        self.canvas.create_oval(knob_x - 8, 4, knob_x + 8, 20, fill=knob_fill, outline="")
        label = self.app.tr("log_switch_on") if progress >= 0.5 else self.app.tr("log_switch_off")
        text_x = 22 if progress >= 0.5 else 36
        text_fill = invert_color(colors["text"]) if progress >= 0.5 else colors["text"]
        self.canvas.create_text(
            text_x,
            12,
            text=label,
            fill=text_fill,
            font=(UI_FONT_FAMILY, 8),
        )

    def set_label(self, text: str) -> None:
        self.label.configure(text=text)

    def set_progress(self, progress: float, redraw: bool = True) -> None:
        self.progress = clamp01(progress)
        if redraw:
            self.draw()

    def set_colors(self, colors: dict[str, str]) -> None:
        bg = colors["panel"]
        self.configure(bg=bg)
        self.label.configure(bg=bg, fg=colors["text"])
        self.canvas.configure(bg=bg)
        self.draw()


class DisclosureToggle(tk.Frame):
    def __init__(self, parent: tk.Widget, app: "FixerGui", text: str, command: object) -> None:
        self.app = app
        self.command = command
        self.progress = 0.0
        bg = str(parent.cget("bg")) if "bg" in parent.keys() else app.colors["bg"]
        self.base_bg = bg
        super().__init__(parent, bg=bg, cursor="hand2")

        self.arrow = tk.Canvas(
            self,
            width=22,
            height=22,
            bg=bg,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self.arrow.pack(side=tk.LEFT)

        self.label = tk.Label(
            self,
            text=text,
            bg=bg,
            fg=app.colors["muted"],
            font=(UI_FONT_FAMILY, UI_SMALL_FONT_SIZE),
            cursor="hand2",
        )
        self.label.pack(side=tk.LEFT, padx=(4, 0))

        for widget in (self, self.arrow, self.label):
            widget.bind("<Button-1>", self.on_click)

        self.draw()

    def on_click(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        if callable(self.command):
            self.command()

    def draw(self) -> None:
        self.arrow.delete("all")
        angle = math.radians(90 * clamp01(self.progress))
        center_x = 11
        center_y = 11
        base_points = [(6, 0), (-5, -6), (-2, 0), (-5, 6)]
        points: list[float] = []
        for x, y in base_points:
            rotated_x = x * math.cos(angle) - y * math.sin(angle)
            rotated_y = x * math.sin(angle) + y * math.cos(angle)
            points.extend((center_x + rotated_x, center_y + rotated_y))
        self.arrow.create_polygon(points, fill=self.app.colors["muted"], outline="")

    def set_progress(self, progress: float, redraw: bool = True) -> None:
        self.progress = clamp01(progress)
        if redraw:
            self.draw()

    def set_colors(self, colors: dict[str, str]) -> None:
        self.configure(bg=self.base_bg)
        self.arrow.configure(bg=self.base_bg)
        self.label.configure(bg=self.base_bg, fg=colors["muted"])
        self.draw()


class RoundedButton(tk.Canvas):
    def __init__(
        self,
        parent: tk.Widget,
        text: str,
        command: object | None,
        bg: str,
        activebackground: str,
        fg: str,
        activeforeground: str,
        width: int | None,
        font: tuple[str, int, str],
        padx: int = 10,
        pady: int = 6,
        radius: int = PANEL_RADIUS,
        select_effect: bool = False,
        selected_fill: str = "#2f8cff",
        selected_border: str = "#9ee7ff",
    ) -> None:
        self.text = text
        self.command = command
        self.fill = bg
        self.active_fill = activebackground
        self.text_fill = fg
        self.active_text_fill = activeforeground
        self.font = font
        self.padx = padx
        self.pady = pady
        self.radius = radius
        self.select_effect = select_effect
        self.selected_fill = selected_fill
        self.selected_border = selected_border
        self.state = tk.NORMAL
        self.hover = False
        self.animating = False
        self.pressed = False
        self.effect_outset = 5 if select_effect else 0
        self.release_progress = 0.0

        font_obj = tkfont.Font(font=font)
        char_width = max(8, font_obj.measure("M"))
        text_width = font_obj.measure(text)
        base_width = max(1, max(text_width + padx * 2, (width or 0) * char_width + padx * 2) - 10)
        base_height = max(1, max(34, font_obj.metrics("linespace") + pady * 2) + 2)
        canvas_width = base_width + self.effect_outset * 2
        canvas_height = base_height + self.effect_outset * 2
        parent_bg = self.read_parent_bg(parent, bg)

        super().__init__(
            parent,
            width=canvas_width,
            height=canvas_height,
            bg=parent_bg,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<ButtonPress-1>", self.on_press)
        self.bind("<ButtonRelease-1>", self.on_release)
        self.draw()

    @staticmethod
    def read_parent_bg(parent: tk.Widget, fallback: str) -> str:
        with contextlib.suppress(tk.TclError):
            return str(parent.cget("bg"))
        return fallback

    def parent_bg(self) -> str:
        with contextlib.suppress(tk.TclError, AttributeError):
            return str(self.master.cget("bg"))
        return self.fill

    def resolved_color(self, value: str) -> str:
        with contextlib.suppress(tk.TclError, ValueError):
            red, green, blue = self.winfo_rgb(value)
            return "#{:02x}{:02x}{:02x}".format(red // 256, green // 256, blue // 256)
        return value

    def draw(self) -> None:
        self.delete("all")
        parent_bg = self.parent_bg()
        super().configure(bg=parent_bg)
        width = max(1, int(float(self.cget("width"))))
        height = max(1, int(float(self.cget("height"))))
        inset = self.effect_outset
        base_x1 = 1 + inset
        base_y1 = 1 + inset
        base_x2 = width - 1 - inset
        base_y2 = height - 1 - inset
        enabled = self.state != tk.DISABLED
        base_fill = self.active_fill if enabled and self.hover else self.fill
        base_text_fill = self.active_text_fill if enabled and self.hover else self.text_fill
        fill = base_fill
        text_fill = base_text_fill
        outline = fill
        if not enabled:
            fill = mix_color(self.resolved_color(fill), self.resolved_color(parent_bg), 0.42)
            text_fill = mix_color(self.resolved_color(text_fill), self.resolved_color(parent_bg), 0.42)
            outline = fill

        if self.select_effect and self.pressed and enabled:
            self.draw_press_overlay(base_x1, base_y1, base_x2, base_y2)
        if self.select_effect and self.release_progress > 0 and enabled:
            self.draw_release_overlay(base_x1, base_y1, base_x2, base_y2)

        round_rect(
            self,
            base_x1,
            base_y1,
            base_x2,
            base_y2,
            self.radius,
            fill=fill,
            outline=outline,
            width=1,
        )
        self.create_text(
            width // 2,
            height // 2,
            text=self.text,
            fill=text_fill,
            font=self.font,
        )

    def draw_press_overlay(self, x1: float, y1: float, x2: float, y2: float) -> None:
        outset = self.effect_outset
        fill = adjust_color_lightness(self.resolved_color(self.fill), SELECTED_LIGHTNESS_DELTA)
        round_rect(
            self,
            x1 - outset,
            y1 - outset,
            x2 + outset,
            y2 + outset,
            self.radius + outset,
            fill=fill,
            outline=self.selected_border,
            width=1,
        )

    def draw_release_overlay(self, x1: float, y1: float, x2: float, y2: float) -> None:
        progress = ease_in_out(self.release_progress)
        outset = self.effect_outset * (1 - progress)
        selected_fill = adjust_color_lightness(self.resolved_color(self.fill), SELECTED_LIGHTNESS_DELTA)
        overlay_fill = mix_color(self.resolved_color(self.fill), selected_fill, progress)
        overlay_outline = mix_color(self.resolved_color(self.fill), self.selected_border, progress)
        round_rect(
            self,
            x1 - outset,
            y1 - outset,
            x2 + outset,
            y2 + outset,
            self.radius + outset,
            fill=overlay_fill,
            outline=overlay_outline,
            width=1,
        )

    def on_enter(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        self.hover = True
        self.draw()

    def on_leave(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        self.hover = False
        self.draw()

    def on_press(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        if self.state == tk.DISABLED or not callable(self.command):
            return
        if self.select_effect:
            self.pressed = True
            self.release_progress = 0.0
            self.draw()
            return
        self.command()

    def on_release(self, event: tk.Event[tk.Misc] | None = None) -> None:
        if self.state == tk.DISABLED or not callable(self.command):
            self.pressed = False
            self.draw()
            return
        if not self.select_effect:
            return
        inside = event is None or (0 <= event.x <= int(float(self.cget("width"))) and 0 <= event.y <= int(float(self.cget("height"))))
        self.pressed = False
        if not inside:
            self.draw()
            return
        self.start_select_cycle()

    def start_select_cycle(self) -> None:
        if self.animating:
            return
        self.animating = True
        frames = 9

        def settle(frame: int = 0) -> None:
            progress = frame / frames
            self.release_progress = progress
            self.draw()
            if frame < frames:
                self.after(14, lambda: settle(frame + 1))
                return

            self.release_progress = 0.0
            self.animating = False
            self.draw()
            if callable(self.command):
                self.command()

        settle()

    def configure(self, cnf: object | None = None, **kwargs: object) -> object:
        if cnf:
            if isinstance(cnf, dict):
                kwargs.update(cnf)
            else:
                return super().configure(cnf)

        redraw = False
        canvas_kwargs: dict[str, object] = {}
        for key, value in kwargs.items():
            if key == "state":
                self.state = str(value)
                super().configure(cursor="arrow" if self.state == tk.DISABLED else "hand2")
                if self.state == tk.DISABLED:
                    self.pressed = False
                    self.release_progress = 0.0
                    self.animating = False
                redraw = True
            elif key == "bg":
                self.fill = str(value)
                redraw = True
            elif key == "activebackground":
                self.active_fill = str(value)
                redraw = True
            elif key == "fg":
                self.text_fill = str(value)
                redraw = True
            elif key == "activeforeground":
                self.active_text_fill = str(value)
                redraw = True
            elif key == "text":
                self.text = str(value)
                redraw = True
            elif key == "command":
                self.command = value
            elif key == "select_effect":
                self.select_effect = bool(value)
                redraw = True
            else:
                canvas_kwargs[key] = value

        if canvas_kwargs:
            super().configure(**canvas_kwargs)
        if redraw:
            self.draw()
        return None

    config = configure


class FixerGui:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_TITLE)
        configure_app_fonts(self.root)
        set_window_icon(self.root)
        self.collapsed_window_height = MIN_COLLAPSED_WINDOW_HEIGHT
        self.root.geometry(f"{DEFAULT_WINDOW_WIDTH}x{self.collapsed_window_height}")
        self.root.minsize(MIN_WINDOW_WIDTH, self.collapsed_window_height)

        self.theme_name = "dark"
        self.language = "zh"
        self.colors = THEMES[self.theme_name]
        self.target_dir = tk.StringVar(value=str(default_target_dir()))
        self.stable_texture = tk.BooleanVar(value=False)
        self.fixmenu = tk.BooleanVar(value=False)
        self.include_disabled = tk.BooleanVar(value=False)
        self.force_new_version = tk.BooleanVar(value=False)
        self.debug_log = tk.BooleanVar(value=True)
        self.running = False
        self.update_check_running = False

        self.log_queue: queue.Queue[object] = queue.Queue()
        self.backup_window: tk.Toplevel | None = None
        self.backup_list: tk.Listbox | None = None
        self.backup_items: list[dict[str, str]] = []

        self.action_buttons: list[tk.Widget] = []
        self.main_frame: tk.Frame | None = None
        self.log_box: tk.Text | None = None
        self.log_shell: TechPanel | None = None
        self.log_inner: TechPanel | None = None
        self.log_header: tk.Frame | None = None
        self.log_area: tk.Frame | None = None
        self.log_title_label: tk.Label | None = None
        self.log_toggle: LogPowerSwitch | DisclosureToggle | None = None
        self.update_button: RoundedButton | None = None
        self.log_default_text: str | None = None
        self.log_expanded = False
        self.log_animating = False
        self.theme_switches: list[ThemeSwitch] = []
        self.theme_animating = False
        self.theme_after_id: str | None = None
        self.language_switches: list[LanguageSwitch] = []
        self.language_animating = False
        self.language_after_id: str | None = None
        self.language_fade_after_id: str | None = None
        self.contour_layers: list[tuple[tk.Canvas, tk.Widget, int, float, int]] = []
        self.contour_redraw_after_id: str | None = None
        self.contour_source_image: object | None = None
        self.contour_tile_cache: dict[tuple[str, str, float], object] = {}
        self.contour_photo_refs: dict[int, object] = {}
        self.root_resize_after_id: str | None = None
        self.log_timer_resolution_active = False

        self.build_ui()
        self.root.bind("<Configure>", self.on_root_configure, add="+")
        self.root.after(80, self.poll_log_queue)
        self.root.after(UPDATE_CHECK_DELAY_MS, lambda: self.start_update_check(manual=False))

    def theme_widget(self, widget: tk.Widget, **roles: str | None) -> tk.Widget:
        widget._theme_roles = {option: key for option, key in roles.items() if key}  # type: ignore[attr-defined]
        return widget

    def apply_theme_to_tree(self, widget: tk.Widget, colors: dict[str, str]) -> None:
        if hasattr(widget, "set_colors"):
            with contextlib.suppress(tk.TclError):
                widget.set_colors(colors)  # type: ignore[attr-defined]

        roles = getattr(widget, "_theme_roles", {})
        updates = {option: colors[key] for option, key in roles.items() if key in colors}
        if updates:
            with contextlib.suppress(tk.TclError):
                widget.configure(**updates)

        for child in widget.winfo_children():
            self.apply_theme_to_tree(child, colors)

    def apply_theme_frame(self, colors: dict[str, str], switch_progress: float) -> None:
        self.colors = colors
        self.root.configure(bg=colors["bg"])
        for switch in list(self.theme_switches):
            if switch.winfo_exists():
                switch.set_progress(switch_progress, redraw=False)
        self.apply_theme_to_tree(self.root, colors)

    def start_theme_transition(self) -> None:
        if self.theme_animating:
            return

        self.theme_animating = True
        from_name = self.theme_name
        to_name = "light" if from_name == "dark" else "dark"
        start_theme = THEMES[from_name]
        end_theme = THEMES[to_name]
        start_switch = 0.0 if from_name == "dark" else 1.0
        end_switch = 0.0 if to_name == "dark" else 1.0
        frames = 18
        interval_ms = 14

        if self.backup_window is not None and self.backup_window.winfo_exists():
            self.backup_window.destroy()
            self.backup_window = None
            self.backup_list = None

        def step(frame: int = 0) -> None:
            progress = ease_in_out(frame / frames)
            colors = mix_theme(start_theme, end_theme, progress)
            switch_progress = start_switch + (end_switch - start_switch) * progress
            self.apply_theme_frame(colors, switch_progress)

            if frame < frames:
                self.theme_after_id = self.root.after(interval_ms, lambda: step(frame + 1))
                return

            self.theme_name = to_name
            self.colors = THEMES[to_name]
            self.apply_theme_frame(self.colors, end_switch)
            self.schedule_contour_redraw(delay_ms=1)
            self.theme_animating = False
            self.theme_after_id = None

        step()

    def tr(self, key: str) -> str:
        current = UI_COPY.get(self.language, UI_COPY["zh"])
        return current.get(key, UI_COPY["zh"].get(key, key))

    def default_log_text(self) -> str:
        return self.default_log_text_for_language(self.language)

    def default_log_text_for_language(self, language: str) -> str:
        current_language = self.language
        self.language = language
        try:
            return self._default_log_text_for_current_language()
        finally:
            self.language = current_language

    def _default_log_text_for_current_language(self) -> str:
        stable_state = self.tr("enabled") if self.stable_texture.get() else self.tr("disabled")
        fixmenu_state = self.tr("enabled") if self.fixmenu.get() else self.tr("disabled")
        return (
            f"[12:45:10]  {self.tr('ready')}\n"
            f"[12:45:11]  {self.tr('target_path')}: {self.target_dir.get()}\n"
            f"[12:45:11]  {self.tr('repair_status')}: {self.tr('stable_texture')} = {stable_state}  |  {self.tr('fix_menu')} = {fixmenu_state}\n"
            f"[12:45:11]  {self.tr('click_start')}\n"
        )

    def scroll_log_to_bottom(self, defer: bool = False) -> None:
        log_box = self.log_box
        if log_box is None:
            return

        def align(update_layout: bool = False) -> None:
            if self.log_box is not log_box:
                return
            with contextlib.suppress(tk.TclError):
                if update_layout:
                    log_box.update_idletasks()
                log_box.see("end-1c")
                log_box.yview_moveto(1.0)

        align()
        if defer:
            with contextlib.suppress(tk.TclError):
                self.root.after_idle(lambda: align(update_layout=True))

    def translate_log_text_for_language(self, text: str) -> str:
        lines = text.splitlines(keepends=True)
        if not lines:
            return text
        translated_lines: list[str] = []
        for raw_line in lines:
            line = raw_line.rstrip("\r\n")
            ending = raw_line[len(line):]
            translated_lines.append(self.update_log_line_for_language(line) + ending)
        return "".join(translated_lines)

    def skipped_log_suffix_for_language(self, count: str | None) -> str:
        if not count:
            return ""
        return f" {self.tr('fixer_skipped_newer').format(count=count.strip())}"

    def chinese_skipped_count(self, text: str) -> str | None:
        marker = "已跳过 "
        suffix = " 个较新版本文件"
        if marker not in text:
            return None
        candidate = text.split(marker, 1)[1].split(suffix, 1)[0].strip()
        return candidate or None

    def english_skipped_count(self, text: str) -> str | None:
        marker = "Skipped "
        suffix = " newer-version file(s)"
        if marker not in text:
            return None
        candidate = text.split(marker, 1)[1].split(suffix, 1)[0].strip()
        return candidate or None

    def process_title_for_language(self, title: str) -> str:
        title = title.strip()
        title_keys = ("preview_title", "fix_title", "rollback_name")
        for language in ("zh", "en"):
            for key in title_keys:
                if title == UI_COPY[language][key]:
                    return self.tr(key)
        return title

    def translate_process_done_line(self, line: str) -> str:
        if not (line.startswith("---- ") and line.endswith(" ----")):
            return line
        body = line[5:-5]
        for language in ("zh", "en"):
            process_end = UI_COPY[language]["process_end"]
            separators = (f" {process_end}: ", f"{process_end}: ")
            for separator in separators:
                if separator in body:
                    title, code = body.rsplit(separator, 1)
                    translated_title = self.process_title_for_language(title)
                    return f"---- {translated_title} {self.tr('process_end')}: {code.strip()} ----"
        return line

    def translate_fixer_summary_line(self, line: str) -> str:
        zh_dry_run_prefix = "预览扫描完成。将修改/删除 "
        zh_dry_run_separator = " 个文件。"
        if line.startswith(zh_dry_run_prefix):
            body = line[len(zh_dry_run_prefix):]
            if zh_dry_run_separator in body:
                count, remainder = body.split(zh_dry_run_separator, 1)
                skipped = self.skipped_log_suffix_for_language(self.chinese_skipped_count(remainder))
                return self.tr("fixer_dry_run_complete").format(count=count.strip(), skipped=skipped)

        en_dry_run_prefix = "Preview scan complete. "
        en_dry_run_separator = " file(s) would be modified/deleted."
        if line.startswith(en_dry_run_prefix):
            body = line[len(en_dry_run_prefix):]
            if en_dry_run_separator in body:
                count, remainder = body.split(en_dry_run_separator, 1)
                skipped = self.skipped_log_suffix_for_language(self.english_skipped_count(remainder))
                return self.tr("fixer_dry_run_complete").format(count=count.strip(), skipped=skipped)

        zh_no_changes_prefix = "完成。无需修改。"
        if line.startswith(zh_no_changes_prefix):
            skipped = self.skipped_log_suffix_for_language(self.chinese_skipped_count(line[len(zh_no_changes_prefix):]))
            return self.tr("fixer_no_changes").format(skipped=skipped)

        en_no_changes_prefix = "Done. No changes needed."
        if line.startswith(en_no_changes_prefix):
            skipped = self.skipped_log_suffix_for_language(self.english_skipped_count(line[len(en_no_changes_prefix):]))
            return self.tr("fixer_no_changes").format(skipped=skipped)

        zh_run_match = re.match(r"^完成。已修改 (?P<modified>\d+) 个文件，已硬删除 (?P<deleted>\d+) 个热修复文件。$", line)
        if zh_run_match:
            return self.tr("fixer_run_complete").format(
                modified=zh_run_match.group("modified"),
                deleted=zh_run_match.group("deleted"),
            )

        en_run_match = re.match(r"^Done\. Modified (?P<modified>\d+) file\(s\), hard-deleted (?P<deleted>\d+) hotfix file\(s\)\.$", line)
        if en_run_match:
            return self.tr("fixer_run_complete").format(
                modified=en_run_match.group("modified"),
                deleted=en_run_match.group("deleted"),
            )

        return line

    def replace_log_with_default_text(self) -> None:
        if self.log_box is None:
            return
        default_text = self.default_log_text()
        self.log_box.delete("1.0", tk.END)
        self.log_box.insert(tk.END, default_text)
        self.scroll_log_to_bottom(defer=True)
        self.log_default_text = default_text

    def refresh_default_log_language(self) -> None:
        if self.log_box is None:
            return
        current_text = self.log_box.get("1.0", "end-1c")
        new_default = self.default_log_text()
        candidates = [
            text
            for text in (
                self.log_default_text,
                self.default_log_text_for_language("zh"),
                self.default_log_text_for_language("en"),
            )
            if text
        ]
        for old_default in candidates:
            if current_text.startswith(old_default):
                remainder = current_text[len(old_default):]
                self.log_box.delete("1.0", tk.END)
                self.log_box.insert(tk.END, new_default + remainder)
                self.scroll_log_to_bottom(defer=True)
                self.log_default_text = new_default
                current_text = self.log_box.get("1.0", "end-1c")
                break
        self.refresh_update_log_language(current_text)
        self.scroll_log_to_bottom(defer=True)

    def update_log_line_for_language(self, line: str) -> str:
        process_line = self.translate_process_done_line(line)
        if process_line != line:
            return process_line

        fixer_line = self.translate_fixer_summary_line(line)
        if fixer_line != line:
            return fixer_line

        zh_current_prefix = "检查更新：当前版本 v"
        zh_current_separator = "，最新版本 "
        en_current_prefix = "Update check: current version v"
        en_current_separator = ", latest version "

        if line.startswith(zh_current_prefix):
            body = line[len(zh_current_prefix):].rstrip("。.")
            if zh_current_separator in body:
                local, remote = body.split(zh_current_separator, 1)
                return self.tr("update_current_log").format(local=local.strip(), remote=remote.strip())

        if line.startswith(en_current_prefix):
            body = line[len(en_current_prefix):].rstrip("。.")
            if en_current_separator in body:
                local, remote = body.split(en_current_separator, 1)
                return self.tr("update_current_log").format(local=local.strip(), remote=remote.strip())

        zh_no_file_prefix = "检查更新：发现新版本 "
        zh_no_file_suffix = "，但暂时没有可下载文件。"
        en_no_file_prefix = "Update check: version "
        en_no_file_suffix = " is available, but no downloadable file is available yet."

        if line.startswith(zh_no_file_prefix) and line.endswith(zh_no_file_suffix):
            remote = line[len(zh_no_file_prefix):-len(zh_no_file_suffix)]
            return self.tr("update_no_file_log").format(remote=remote.strip())

        if line.startswith(en_no_file_prefix) and line.endswith(en_no_file_suffix):
            remote = line[len(en_no_file_prefix):-len(en_no_file_suffix)]
            return self.tr("update_no_file_log").format(remote=remote.strip())

        translations = {
            UI_COPY["zh"]["update_available_log"]: self.tr("update_available_log"),
            UI_COPY["en"]["update_available_log"]: self.tr("update_available_log"),
            UI_COPY["zh"]["update_downloaded_log"]: self.tr("update_downloaded_log"),
            UI_COPY["en"]["update_downloaded_log"]: self.tr("update_downloaded_log"),
            UI_COPY["zh"]["update_unknown_status"]: self.tr("update_unknown_status"),
            UI_COPY["en"]["update_unknown_status"]: self.tr("update_unknown_status"),
            f"---- {UI_COPY['zh']['update_check_start']} ----": f"---- {self.tr('update_check_start')} ----",
            f"---- {UI_COPY['en']['update_check_start']} ----": f"---- {self.tr('update_check_start')} ----",
            f"---- {UI_COPY['zh']['update_download_start']} ----": f"---- {self.tr('update_download_start')} ----",
            f"---- {UI_COPY['en']['update_download_start']} ----": f"---- {self.tr('update_download_start')} ----",
        }
        return translations.get(line, line)

    def refresh_update_log_language(self, current_text: str | None = None) -> None:
        if self.log_box is None:
            return
        if current_text is None:
            current_text = self.log_box.get("1.0", "end-1c")
        lines = current_text.splitlines(keepends=True)
        changed = False
        translated_lines: list[str] = []
        for raw_line in lines:
            line = raw_line.rstrip("\r\n")
            ending = raw_line[len(line):]
            translated = self.update_log_line_for_language(line)
            if translated != line:
                changed = True
            translated_lines.append(translated + ending)
        if changed:
            self.log_box.delete("1.0", tk.END)
            self.log_box.insert(tk.END, "".join(translated_lines))
            self.scroll_log_to_bottom(defer=True)

    def start_language_transition(self) -> None:
        if self.language_animating:
            return

        self.language_animating = True
        from_language = self.language
        to_language = "en" if from_language == "zh" else "zh"
        start_progress = 0.0 if from_language == "zh" else 1.0
        end_progress = 0.0 if to_language == "zh" else 1.0
        frames = 14
        interval_ms = 14

        def step(frame: int = 0) -> None:
            progress = ease_in_out(frame / frames)
            switch_progress = start_progress + (end_progress - start_progress) * progress
            for switch in list(self.language_switches):
                if switch.winfo_exists():
                    switch.set_progress(switch_progress)

            if frame < frames:
                self.language_after_id = self.root.after(interval_ms, lambda: step(frame + 1))
                return

            self.language_after_id = None
            self.fade_language_rebuild(to_language)

        step()

    def panel_fade_colors(self, progress: float) -> dict[str, str]:
        base_colors = THEMES[self.theme_name]
        bg = base_colors["bg"]
        progress = clamp01(progress)
        return {
            key: value if key == "bg" else mix_color(value, bg, progress)
            for key, value in base_colors.items()
        }

    def apply_panel_fade(self, progress: float) -> None:
        colors = self.panel_fade_colors(progress)
        self.colors = colors
        self.root.configure(bg=colors["bg"])
        self.apply_theme_to_tree(self.root, colors)

    def fade_language_rebuild(self, to_language: str) -> None:
        frames = LANGUAGE_FADE_FRAMES
        interval_ms = LANGUAGE_FADE_INTERVAL_MS
        target_fade = LANGUAGE_FADE_PANEL_TARGET

        def fade_out(frame: int = 0) -> None:
            progress = ease_in_out(frame / frames)
            self.apply_panel_fade(target_fade * progress)
            if frame < frames:
                self.language_fade_after_id = self.root.after(interval_ms, lambda: fade_out(frame + 1))
                return

            try:
                self.language = to_language
                self.update_language_texts()
                self.apply_panel_fade(target_fade)
                self.root.update_idletasks()
            except Exception:
                self.apply_panel_fade(0.0)
                self.language_animating = False
                self.language_fade_after_id = None
                raise
            fade_in()

        def fade_in(frame: int = 0) -> None:
            progress = ease_in_out(frame / frames)
            self.apply_panel_fade(target_fade * (1.0 - progress))
            if frame < frames:
                self.language_fade_after_id = self.root.after(interval_ms, lambda: fade_in(frame + 1))
                return

            self.apply_panel_fade(0.0)
            self.colors = THEMES[self.theme_name]
            self.language_animating = False
            self.language_fade_after_id = None

        fade_out()

    def hide_task_tooltips(self) -> None:
        for button in (self.fix_button, self.preview_button, self.rollback_button):
            if hasattr(button, "hide_tooltip"):
                button.hide_tooltip()  # type: ignore[attr-defined]

    def update_language_texts(self) -> None:
        self.hide_task_tooltips()
        self.app_title_label.configure(text=f"{self.tr('app_header')}  v{APP_VERSION}")
        self.target_header_label.configure(text=self.tr("target_title"))
        self.options_header_label.configure(text=self.tr("repair_title"))
        self.task_header_label.configure(text=self.tr("task_title"))
        self.choose_button_label.configure(text=self.tr("choose_mod"))
        self.target_hint_label.configure(text=self.tr("target_hint"))
        self.stable_texture_row.set_text(self.tr("stable_texture"), self.tr("stable_texture_desc"))
        self.fixmenu_row.set_text(self.tr("fix_menu"), self.tr("fix_menu_desc"))
        self.fix_button.set_text(self.tr("fix_title"), self.tr("fix_tip"), "", self.tr("fix_action"))
        self.preview_button.set_text(self.tr("preview_title"), self.tr("preview_tip"), "", self.tr("preview_action"))
        self.rollback_button.set_text(self.tr("rollback_title"), self.tr("rollback_tip"), "", self.tr("rollback_action"))
        self.log_title_label.configure(text=self.tr("log_title"))
        if hasattr(self.log_toggle, "set_label"):
            self.log_toggle.set_label(self.tr("debug_log"))  # type: ignore[attr-defined]
        if hasattr(self.log_toggle, "set_progress"):
            self.log_toggle.set_progress(self.log_toggle.progress)  # type: ignore[attr-defined]
        self.export_log_button.configure(text=self.tr("export_log"))
        self.clear_log_button.configure(text=self.tr("clear_log"))
        self.refresh_default_log_language()
        if self.update_button is not None:
            self.update_button.configure(text=self.tr("check_update"))

    def rebuild_ui_preserving_log(self) -> None:
        log_text = self.log_box.get("1.0", "end-1c") if self.log_box is not None else None
        was_expanded = self.log_expanded
        for child in self.root.winfo_children():
            child.destroy()
        self.log_box = None
        self.log_shell = None
        self.log_inner = None
        self.log_header = None
        self.log_area = None
        self.log_toggle = None
        self.log_expanded = was_expanded
        self.debug_log.set(was_expanded)
        self.build_ui(log_text=log_text)

    def on_root_configure(self, event: tk.Event[tk.Misc]) -> None:
        if event.widget is not self.root:
            return
        if self.log_animating or not self.log_expanded:
            return
        if self.log_area is None or not self.log_area.winfo_ismapped():
            return
        if self.root_resize_after_id is not None:
            with contextlib.suppress(tk.TclError):
                self.root.after_cancel(self.root_resize_after_id)

        def sync_height() -> None:
            self.root_resize_after_id = None
            if self.log_area is None or not self.log_expanded or self.log_animating:
                return
            target_height = self.available_log_height()
            if target_height > 0 and abs(self.log_area.winfo_height() - target_height) > 1:
                self.log_area.configure(height=target_height)
                self.set_log_shell_height(self.log_shell_height_for_area(target_height))
                self.set_log_visual_progress(1.0, target_height)

        self.root_resize_after_id = self.root.after(ROOT_RESIZE_SYNC_DELAY_MS, sync_height)

    def _build_ui_legacy_unused(self, log_text: str | None = None) -> None:
        self.colors = THEMES[self.theme_name]
        self.root.configure(bg=self.colors["bg"])
        self.action_buttons = []
        self.theme_switches = []

        main = self.theme_widget(tk.Frame(self.root, bg=self.colors["bg"], padx=26, pady=0), bg="bg")
        self.main_frame = main
        main.pack(fill=tk.BOTH, expand=True)

        header = self.theme_widget(tk.Frame(main, bg=self.colors["bg"]), bg="bg")
        header.pack(fill=tk.X, pady=(24, 0))

        self.theme_widget(tk.Label(
            header,
            text="EFMI模组修复v1.0  |",
            bg=self.colors["bg"],
            fg=self.colors["muted"],
            font=(UI_FONT_FAMILY, UI_TITLE_FONT_SIZE),
        ), bg="bg", fg="muted").pack(side=tk.LEFT)

        self.theme_widget(tk.Label(
            header,
            text="by SWAGost",
            bg=self.colors["bg"],
            fg=self.colors["blue"],
            font=(UI_FONT_FAMILY, UI_TITLE_FONT_SIZE),
        ), bg="bg", fg="blue").pack(side=tk.LEFT, padx=(10, 0))

        self.separator(main)

        self.section_label(main, "-- 目标文件夹 --")
        target_shell = RoundedPanel(
            main,
            self.colors,
            padx=18,
            pady=18,
            radius=PANEL_RADIUS,
            min_height=84,
        )
        target_shell.pack(fill=tk.X, padx=(5, 5), pady=(7, 18))
        target_panel = target_shell.content

        choose_btn = self.make_button(
            target_panel,
            "[+] 选择 Mod 文件夹",
            command=self.choose_dir,
            width=18,
            select_effect=True,
        )
        choose_btn.pack(side=tk.LEFT)

        self.path_label = self.theme_widget(tk.Label(
            target_panel,
            textvariable=self.target_dir,
            bg=self.colors["panel"],
            fg=self.colors["text"],
            anchor="w",
            font=(UI_FONT_FAMILY, UI_BODY_FONT_SIZE),
        ), bg="panel", fg="text")
        self.path_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(14, 0))

        self.section_label(main, "-- 修复选项 --")
        options_shell = RoundedPanel(
            main,
            self.colors,
            padx=18,
            pady=18,
            radius=PANEL_RADIUS,
            min_height=154,
        )
        options_shell.pack(fill=tk.X, padx=(5, 5), pady=(7, 12))
        options_panel = options_shell.content

        stable_texture_check = RoundedCheck(
            options_panel,
            self.stable_texture,
            "稳定纹理",
            "把材质转换为Rabbitfx稳定纹理，修复完后mod异常时可尝试启用，部分mod可用",
            self.colors,
        )
        stable_texture_check.pack(fill=tk.X, pady=(0, 10))

        fixmenu_check = RoundedCheck(
            options_panel,
            self.fixmenu,
            "修复菜单",
            "当菜单无法呼出时，修复菜单丢失问题",
            self.colors,
        )
        fixmenu_check.pack(fill=tk.X)

        action_row = self.theme_widget(tk.Frame(main, bg=self.colors["bg"]), bg="bg")
        action_row.pack(fill=tk.X, pady=(0, 12))

        self.fix_button = self.make_button(
            action_row,
            "[>>] 一键修复",
            command=lambda: self.run_fixer(dry_run=False),
            bg=self.colors["green"],
            active=self.colors["green_dark"],
            width=14,
            bg_key="green",
            active_key="green_dark",
            select_effect=True,
        )
        self.fix_button.pack(side=tk.LEFT, padx=(0, 10))

        self.preview_button = self.make_button(
            action_row,
            "[?] 预览扫描",
            command=lambda: self.run_fixer(dry_run=True),
            bg=self.colors["blue"],
            active=self.colors["blue_dark"],
            width=14,
            bg_key="blue",
            active_key="blue_dark",
            select_effect=True,
        )
        self.preview_button.pack(side=tk.LEFT, padx=(0, 10))

        self.rollback_button = self.make_button(
            action_row,
            "[<<] 回滚管理",
            command=self.open_rollback_manager,
            bg=self.colors["blue_dark"],
            active="#2872a3",
            width=14,
            bg_key="blue_dark",
            select_effect=True,
        )
        self.rollback_button.pack(side=tk.LEFT)

        self.separator(main)

        toolbar = self.theme_widget(tk.Frame(main, bg=self.colors["bg"]), bg="bg")
        toolbar.pack(fill=tk.X, pady=(0, 10))

        self.make_button(
            toolbar,
            "刷新数据配置",
            command=self.refresh_config,
            bg=self.colors["soft_button"],
            active=self.colors["soft_button_active"],
            fg=self.colors["text"],
            width=14,
            bg_key="soft_button",
            active_key="soft_button_active",
            fg_key="text",
        ).pack(side=tk.LEFT)

        theme_switch = ThemeSwitch(toolbar, self)
        theme_switch.pack(side=tk.LEFT, padx=(10, 0))

        self.log_toggle = DisclosureToggle(toolbar, self, "调试日志", self.toggle_log_panel)
        self.log_toggle.pack(side=tk.RIGHT, padx=(10, 0))

        self.make_button(
            toolbar,
            "导出日志",
            command=self.export_log,
            bg=self.colors["soft_button"],
            active=self.colors["soft_button_active"],
            fg=self.colors["text"],
            width=10,
            bg_key="soft_button",
            active_key="soft_button_active",
            fg_key="text",
        ).pack(side=tk.RIGHT, padx=(8, 0))

        self.make_button(
            toolbar,
            "清空日志",
            command=self.clear_log,
            bg=self.colors["soft_button"],
            active=self.colors["soft_button_active"],
            fg=self.colors["text"],
            width=10,
            bg_key="soft_button",
            active_key="soft_button_active",
            fg_key="text",
        ).pack(side=tk.RIGHT)

        self.log_area = self.theme_widget(
            tk.Frame(main, bg=self.colors["bg"], height=0),
            bg="bg",
        )
        self.log_area.pack(fill=tk.X, expand=False, padx=(5, 5), pady=(7, 0))
        self.log_area.pack_propagate(False)

        self.log_title_label = self.theme_widget(tk.Label(
            self.log_area,
            text="-- 日志 --",
            bg=self.colors["bg"],
            fg=self.colors["muted"],
            font=(UI_FONT_FAMILY, UI_SECTION_FONT_SIZE),
        ), bg="bg", fg="muted")
        self.log_title_label.pack(anchor="w")

        log_shell = RoundedPanel(
            self.log_area,
            self.colors,
            padx=1,
            pady=1,
            radius=PANEL_RADIUS,
            min_height=1,
            fill_key="log_bg",
            stretch_content=True,
        )
        log_shell.pack(fill=tk.BOTH, expand=True)
        log_frame = log_shell.content

        self.log_box = self.theme_widget(tk.Text(
            log_frame,
            bg=self.colors["log_bg"],
            fg=self.colors["log_text"],
            insertbackground=self.colors["log_text"],
            relief=tk.FLAT,
            wrap=tk.WORD,
            padx=12,
            pady=10,
            font=(LOG_FONT_FAMILY, 14),
        ), bg="log_bg", fg="log_text", insertbackground="log_text")
        self.log_box.pack(fill=tk.BOTH, expand=True)
        self.bind_log_mousewheel(log_frame)

        if log_text is None:
            self.log(
                "================================================\n"
                "EFMI 模组修复 已就绪\n"
                "* 选择目标 Mod 文件夹\n"
                "* 勾选“修复菜单”后点击“一键修复”\n"
                "* 每次写入都会生成 before/after 备份，可在回滚管理中切换\n"
            )
        else:
            self.log_box.insert(tk.END, log_text)
            self.scroll_log_to_bottom(defer=True)

        for _ in range(2):
            self.root.update_idletasks()
        self.log_area.pack_forget()
        self.update_collapsed_window_height()
        self.sync_log_panel_state(animated=False)

        if self.running:
            self.set_running(True)

    def reset_contour_backgrounds(self) -> None:
        if self.contour_redraw_after_id is not None:
            with contextlib.suppress(tk.TclError):
                self.root.after_cancel(self.contour_redraw_after_id)
        self.contour_redraw_after_id = None
        self.contour_photo_refs = {}
        self.contour_layers = []

    def schedule_contour_redraw(self, delay_ms: int = CONTOUR_REDRAW_DELAY_MS) -> None:
        if self.log_animating and delay_ms >= CONTOUR_REDRAW_DELAY_MS:
            return
        if self.contour_redraw_after_id is not None:
            with contextlib.suppress(tk.TclError):
                self.root.after_cancel(self.contour_redraw_after_id)
        self.contour_redraw_after_id = self.root.after(delay_ms, self.redraw_contour_backgrounds)

    def load_contour_source_image(self) -> object | None:
        if Image is None:
            return None
        if self.contour_source_image is not None:
            return self.contour_source_image

        image_path = app_resource_path(CONTOUR_SOURCE_IMAGE_NAME)
        if not image_path.exists():
            return None

        try:
            with Image.open(image_path) as image:  # type: ignore[union-attr]
                self.contour_source_image = image.convert("L")
        except Exception:
            self.contour_source_image = None
        return self.contour_source_image

    def contour_tile(self, colors: dict[str, str], density: float) -> object | None:
        if Image is None or ImageEnhance is None or ImageOps is None:
            return None

        key = (colors["bg"], colors["muted"], round(density, 2))
        if key in self.contour_tile_cache:
            return self.contour_tile_cache[key]

        source = self.load_contour_source_image()
        if source is None:
            return None

        target_size = max(760, min(1120, round(900 / max(0.55, density))))
        resampling = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
        gray = source.resize((target_size, target_size), resampling)  # type: ignore[attr-defined]
        alpha = ImageOps.invert(gray)
        alpha = ImageEnhance.Contrast(alpha).enhance(1.55)
        alpha = ImageEnhance.Brightness(alpha).enhance(0.78)
        alpha = alpha.point(lambda value: 0 if value < 12 else min(118, int(value)))

        line_rgb = hex_to_rgb(mix_color(colors["bg"], colors["muted"], 0.54))
        tile = Image.new("RGBA", gray.size, (*line_rgb, 0))  # type: ignore[union-attr]
        tile.putalpha(alpha)
        self.contour_tile_cache[key] = tile
        return tile

    def render_contour_photo(
        self,
        width: int,
        height: int,
        colors: dict[str, str],
        density: float,
        origin_x: int,
        origin_y: int,
    ) -> object | None:
        if Image is None or ImageTk is None:
            return None
        tile = self.contour_tile(colors, density)
        if tile is None:
            return None

        bg = Image.new("RGBA", (width, height), (*hex_to_rgb(colors["bg"]), 255))  # type: ignore[union-attr]
        tile_width, tile_height = tile.size  # type: ignore[attr-defined]
        start_x = -(origin_x % tile_width)
        start_y = -(origin_y % tile_height)
        for y in range(start_y, height, tile_height):
            for x in range(start_x, width, tile_width):
                bg.alpha_composite(tile, (x, y))  # type: ignore[attr-defined]
        return ImageTk.PhotoImage(bg)  # type: ignore[union-attr]

    def redraw_contour_backgrounds(self) -> None:
        self.contour_redraw_after_id = None
        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        colors = THEMES[self.theme_name]
        live_layers: list[tuple[tk.Canvas, tk.Widget, int, float, int]] = []
        for background, parent, phase_offset, density, top_offset in self.contour_layers:
            try:
                if not background.winfo_exists() or not parent.winfo_exists():
                    continue
                width = parent.winfo_width()
                height = max(1, parent.winfo_height() - top_offset)
                if width <= 1 or height <= 1:
                    live_layers.append((background, parent, phase_offset, density, top_offset))
                    continue
                background.place_configure(x=0, y=top_offset, relwidth=1, height=height)
                origin_x = parent.winfo_rootx() - root_x
                origin_y = parent.winfo_rooty() - root_y + top_offset
                signature = (
                    width,
                    height,
                    colors["bg"],
                    colors["muted"],
                    round(density, 2),
                    origin_x,
                    origin_y,
                )
                if getattr(background, "_contour_signature", None) != signature:
                    photo = self.render_contour_photo(width, height, colors, density, origin_x, origin_y)
                    background.delete("contours")
                    if photo is None:
                        draw_uniform_contours(
                            background,
                            width,
                            height,
                            colors,
                            phase_offset,
                            density,
                            origin_x,
                            origin_y,
                        )
                        self.contour_photo_refs.pop(id(background), None)
                    else:
                        background.create_image(0, 0, anchor="nw", image=photo, tags="contours")
                        self.contour_photo_refs[id(background)] = photo
                    background._contour_signature = signature  # type: ignore[attr-defined]
                background.tk.call("lower", background._w)
                live_layers.append((background, parent, phase_offset, density, top_offset))
            except tk.TclError:
                continue
        self.contour_layers = live_layers

    def attach_contour_background(
        self,
        parent: tk.Widget,
        phase_offset: int,
        density: float = 1.0,
        top_offset: int = 0,
    ) -> tk.Canvas:
        background = tk.Canvas(parent, bg=self.colors["bg"], highlightthickness=0, bd=0)
        background.place(x=0, y=top_offset, relwidth=1, height=1)
        background.tk.call("lower", background._w)
        self.contour_layers.append((background, parent, phase_offset, density, top_offset))
        parent.bind("<Configure>", lambda _event: self.schedule_contour_redraw(), add="+")
        self.schedule_contour_redraw(delay_ms=1)
        return background

    def draw_backdrop_header(self, canvas: tk.Canvas, width: int, height: int) -> None:
        canvas.delete("all")
        base_colors = THEMES[self.theme_name]
        origin_x = canvas.winfo_rootx() - self.root.winfo_rootx()
        origin_y = canvas.winfo_rooty() - self.root.winfo_rooty()
        draw_uniform_contours(canvas, width, height, base_colors, phase_offset=1, density=0.75, origin_x=origin_x, origin_y=origin_y)
        canvas.create_line(0, height - 3, width, height - 3, fill="#2a3339")
        canvas.create_line(0, height - 3, 70, height - 3, fill=base_colors["accent_dim"], width=2)
        canvas.create_line(70, height - 3, 90, 16, fill=base_colors["accent"], width=3)

    def tech_section_header(self, parent: tk.Widget, icon: str, title: str, _subtitle: str = "") -> tk.Label:
        header = self.theme_widget(tk.Frame(parent, bg=self.colors["panel"]), bg="panel")
        header.pack(fill=tk.X)
        if icon == "search":
            SearchHeaderIcon(header, self.colors).pack(side=tk.LEFT, padx=(0, 8))
        else:
            self.theme_widget(tk.Label(
                header,
                text=icon,
                bg=self.colors["panel"],
                fg=self.colors["accent"],
                font=(SYMBOL_FONT_FAMILY, 15),
            ), bg="panel", fg="accent").pack(side=tk.LEFT, padx=(0, 8))
        title_label = self.theme_widget(tk.Label(
            header,
            text=title,
            bg=self.colors["panel"],
            fg=self.colors["text"],
            font=(UI_FONT_FAMILY, UI_SECTION_FONT_SIZE),
        ), bg="panel", fg="text")
        title_label.pack(side=tk.LEFT)
        return title_label

    def build_ui(self, log_text: str | None = None) -> None:
        self.colors = THEMES[self.theme_name]
        self.root.configure(bg=self.colors["bg"])
        self.action_buttons = []
        self.theme_switches = []
        self.language_switches = []
        self.reset_contour_backgrounds()

        main = self.theme_widget(tk.Frame(self.root, bg=self.colors["bg"], padx=10, pady=0), bg="bg")
        self.main_frame = main
        main.pack(fill=tk.BOTH, expand=True)
        self.attach_contour_background(main, phase_offset=1, density=0.62, top_offset=CONTOUR_TOP_OFFSET)

        top_bar = self.theme_widget(tk.Frame(main, bg=self.colors["bg"], height=42), bg="bg")
        top_bar.pack(fill=tk.X)
        top_bar.pack_propagate(False)

        title_wrap = self.theme_widget(tk.Frame(top_bar, bg=self.colors["bg"]), bg="bg")
        title_wrap.pack(side=tk.LEFT, fill=tk.Y)
        self.app_title_label = self.theme_widget(tk.Label(
            title_wrap,
            text=f"{self.tr('app_header')}  v{APP_VERSION}",
            bg=self.colors["bg"],
            fg=self.colors["text"],
            font=(UI_FONT_FAMILY, 14),
        ), bg="bg", fg="text")
        self.app_title_label.pack(side=tk.LEFT, pady=(12, 0))
        accent = tk.Canvas(title_wrap, width=54, height=16, bg=self.colors["bg"], highlightthickness=0, bd=0)
        accent.pack(side=tk.LEFT, padx=(10, 0), pady=(16, 0))
        accent.create_line(0, 12, 32, 12, fill=self.colors["accent_dim"], width=2)
        accent.create_line(32, 12, 48, 0, fill=self.colors["accent"], width=3)

        status_wrap = self.theme_widget(tk.Frame(top_bar, bg=self.colors["bg"]), bg="bg")
        status_wrap.pack(side=tk.RIGHT, fill=tk.Y)
        LanguageSwitch(status_wrap, self).pack(side=tk.RIGHT, pady=(6, 0))
        self.update_button = self.make_button(
            status_wrap,
            self.tr("check_update"),
            command=lambda: self.start_update_check(manual=True),
            bg=self.colors["soft_button"],
            active=self.colors["soft_button_active"],
            fg=self.colors["text"],
            width=8,
            bg_key="soft_button",
            active_key="soft_button_active",
            fg_key="text",
        )
        self.update_button.pack(side=tk.RIGHT, padx=(0, 10), pady=(6, 0))

        content = self.theme_widget(tk.Frame(main, bg=self.colors["bg"]), bg="bg")
        content.pack(fill=tk.X, pady=(44, 0))
        self.attach_contour_background(content, phase_offset=1, density=0.62)
        content.grid_columnconfigure(0, weight=58, minsize=630)
        content.grid_columnconfigure(1, weight=50, minsize=520)
        content.grid_rowconfigure(0, weight=1)

        left_column = self.theme_widget(tk.Frame(content, bg=self.colors["bg"]), bg="bg")
        right_column = self.theme_widget(tk.Frame(content, bg=self.colors["bg"]), bg="bg")
        left_column.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        right_column.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self.attach_contour_background(left_column, phase_offset=1, density=0.62)
        self.attach_contour_background(right_column, phase_offset=1, density=0.62)

        target_shell = TechPanel(left_column, self.colors, padx=18, pady=14, min_height=176)
        target_shell.pack(fill=tk.X, pady=(0, 14))
        target_panel = target_shell.content
        self.target_header_label = self.tech_section_header(target_panel, "search", self.tr("target_title"), self.tr("target_sub"))

        path_box = self.theme_widget(
            tk.Frame(target_panel, bg=self.colors["panel"], highlightthickness=1, highlightbackground=self.colors["border"]),
            bg="panel",
            highlightbackground="border",
        )
        path_box.pack(fill=tk.X, pady=(18, 0))
        path_box.grid_columnconfigure(1, weight=1)
        self.choose_button_label = self.theme_widget(tk.Label(
            path_box,
            text=self.tr("choose_mod"),
            bg=self.colors["bg"],
            fg=self.colors["accent"],
            font=(UI_FONT_FAMILY, 13),
            padx=16,
            pady=8,
            cursor="hand2",
            highlightthickness=1,
            highlightbackground=self.colors["accent_dim"],
        ), bg="bg", fg="accent", highlightbackground="accent_dim")
        self.choose_button_label.grid(row=0, column=0, sticky="w", padx=(20, 16), pady=12)
        self.choose_button_label.bind("<Button-1>", lambda _event: self.choose_dir())
        self.path_label = self.theme_widget(tk.Label(
            path_box,
            textvariable=self.target_dir,
            bg=self.colors["panel"],
            fg=self.colors["text"],
            anchor="w",
            justify=tk.LEFT,
            width=1,
            wraplength=420,
            font=(UI_FONT_FAMILY, 10),
        ), bg="panel", fg="text")
        self.path_label.grid(row=0, column=1, sticky="ew", pady=12)
        self.path_label.bind(
            "<Configure>",
            lambda event: self.path_label.configure(wraplength=max(260, event.width)),
        )
        folder_btn = self.theme_widget(
            tk.Label(path_box, text="▣", bg=self.colors["panel"], fg=self.colors["muted"], font=(SYMBOL_FONT_FAMILY, 21), padx=12),
            bg="panel",
            fg="muted",
        )
        folder_btn.grid(row=0, column=2, sticky="e", padx=(8, 16), pady=12)
        folder_btn.bind("<Button-1>", lambda _event: self.choose_dir())
        self.target_hint_label = self.theme_widget(tk.Label(
            target_panel,
            text=self.tr("target_hint"),
            bg=self.colors["panel"],
            fg=self.colors["muted"],
            font=(UI_FONT_FAMILY, 11),
            anchor="w",
            justify=tk.LEFT,
            width=1,
            wraplength=420,
        ), bg="panel", fg="muted")
        self.target_hint_label.pack(anchor="w", fill=tk.X, pady=(18, 0))
        self.target_hint_label.bind(
            "<Configure>",
            lambda event: self.target_hint_label.configure(wraplength=max(260, event.width)),
        )

        options_shell = TechPanel(left_column, self.colors, padx=18, pady=14, min_height=242)
        options_shell.pack(fill=tk.X)
        options_panel = options_shell.content
        self.options_header_label = self.tech_section_header(options_panel, "▧", self.tr("repair_title"), self.tr("repair_sub"))
        self.stable_texture_row = TechOptionRow(
            options_panel,
            self.stable_texture,
            "▱",
            self.tr("stable_texture"),
            self.tr("stable_texture_desc"),
            self.colors,
        )
        self.stable_texture_row.pack(fill=tk.X, pady=(18, 1))
        self.fixmenu_row = TechOptionRow(
            options_panel,
            self.fixmenu,
            "☷",
            self.tr("fix_menu"),
            self.tr("fix_menu_desc"),
            self.colors,
        )
        self.fixmenu_row.pack(fill=tk.X, pady=(1, 0))

        task_shell = TechPanel(right_column, self.colors, padx=18, pady=14, min_height=432, stretch_content=True)
        task_shell.pack(fill=tk.BOTH, expand=True)
        task_panel = task_shell.content
        self.task_header_label = self.tech_section_header(task_panel, "☑", self.tr("task_title"), self.tr("task_sub"))
        task_cards = self.theme_widget(tk.Frame(task_panel, bg=self.colors["panel"]), bg="panel")
        task_cards.pack(fill=tk.BOTH, expand=True, pady=(18, 0))
        task_cards.grid_columnconfigure(0, weight=1)
        for row in range(3):
            task_cards.grid_rowconfigure(row, weight=1, uniform="task_cards")
        self.fix_button = TechTaskCard(task_cards, self.colors, self.tr("fix_title"), self.tr("fix_tip"), "", "⚡", self.tr("fix_action"), lambda: self.run_fixer(dry_run=False))
        self.fix_button.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        self.preview_button = TechTaskCard(task_cards, self.colors, self.tr("preview_title"), self.tr("preview_tip"), "", "⌖", self.tr("preview_action"), lambda: self.run_fixer(dry_run=True))
        self.preview_button.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        self.rollback_button = TechTaskCard(task_cards, self.colors, self.tr("rollback_title"), self.tr("rollback_tip"), "", "◀", self.tr("rollback_action"), self.open_rollback_manager)
        self.rollback_button.grid(row=2, column=0, sticky="nsew")

        self.log_shell = TechPanel(main, self.colors, padx=18, pady=12, min_height=1, fill_key="panel", stretch_content=True)
        self.log_shell.pack(fill=tk.X, expand=False, pady=(12, 0))
        log_panel = self.log_shell.content
        self.log_header = self.theme_widget(tk.Frame(log_panel, bg=self.colors["panel"]), bg="panel")
        self.log_header.pack(fill=tk.X)
        self.log_title_label = self.theme_widget(tk.Label(
            self.log_header,
            text=self.tr("log_title"),
            bg=self.colors["panel"],
            fg=self.colors["text"],
            font=(UI_FONT_FAMILY, UI_SECTION_FONT_SIZE),
        ), bg="panel", fg="text")
        self.log_title_label.pack(side=tk.LEFT)
        self.log_toggle = LogPowerSwitch(self.log_header, self, self.tr("debug_log"), self.toggle_log_panel)
        self.log_toggle.pack(side=tk.RIGHT, padx=(18, 0))
        self.export_log_button = self.make_button(self.log_header, self.tr("export_log"), command=self.export_log, bg=self.colors["soft_button"], active=self.colors["soft_button_active"], fg=self.colors["text"], width=8, bg_key="soft_button", active_key="soft_button_active", fg_key="text")
        self.export_log_button.pack(side=tk.RIGHT, padx=(8, 0))
        self.clear_log_button = self.make_button(self.log_header, self.tr("clear_log"), command=self.clear_log, bg=self.colors["soft_button"], active=self.colors["soft_button_active"], fg=self.colors["text"], width=8, bg_key="soft_button", active_key="soft_button_active", fg_key="text")
        self.clear_log_button.pack(side=tk.RIGHT)

        self.log_area = self.theme_widget(tk.Frame(log_panel, bg=self.colors["panel"], height=0), bg="panel")
        self.log_area.pack(fill=tk.BOTH, expand=False, pady=(8, 0))
        self.log_area.pack_propagate(False)
        self.log_inner = TechPanel(self.log_area, self.colors, padx=8, pady=8, min_height=1, fill_key="log_bg", stretch_content=True)
        self.log_inner.place(x=0, y=0, relwidth=1, height=1)
        log_frame = self.log_inner.content
        self.log_box = self.theme_widget(tk.Text(
            log_frame,
            bg=self.colors["log_bg"],
            fg=self.colors["log_text"],
            insertbackground=self.colors["log_text"],
            relief=tk.FLAT,
            wrap=tk.WORD,
            padx=12,
            pady=8,
            font=(LOG_FONT_FAMILY, 11),
        ), bg="log_bg", fg="log_text", insertbackground="log_text")
        self.log_box.pack(fill=tk.BOTH, expand=True)
        self.bind_log_mousewheel(log_frame)

        if log_text is None:
            self.replace_log_with_default_text()
        else:
            self.log_box.insert(tk.END, log_text)
            self.scroll_log_to_bottom(defer=True)
            self.log_default_text = log_text if log_text == self.default_log_text() else None

        self.log_area.pack_forget()
        self.set_log_shell_height(self.collapsed_log_shell_height())
        self.update_collapsed_window_height()
        self.sync_log_panel_state(animated=False)

        if self.running:
            self.set_running(True)

    def separator(self, parent: tk.Widget, pady: tuple[int, int] = (16, 14)) -> None:
        self.theme_widget(tk.Frame(parent, bg=self.colors["border"], height=1), bg="border").pack(fill=tk.X, pady=pady)

    def section_label(self, parent: tk.Widget, text: str) -> None:
        self.theme_widget(tk.Label(
            parent,
            text=text,
            bg=self.colors["bg"],
            fg=self.colors["muted"],
            font=(UI_FONT_FAMILY, UI_SECTION_FONT_SIZE),
        ), bg="bg", fg="muted").pack(anchor="w")

    def make_button(
        self,
        parent: tk.Widget,
        text: str,
        command: object | None = None,
        bg: str | None = None,
        active: str | None = None,
        fg: str = "white",
        width: int | None = None,
        bg_key: str | None = None,
        active_key: str | None = None,
        fg_key: str | None = None,
        select_effect: bool = False,
    ) -> RoundedButton:
        button = RoundedButton(
            parent,
            text=text,
            command=command,
            bg=bg or self.colors["blue"],
            activebackground=active or self.colors["blue_dark"],
            fg=fg,
            activeforeground=fg,
            width=width,
            font=(UI_FONT_FAMILY, UI_BODY_FONT_SIZE),
            select_effect=select_effect,
        )
        roles: dict[str, str] = {}
        if bg_key is not None:
            roles["bg"] = bg_key
        elif bg is None:
            roles["bg"] = "blue"
        if active_key is not None:
            roles["activebackground"] = active_key
        elif active is None:
            roles["activebackground"] = "blue_dark"
        if fg_key is not None:
            roles["fg"] = fg_key
            roles["activeforeground"] = fg_key
        self.theme_widget(button, **roles)
        return button

    def bind_log_mousewheel(self, container: tk.Widget) -> None:
        if self.log_box is None:
            return

        def scroll_units(delta: int) -> int:
            if delta == 0:
                return 0
            units = int(delta / 120)
            if units == 0:
                units = 1 if delta > 0 else -1
            return -units

        def on_mousewheel(event: tk.Event[tk.Misc]) -> str:
            if self.log_box is None:
                return "break"
            units = scroll_units(int(getattr(event, "delta", 0)))
            if units:
                self.log_box.yview_scroll(units * 3, "units")
            return "break"

        def on_scroll_up(_event: tk.Event[tk.Misc]) -> str:
            if self.log_box is not None:
                self.log_box.yview_scroll(-3, "units")
            return "break"

        def on_scroll_down(_event: tk.Event[tk.Misc]) -> str:
            if self.log_box is not None:
                self.log_box.yview_scroll(3, "units")
            return "break"

        for widget in (container, self.log_box):
            widget.bind("<MouseWheel>", on_mousewheel)
            widget.bind("<Button-4>", on_scroll_up)
            widget.bind("<Button-5>", on_scroll_down)

    def toggle_log_panel(self) -> None:
        if self.log_animating:
            return
        self.sync_log_panel_state(animated=True, expanded=not self.log_expanded)

    def pack_log_area(self) -> None:
        if self.log_area is None:
            return
        if not self.log_area.winfo_ismapped():
            self.log_area.pack(fill=tk.BOTH, expand=False, pady=(8, 0))
            self.log_area.pack_propagate(False)

    def set_log_title_progress(self, progress: float) -> None:
        if self.log_title_label is None:
            return
        self.log_title_label.configure(fg=self.colors["text"])

    def collapsed_log_shell_height(self) -> int:
        if self.log_shell is None:
            return 1
        self.root.update_idletasks()
        header_height = 0
        if self.log_header is not None:
            header_height = max(self.log_header.winfo_reqheight(), self.log_header.winfo_height())
        return max(1, header_height + self.log_shell.pady * 2 + 2)

    def log_shell_height_for_area(self, area_height: int) -> int:
        area_height = max(0, int(round(area_height)))
        gap = LOG_AREA_TOP_GAP if area_height > 0 else 0
        return self.collapsed_log_shell_height() + gap + area_height

    def set_log_shell_height(self, height: int) -> None:
        if self.log_shell is None:
            return
        height = max(1, int(round(height)))
        self.log_shell.configure(height=height)
        self.log_shell.canvas.configure(height=height)
        if self.log_animating:
            return
        self.log_shell.schedule_draw(delay_ms=1)

    def set_log_visual_progress(self, progress: float, area_height: int | None = None) -> None:
        if self.log_area is None or self.log_inner is None or self.log_box is None:
            return
        progress = clamp01(progress)
        if area_height is None:
            area_height = self.log_area.winfo_height()
        area_height = max(1, int(round(area_height)))
        offset = round(-LOG_ANIMATION_SLIDE_OFFSET * (1.0 - progress))
        self.log_inner.place_configure(x=0, y=offset, relwidth=1, height=area_height)

        panel_color = self.colors["panel"]
        log_bg = mix_color(panel_color, self.colors["log_bg"], progress)
        log_text = mix_color(log_bg, self.colors["log_text"], progress)
        animated_colors = dict(self.colors)
        animated_colors["log_bg"] = log_bg
        animated_colors["border"] = mix_color(panel_color, self.colors["border"], progress)
        animated_colors["muted"] = mix_color(panel_color, self.colors["muted"], progress)
        animated_colors["accent"] = mix_color(panel_color, self.colors["accent"], progress)
        self.log_inner.set_colors(animated_colors if progress < 1.0 else self.colors)
        self.log_box.configure(bg=log_bg, fg=log_text, insertbackground=log_text)

    def begin_log_animation_timer_resolution(self) -> None:
        if sys.platform != "win32" or self.log_timer_resolution_active:
            return
        with contextlib.suppress(AttributeError, OSError, ValueError):
            if ctypes.windll.winmm.timeBeginPeriod(LOG_ANIMATION_TIMER_RESOLUTION_MS) == 0:
                self.log_timer_resolution_active = True

    def end_log_animation_timer_resolution(self) -> None:
        if sys.platform != "win32" or not self.log_timer_resolution_active:
            return
        with contextlib.suppress(AttributeError, OSError, ValueError):
            ctypes.windll.winmm.timeEndPeriod(LOG_ANIMATION_TIMER_RESOLUTION_MS)
        self.log_timer_resolution_active = False

    def set_window_height(self, height: int) -> None:
        width = self.root.winfo_width()
        if width <= 1:
            width = DEFAULT_WINDOW_WIDTH
        self.root.geometry(f"{width}x{max(self.collapsed_window_height, height)}")

    def update_collapsed_window_height(self, apply_geometry: bool = False) -> int:
        if self.main_frame is None:
            return self.collapsed_window_height
        if self.log_area is not None and not self.log_area.winfo_ismapped() and not self.log_animating:
            self.set_log_shell_height(self.collapsed_log_shell_height())
        self.root.update_idletasks()
        height = max(
            MIN_COLLAPSED_WINDOW_HEIGHT,
            self.main_frame.winfo_reqheight() + COLLAPSED_BOTTOM_PADDING,
        )
        self.collapsed_window_height = height
        self.root.minsize(MIN_WINDOW_WIDTH, height)
        if apply_geometry:
            self.set_window_height(height)
        return height

    def available_log_height(self) -> int:
        if self.log_shell is None or self.main_frame is None:
            return 0
        self.root.update_idletasks()
        root_bottom = self.root.winfo_rooty() + self.root.winfo_height() - COLLAPSED_BOTTOM_PADDING
        shell_top = self.log_shell.winfo_rooty()
        available_shell_height = max(0, root_bottom - shell_top)
        return max(0, available_shell_height - self.collapsed_log_shell_height() - LOG_AREA_TOP_GAP)

    def sync_log_panel_state(self, animated: bool, expanded: bool | None = None) -> None:
        if self.log_area is None or self.log_shell is None or self.log_toggle is None:
            return

        target_expanded = self.debug_log.get() if expanded is None else expanded
        target_progress = 1.0 if target_expanded else 0.0
        collapsed_shell_height = self.collapsed_log_shell_height()

        if not animated:
            if target_expanded:
                self.set_log_shell_height(collapsed_shell_height)
                self.update_collapsed_window_height()
                self.pack_log_area()
                target_window_height = max(
                    EXPANDED_WINDOW_HEIGHT,
                    self.collapsed_window_height + LOG_AREA_TOP_GAP + DEFAULT_LOG_AREA_HEIGHT,
                )
                self.set_window_height(target_window_height)
                self.root.update_idletasks()
                target_height = max(
                    DEFAULT_LOG_AREA_HEIGHT,
                    target_window_height - self.collapsed_window_height - LOG_AREA_TOP_GAP,
                    self.available_log_height(),
                )
            else:
                target_height = 0
            self.log_expanded = target_expanded
            self.debug_log.set(target_expanded)
            self.log_area.configure(height=target_height)
            self.set_log_shell_height(self.log_shell_height_for_area(target_height))
            self.log_shell.pack_configure(fill=tk.X, expand=False)
            self.set_log_visual_progress(target_progress, target_height if target_expanded else 1)
            self.log_area.pack_configure(
                fill=tk.BOTH if target_expanded else tk.X,
                expand=target_expanded,
            )
            if not target_expanded:
                self.log_area.pack_forget()
                self.set_log_shell_height(collapsed_shell_height)
                self.update_collapsed_window_height(apply_geometry=True)
            self.log_toggle.set_progress(target_progress)
            self.set_log_title_progress(target_progress)
            if target_expanded:
                self.scroll_log_to_bottom(defer=True)
            self.schedule_contour_redraw(delay_ms=1)
            return

        self.log_animating = True
        if target_expanded:
            self.set_log_shell_height(collapsed_shell_height)
            self.update_collapsed_window_height()
            self.pack_log_area()
            self.log_area.configure(height=0)
        else:
            self.set_log_visual_progress(1.0, max(1, self.log_area.winfo_height()))

        self.root.update_idletasks()
        self.log_area.update_idletasks()
        start_window_height = self.root.winfo_height()
        target_window_height = self.collapsed_window_height
        if target_expanded:
            target_window_height = max(
                EXPANDED_WINDOW_HEIGHT,
                self.collapsed_window_height + LOG_AREA_TOP_GAP + DEFAULT_LOG_AREA_HEIGHT,
            )

        target_height = (
            max(
                DEFAULT_LOG_AREA_HEIGHT,
                target_window_height - self.collapsed_window_height - LOG_AREA_TOP_GAP,
            )
            if target_expanded
            else 0
        )
        target_shell_height = self.log_shell_height_for_area(target_height)
        start_progress = self.log_toggle.progress
        self.log_shell.pack_configure(fill=tk.X, expand=False)
        visual_area_height = target_height if target_expanded else max(1, self.log_area.winfo_height())
        if target_expanded:
            self.set_log_shell_height(target_shell_height)
            self.log_area.configure(height=target_height)
            self.log_area.pack_configure(fill=tk.BOTH, expand=False)
            self.set_log_visual_progress(0.0, visual_area_height)

        duration_ms = LOG_ANIMATION_DURATION_MS
        interval_ms = LOG_ANIMATION_INTERVAL_MS
        self.begin_log_animation_timer_resolution()
        start_time = time.perf_counter()
        last_window_height: int | None = None

        def step() -> None:
            nonlocal last_window_height
            linear_progress = clamp01((time.perf_counter() - start_time) * 1000 / duration_ms)
            progress = ease_in_out(linear_progress)
            window_height = round(start_window_height + (target_window_height - start_window_height) * progress)
            arrow_progress = start_progress + (target_progress - start_progress) * progress
            visual_progress = progress if target_expanded else 1.0 - progress
            if window_height != last_window_height:
                self.set_window_height(window_height)
                last_window_height = window_height
            self.set_log_visual_progress(visual_progress, visual_area_height)
            self.log_toggle.set_progress(arrow_progress)
            self.set_log_title_progress(arrow_progress)

            if linear_progress < 1.0:
                self.root.after(interval_ms, step)
                return

            self.log_expanded = target_expanded
            self.debug_log.set(target_expanded)
            self.set_window_height(target_window_height)
            self.set_log_shell_height(target_shell_height)
            self.log_shell.pack_configure(fill=tk.X, expand=False)
            if target_expanded:
                self.pack_log_area()
                self.log_area.configure(height=target_height)
                self.log_area.pack_configure(fill=tk.BOTH, expand=True)
                self.set_log_visual_progress(1.0, target_height)
            else:
                self.set_log_visual_progress(0.0, visual_area_height)
                self.log_area.pack_forget()
                self.set_log_shell_height(collapsed_shell_height)
                collapsed_height = self.update_collapsed_window_height()
                self.set_window_height(collapsed_height)
            self.log_toggle.set_progress(target_progress)
            self.set_log_title_progress(target_progress)
            if target_expanded:
                self.scroll_log_to_bottom(defer=True)
            self.log_animating = False
            self.log_shell.schedule_draw(delay_ms=1)
            self.end_log_animation_timer_resolution()
            self.schedule_contour_redraw(delay_ms=1)

        step()

    def toggle_theme(self) -> None:
        self.start_theme_transition()

    def update_notes_text(self, notes_raw: object) -> str:
        notes = [str(note) for note in notes_raw] if isinstance(notes_raw, list) else []
        return "\n".join(f"- {note}" for note in notes) if notes else self.tr("none")

    def bool_text(self, value: bool) -> str:
        return self.tr("yes") if value else self.tr("no")

    def start_update_check_i18n(self, manual: bool = False) -> None:
        if self.update_check_running:
            return
        self.update_check_running = True
        if manual:
            self.log(f"\n---- {self.tr('update_check_start')} ----")

        def worker() -> None:
            try:
                result = check_and_download_update()
                self.log_queue.put(("update_result", result, manual))
            except Exception as exc:
                self.log_queue.put(("update_error", str(exc), manual))

        threading.Thread(target=worker, daemon=True).start()

    def start_update_download_i18n(self, result: dict[str, object], destination_path: str) -> None:
        if self.update_check_running:
            return
        self.update_check_running = True
        self.log(f"\n---- {self.tr('update_download_start')} ----\n{self.tr('update_save_location')}: {destination_path}")

        def worker() -> None:
            try:
                downloaded = download_update_from_result(result, destination_path=destination_path)
                self.log_queue.put(("update_result", downloaded, True))
            except Exception as exc:
                self.log_queue.put(("update_error", str(exc), True))

        threading.Thread(target=worker, daemon=True).start()

    def handle_update_result_i18n(self, result: dict[str, object], manual: bool) -> None:
        self.update_check_running = False
        status = result.get("status")
        remote_tag = str(result.get("remote_tag") or "")

        if status == "current":
            if manual:
                messagebox.showinfo(self.tr("check_update"), self.tr("update_current_message").format(version=APP_VERSION))
            self.log(f"\n{self.tr('update_current_log').format(local=APP_VERSION, remote=remote_tag)}")
            return

        if status == "no_file":
            self.log(f"\n{self.tr('update_no_file_log').format(remote=remote_tag)}")
            messagebox.showinfo(self.tr("update_available_title"), self.tr("update_no_file_message").format(remote=remote_tag))
            return

        if status == "available":
            asset_name = str(result.get("asset_name") or "")
            required = bool(result.get("required") or False)
            note_text = self.update_notes_text(result.get("release_notes"))
            self.log(
                f"\n{self.tr('update_available_log')}\n"
                f"{self.tr('update_current_version')}: v{APP_VERSION}\n"
                f"{self.tr('update_remote_version')}: {remote_tag}\n"
                f"{self.tr('update_file')}: {asset_name}\n"
                f"{self.tr('update_required')}: {self.bool_text(required)}\n"
                f"{self.tr('update_notes')}:\n{note_text}"
            )
            if messagebox.askyesno(
                self.tr("update_available_title"),
                self.tr("update_available_prompt").format(remote=remote_tag, asset=asset_name, notes=note_text),
            ):
                asset_suffix = Path(asset_name).suffix
                destination = filedialog.asksaveasfilename(
                    title=self.tr("update_choose_save_title"),
                    initialdir=str(APP_DIR),
                    initialfile=safe_download_name(asset_name),
                    defaultextension=asset_suffix,
                    filetypes=[
                        (self.tr("update_file_type"), f"*{asset_suffix}" if asset_suffix else "*.*"),
                        (self.tr("all_files"), "*.*"),
                    ],
                )
                if not destination:
                    self.log(f"\n{self.tr('update_cancel_save')}")
                    return
                destination_path = Path(destination)
                if destination_path.exists() and not messagebox.askyesno(
                    self.tr("overwrite_file_title"),
                    self.tr("overwrite_file_message").format(path=destination_path),
                ):
                    self.log(f"\n{self.tr('update_cancel_overwrite')}")
                    return
                self.start_update_download_i18n(result, destination)
            else:
                self.log(f"\n{self.tr('update_cancel_download')}")
            return

        if status == "downloaded":
            asset_name = str(result.get("asset_name") or "")
            downloaded_path = str(result.get("downloaded_path") or "")
            required = bool(result.get("required") or False)
            note_text = self.update_notes_text(result.get("release_notes"))
            self.log(
                f"\n{self.tr('update_downloaded_log')}\n"
                f"{self.tr('update_version')}: {remote_tag}\n"
                f"{self.tr('update_file')}: {asset_name}\n"
                f"{self.tr('update_location')}: {downloaded_path}\n"
                f"{self.tr('update_required')}: {self.bool_text(required)}\n"
                f"{self.tr('update_notes')}:\n{note_text}"
            )
            messagebox.showinfo(
                self.tr("update_downloaded_title"),
                self.tr("update_downloaded_message").format(remote=remote_tag, path=downloaded_path, notes=note_text),
            )
            return

        self.log(f"\n{self.tr('update_unknown_status')}")

    def handle_update_error_i18n(self, message: str, manual: bool) -> None:
        self.update_check_running = False
        public_message = sanitize_update_error_message(message)
        self.log(f"\n{self.tr('update_error_log').format(message=public_message)}")
        if manual:
            messagebox.showerror(self.tr("update_error_title"), public_message)

    def start_update_check(self, manual: bool = False) -> None:
        return self.start_update_check_i18n(manual)
        if self.update_check_running:
            return
        self.update_check_running = True
        if manual:
            self.log("\n---- 检查更新开始 ----")

        def worker() -> None:
            try:
                result = check_and_download_update()
                self.log_queue.put(("update_result", result, manual))
            except Exception as exc:
                self.log_queue.put(("update_error", str(exc), manual))

        threading.Thread(target=worker, daemon=True).start()

    def start_update_download(self, result: dict[str, object], destination_path: str) -> None:
        return self.start_update_download_i18n(result, destination_path)
        if self.update_check_running:
            return
        self.update_check_running = True
        self.log(f"\n---- 下载更新开始 ----\n保存位置：{destination_path}")

        def worker() -> None:
            try:
                downloaded = download_update_from_result(result, destination_path=destination_path)
                self.log_queue.put(("update_result", downloaded, True))
            except Exception as exc:
                self.log_queue.put(("update_error", str(exc), True))

        threading.Thread(target=worker, daemon=True).start()

    def handle_update_result(self, result: dict[str, object], manual: bool) -> None:
        return self.handle_update_result_i18n(result, manual)
        self.update_check_running = False
        status = result.get("status")
        remote_tag = str(result.get("remote_tag") or "")

        if status == "current":
            if manual:
                messagebox.showinfo("检查更新", f"当前已是最新版本：v{APP_VERSION}")
            self.log(f"\n检查更新：当前版本 v{APP_VERSION}，最新版本 {remote_tag}。")
            return

        if status == "no_file":
            self.log(f"\n检查更新：发现新版本 {remote_tag}，但暂时没有可下载文件。")
            messagebox.showinfo("发现新版本", f"发现新版本 {remote_tag}，但暂时没有可下载文件。")
            return

        if status == "available":
            asset_name = str(result.get("asset_name") or "")
            required = bool(result.get("required") or False)
            notes_raw = result.get("release_notes")
            notes = [str(note) for note in notes_raw] if isinstance(notes_raw, list) else []
            note_text = "\n".join(f"- {note}" for note in notes) if notes else "无"
            self.log(
                "\n检查更新：发现新版本。\n"
                f"当前版本：v{APP_VERSION}\n"
                f"云端版本：{remote_tag}\n"
                f"文件：{asset_name}\n"
                f"强制更新：{'是' if required else '否'}\n"
                f"更新说明：\n{note_text}"
            )
            if messagebox.askyesno(
                "发现新版本",
                f"发现新版本 {remote_tag}。\n\n文件：{asset_name}\n\n更新说明：\n{note_text}\n\n是否选择保存位置并下载？",
            ):
                destination = filedialog.asksaveasfilename(
                    title="选择更新文件保存位置",
                    initialdir=str(APP_DIR),
                    initialfile=safe_download_name(asset_name),
                    defaultextension=Path(asset_name).suffix,
                    filetypes=[
                        ("更新文件", f"*{Path(asset_name).suffix}" if Path(asset_name).suffix else "*.*"),
                        ("所有文件", "*.*"),
                    ],
                )
                if not destination:
                    self.log("\n检查更新：用户取消选择保存位置。")
                    return
                destination_path = Path(destination)
                if destination_path.exists() and not messagebox.askyesno("覆盖文件", f"文件已存在，是否覆盖？\n{destination_path}"):
                    self.log("\n检查更新：用户取消覆盖已有文件。")
                    return
                self.start_update_download(result, destination)
            else:
                self.log("\n检查更新：用户取消下载。")
            return

        if status == "downloaded":
            asset_name = str(result.get("asset_name") or "")
            downloaded_path = str(result.get("downloaded_path") or "")
            required = bool(result.get("required") or False)
            notes_raw = result.get("release_notes")
            notes = [str(note) for note in notes_raw] if isinstance(notes_raw, list) else []
            note_text = "\n".join(f"- {note}" for note in notes) if notes else "无"
            self.log(
                "\n检查更新：发现新版本并已下载。\n"
                f"版本：{remote_tag}\n"
                f"文件：{asset_name}\n"
                f"位置：{downloaded_path}\n"
                f"强制更新：{'是' if required else '否'}\n"
                f"更新说明：\n{note_text}"
            )
            messagebox.showinfo(
                "更新已下载",
                f"新版本 {remote_tag} 已下载到：\n{downloaded_path}\n\n更新说明：\n{note_text}",
            )
            return

        self.log(f"\n检查更新：收到未知更新状态。")

    def handle_update_error(self, message: str, manual: bool) -> None:
        return self.handle_update_error_i18n(message, manual)
        self.update_check_running = False
        public_message = sanitize_update_error_message(message)
        self.log(f"\n检查更新失败：{public_message}")
        if manual:
            messagebox.showerror("检查更新失败", public_message)

    def choose_dir(self) -> None:
        initial = self.target_dir.get()
        if not Path(initial).exists():
            initial = str(default_target_dir())
        selected = filedialog.askdirectory(title=self.tr("choose_mod"), initialdir=initial)
        if selected:
            self.target_dir.set(selected)

    def selected_root(self) -> Path | None:
        path = Path(self.target_dir.get()).expanduser()
        if not path.exists() or not path.is_dir():
            messagebox.showerror(self.tr("invalid_target_title"), self.tr("invalid_target_msg"))
            return None
        return path

    def run_fixer(self, dry_run: bool = False) -> None:
        root = self.selected_root()
        if root is None or self.running:
            return

        args = [str(root)]
        if dry_run:
            args.append("--dry-run")
        if self.fixmenu.get():
            args.append("--fixmenu")
        if self.include_disabled.get():
            args.append("--include-disabled")
        if self.force_new_version.get():
            args.append("--force-new-version")

        stable_args: list[str] | None = None
        if self.stable_texture.get():
            stable_args = [str(root)]
            if dry_run:
                stable_args.append("--dry-run")
            if self.include_disabled.get():
                stable_args.append("--include-disabled")

        title = self.tr("preview_title") if dry_run else self.tr("fix_title")
        start_title = self.tr("preview_start") if dry_run else self.tr("fix_start")
        self.log(f"\n---- {start_title} ----\n{self.tr('command_args')}: {' '.join(args)}\n")
        if stable_args is not None:
            self.log(f"{self.tr('stable_args')}: rabbitfx_ps_t_converter.py {' '.join(stable_args)}\n")
        self.set_running(True)

        def worker() -> None:
            code = 1
            writer = QueueWriter(self.log_queue)
            try:
                with contextlib.redirect_stdout(writer), contextlib.redirect_stderr(writer):
                    code = fixer.main(args)
                    if stable_args is not None and code == 0:
                        print(f"\n---- {self.tr('stable_start')} ----")
                        stable_code = stable_texture_converter.main(stable_args)
                        print(f"---- {self.tr('stable_end')}: {stable_code} ----")
                        code = stable_code
            except Exception:
                writer.write(traceback.format_exc())
            self.log_queue.put(("done", code, title))

        threading.Thread(target=worker, daemon=True).start()

    def run_rollback(self, session_id: str, before: bool = False) -> None:
        root = self.selected_root()
        if root is None or self.running:
            return

        args = [str(root), "--rollback", session_id]
        if before:
            args.append("--rollback-before")

        mode = self.tr("rollback_before_state") if before else self.tr("rollback_after_state")
        confirm_message = self.tr("confirm_rollback_msg").format(session_id=session_id, mode=mode)
        if not messagebox.askyesno(self.tr("confirm_rollback"), confirm_message):
            return

        self.log(f"\n---- {self.tr('rollback_name')} ----\n{self.tr('command_args')}: {' '.join(args)}\n")
        self.set_running(True)

        def worker() -> None:
            code = 1
            writer = QueueWriter(self.log_queue)
            try:
                with contextlib.redirect_stdout(writer), contextlib.redirect_stderr(writer):
                    code = fixer.main(args)
            except Exception:
                writer.write(traceback.format_exc())
            self.log_queue.put(("done", code, self.tr("rollback_name")))
            self.log_queue.put(("refresh_backups",))

        threading.Thread(target=worker, daemon=True).start()

    def set_running(self, running: bool) -> None:
        self.running = running
        state = tk.DISABLED if running else tk.NORMAL
        for button in (self.fix_button, self.preview_button, self.rollback_button):
            button.configure(state=state)

    def poll_log_queue(self) -> None:
        try:
            while True:
                item = self.log_queue.get_nowait()
                if isinstance(item, tuple) and item and item[0] == "done":
                    _, code, title = item
                    self.log(f"\n---- {title} {self.tr('process_end')}: {code} ----\n")
                    self.set_running(False)
                elif isinstance(item, tuple) and item and item[0] == "refresh_backups":
                    self.refresh_backup_list()
                elif isinstance(item, tuple) and item and item[0] == "update_result":
                    _, result, manual = item
                    self.handle_update_result(result, bool(manual))
                elif isinstance(item, tuple) and item and item[0] == "update_error":
                    _, message, manual = item
                    self.handle_update_error(str(message), bool(manual))
                else:
                    self.log(str(item), newline=False)
        except queue.Empty:
            pass
        self.root.after(80, self.poll_log_queue)

    def log(self, text: str, newline: bool = True) -> None:
        if self.log_box is None:
            return
        text = self.translate_log_text_for_language(text)
        suffix = "\n" if newline else ""
        self.log_box.insert(tk.END, text + suffix)
        self.scroll_log_to_bottom()

    def clear_log(self) -> None:
        if self.log_box is not None:
            self.log_box.delete("1.0", tk.END)

    def export_log(self) -> None:
        if self.log_box is None:
            return
        path = filedialog.asksaveasfilename(
            title=self.tr("export_log"),
            defaultextension=".txt",
            filetypes=[(self.tr("text_files"), "*.txt"), (self.tr("all_files"), "*.*")],
        )
        if path:
            Path(path).write_text(self.log_box.get("1.0", "end-1c"), encoding="utf-8")
            messagebox.showinfo(self.tr("export_done"), f"{self.tr('export_done_msg')}\n{path}")

    def refresh_config(self) -> None:
        self.log("\n数据配置已刷新：GUI 会在下次运行时重新读取。")
        self.refresh_backup_list()

    def open_rollback_manager(self) -> None:
        if self.backup_window is not None and self.backup_window.winfo_exists():
            self.backup_window.lift()
            self.refresh_backup_list()
            return

        window = tk.Toplevel(self.root)
        self.backup_window = window
        window.title(self.tr("rollback_window"))
        set_window_icon(window)
        window.geometry(f"{ROLLBACK_WINDOW_BASE_WIDTH}x{ROLLBACK_WINDOW_BASE_HEIGHT}")
        window.configure(bg=self.colors["bg"])

        outer = tk.Frame(window, bg=self.colors["bg"], padx=20, pady=18)
        outer.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            outer,
            text=self.tr("backup_list"),
            bg=self.colors["bg"],
            fg=self.colors["muted"],
            font=(UI_FONT_FAMILY, UI_SECTION_FONT_SIZE),
        ).pack(anchor="w")

        list_frame = tk.Frame(outer, bg=self.colors["border"], padx=1, pady=1)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(8, 12))

        self.backup_list = tk.Listbox(
            list_frame,
            bg=self.colors["log_bg"],
            fg=self.colors["log_text"],
            selectbackground=self.colors["blue_dark"],
            selectforeground="white",
            relief=tk.FLAT,
            font=(LOG_FONT_FAMILY, 14),
        )
        self.backup_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll = tk.Scrollbar(list_frame, command=self.backup_list.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.backup_list.configure(yscrollcommand=scroll.set)

        row = tk.Frame(outer, bg=self.colors["bg"])
        row.pack(fill=tk.X)

        self.make_button(
            row,
            self.tr("refresh_backups"),
            command=self.refresh_backup_list,
            bg=ROLLBACK_CYAN,
            active=ROLLBACK_CYAN,
            fg=ROLLBACK_BUTTON_TEXT,
            width=12,
        ).pack(side=tk.LEFT)

        self.make_button(
            row,
            self.tr("restore_selected"),
            command=lambda: self.restore_selected_backup(False),
            bg=ROLLBACK_MAGENTA,
            active=ROLLBACK_MAGENTA,
            fg=ROLLBACK_BUTTON_TEXT,
            width=14,
        ).pack(side=tk.LEFT, padx=(10, 0))

        self.make_button(
            row,
            self.tr("restore_before"),
            command=lambda: self.restore_selected_backup(True),
            bg=ROLLBACK_YELLOW,
            active=ROLLBACK_YELLOW,
            fg=ROLLBACK_BUTTON_TEXT,
            width=14,
        ).pack(side=tk.LEFT, padx=(10, 0))

        window.update_idletasks()
        required_width = max(ROLLBACK_WINDOW_BASE_WIDTH, row.winfo_reqwidth() + 44)
        window.minsize(required_width, ROLLBACK_WINDOW_BASE_HEIGHT)
        window.geometry(f"{required_width}x{ROLLBACK_WINDOW_BASE_HEIGHT}")

        self.refresh_backup_list()

    def refresh_backup_list(self) -> None:
        if self.backup_list is None:
            return
        root = self.selected_root()
        if root is None:
            return

        self.backup_items = []
        self.backup_list.delete(0, tk.END)

        sessions = fixer.list_backup_sessions(root)
        if not sessions:
            self.backup_list.insert(tk.END, "暂无备份")
            return

        for index, session in enumerate(sessions, start=1):
            try:
                manifest = json.loads((session / fixer.BACKUP_MANIFEST).read_text(encoding="utf-8"))
                count = len(manifest.get("files", []))
                created = manifest.get("created_at", session.name)
                operation = manifest.get("operation", "legacy")
                has_after = any(entry.get("after_rel") for entry in manifest.get("files", []))
                state = "after" if has_after else "before-only"
            except Exception:
                count = 0
                created = session.name
                operation = "unreadable"
                state = "unknown"

            label = f"[{index}] {session.name} | {count} file(s) | {created} | {operation} | {state}"
            self.backup_items.append({"name": session.name, "label": label})
            self.backup_list.insert(tk.END, label)

    def restore_selected_backup(self, before: bool) -> None:
        if self.backup_list is None:
            return
        selection = self.backup_list.curselection()
        if not selection:
            messagebox.showwarning("未选择备份", "请先在列表中选择一个备份。")
            return
        index = selection[0]
        if index >= len(self.backup_items):
            return
        self.run_rollback(self.backup_items[index]["name"], before=before)


def main() -> None:
    try:
        configure_process_dpi_awareness()
        root = tk.Tk()
        FixerGui(root)
        root.mainloop()
    except Exception:
        crash_log = APP_DIR / "gui_crash.log"
        with contextlib.suppress(Exception):
            crash_log.write_text(traceback.format_exc(), encoding="utf-8")
        raise


if __name__ == "__main__":
    main()
