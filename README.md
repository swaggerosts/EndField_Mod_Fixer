# Endfield Mod Fixer

Endfield Mod Fixer is a Windows-focused repair tool for Endfield / EFMI mod `.ini` files. It provides a GUI workflow for regular users and a command-line entry point for batch repair, preview scans, backup listing, and rollback.

Current app version: `1.3.1`

## Features

- Scan and repair supported `.ini` files under a selected mod folder.
- Preview changes with `--dry-run` before writing files.
- Automatically creates rollback backups before writing changes.
- Restore either the repaired after-state or the original before-state from a backup session.
- Optional handling for `DISABLED*.ini` files.
- Optional `fixmenu2.0` repair stage: `ps-t102 -> ps-t100`.
- Cleans known Endfield v1.3 hotfix files when detected.
- Optional RabbitFX stable texture conversion from the GUI.

## GUI Usage

Run the GUI from source:

```powershell
python Endfield_mod_fixer_gui.py
```

Or run the packaged executable:

```powershell
.\Endfield_mod_fixer_gui.exe
```

In the GUI:

- Choose the target mod folder.
- Use **Preview Scan** to inspect what would change.
- Use **One-click Fix** to apply repairs.
- Use **Rollback Manager** to restore backup sessions.
- Enable **Stable Texture** only when repaired mods still behave abnormally.
- Enable **Fix Menu** when the in-game menu cannot be opened.

## CLI Usage

Basic repair:

```powershell
python Endfield_mod_fixer.py "D:\Path\To\Mods"
```

Preview only:

```powershell
python Endfield_mod_fixer.py "D:\Path\To\Mods" --dry-run
```

Process disabled ini files too:

```powershell
python Endfield_mod_fixer.py "D:\Path\To\Mods" --include-disabled
```

Enable the optional fixmenu stage:

```powershell
python Endfield_mod_fixer.py "D:\Path\To\Mods" --fixmenu
```

Force all repair stages even when files look like newer-version mods:

```powershell
python Endfield_mod_fixer.py "D:\Path\To\Mods" --force-new-version
```

## Backups And Rollback

List backup sessions:

```powershell
python Endfield_mod_fixer.py "D:\Path\To\Mods" --list-backups
```

Restore the latest backup to the repaired after-state:

```powershell
python Endfield_mod_fixer.py "D:\Path\To\Mods" --rollback
```

Restore a specific backup to the repaired after-state:

```powershell
python Endfield_mod_fixer.py "D:\Path\To\Mods" --rollback BACKUP_ID
```

Undo a repair by restoring the before-state:

```powershell
python Endfield_mod_fixer.py "D:\Path\To\Mods" --rollback BACKUP_ID --rollback-before
```

`--restore` is an alias for `--rollback`.

## RabbitFX Stable Texture Converter

The stable texture converter can also be run directly:

```powershell
python rabbitfx_ps_t_converter.py "D:\Path\To\Mods"
```

Preview conversion:

```powershell
python rabbitfx_ps_t_converter.py "D:\Path\To\Mods" --dry-run
```

Useful options:

- `--slots 2,3,4` limits conversion to selected `ps-t` slots.
- `--strategy auto|rabbitfx|shift` chooses the conversion strategy.
- `--force` converts even if RabbitFX entries already exist.
- `--include-disabled` includes paths whose folder name starts with `DISABLED`.
- `--include-backups` includes backup-looking files when scanning a directory.

## Build Executable

Build the GUI executable with PyInstaller:

```powershell
$image = '等高线.png'
python -m PyInstaller --noconfirm --clean --onefile --windowed `
  --name Endfield_mod_fixer_gui `
  --distpath release `
  --workpath build_onefile `
  --specpath . `
  --icon favicon.ico `
  --runtime-hook pyinstaller_tk_runtime.py `
  --additional-hooks-dir pyinstaller_hooks `
  --add-data "favicon.ico;." `
  --add-data "MaoKenShiJinHei;MaoKenShiJinHei" `
  --add-data "$image;." `
  Endfield_mod_fixer_gui.py
```

The executable will be generated at:

```text
release\Endfield_mod_fixer_gui.exe
```

## Project Files

- `Endfield_mod_fixer.py` - core CLI repair, backup, and rollback logic.
- `Endfield_mod_fixer_gui.py` - Tkinter GUI.
- `rabbitfx_ps_t_converter.py` - optional RabbitFX stable texture converter.
- `pyinstaller_tk_runtime.py` and `pyinstaller_hooks/` - PyInstaller Tcl/Tk packaging helpers.
- `MaoKenShiJinHei/` - bundled UI font.
- `favicon.ico` - application icon.
