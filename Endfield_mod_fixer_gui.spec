# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['Endfield_mod_fixer_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('favicon.ico', '.'), ('MaoKenShiJinHei', 'MaoKenShiJinHei'), ('无缝地形等高线_爱给网_aigei_com.png', '.')],
    hiddenimports=[],
    hookspath=['pyinstaller_hooks'],
    hooksconfig={},
    runtime_hooks=['pyinstaller_tk_runtime.py'],
    excludes=['numpy', 'numpy.testing', 'setuptools', 'pkg_resources', 'pycparser', 'cffi'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Endfield_mod_fixer_gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['favicon.ico'],
)
