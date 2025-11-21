# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src\\ui\\kivy\\app.py'],
    pathex=[],
    binaries=[],
    datas=[('src/ui/kivy/InterfazMain.py', 'src/ui/kivy'), ('src/ui/kivy/InterfazMain.kv', 'src/ui/kivy'), ('src/ui/kivy/icons/app_icon.png', 'src/ui/kivy/icons'), ('src/ui/kivy/icons/app_icon.ico', 'src/ui/kivy/icons')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CirKit',
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
    icon=['src\\ui\\kivy\\icons\\app_icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CirKit',
)
