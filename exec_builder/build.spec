# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['../crop_tool.py'],
    pathex=[],
    binaries=[],
    datas=[('../part_config/alias.json','.'),('../part_config/substitution.json','.'),('../template.png','.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pandas','numpy'],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='crop_tool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
# -*- mode: python ; coding: utf-8 -*-


b = Analysis(
    ['../pdf_splitter.py'],
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
    b_pyz,
    b.scripts,
    [],
    exclude_binaries=True,
    name='pdf_splitter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    b_exe,
    a.binaries,
    b.binaries,
    a.datas,
    b.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='crop_tool'
)
