# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all

block_cipher = None

# 收集 dependency_injector 的所有文件
datas_di, binaries_di, hiddenimports_di = collect_all('dependency_injector')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries_di,
    datas=[
        ('qml', 'qml'),
        ('resources', 'resources'),
        ('prompts/templates', 'prompts/templates'),
        ('alembic.ini', '.'),
        ('alembic', 'alembic'),
    ] + datas_di,
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtQml',
        'PySide6.QtQuick',
        'PySide6.QtQuickControls2',
        'sqlalchemy.ext.baked',
        'logging.config',
        'alembic.script',
        'alembic.runtime.migration',
    ] + hiddenimports_di,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AiVideoGUI',
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
    icon='resources/logo.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AiVideoGUI',
)
