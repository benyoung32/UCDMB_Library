# -*- mode: python ; coding: utf-8 -*-


b = Analysis(
    ['pdf_splitter.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pandas','numpy'],
    noarchive=False,
)
b_pyz = PYZ(a.pure)

b_exe = EXE(
    pyz,
    b.scripts,
    [],
    exclude_binaries=True,
    name='pdf_splitter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='pdf_splitter',
)
