# EndField Mod Fixer

EndField Mod Fixer is a Windows GUI tool for repairing Endfield mod files.

## Features

- Scan and repair supported mod folders.
- Preview changes before applying fixes.
- Manage rollback backups.
- Check for published updates.

## Run From Source

```powershell
python Endfield_mod_fixer_gui.py
```

Optional dependency:

```powershell
python -m pip install pillow
```

## Build

```powershell
pyinstaller --noconfirm --onefile --windowed --name Endfield_mod_fixer_gui Endfield_mod_fixer_gui.py
```
