"""pytest設定ファイル - Panda3D関連の依存関係をモック化"""

import pytest
from unittest.mock import Mock, MagicMock
import sys

# 特別なPanda3Dクラスのモック
class MockDirectObject:
    def __init__(self):
        pass
    
    def accept(self, *args, **kwargs):
        pass
    
    def ignore(self, *args, **kwargs):
        pass

class MockShowBase:
    def __init__(self):
        self.taskMgr = Mock()
        self.messenger = Mock()
        self.devices = Mock()

class MockModule(Mock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # DirectGuiの主要なコンポーネントを追加
        self.DirectFrame = Mock()
        self.DirectButton = Mock()
        self.DirectLabel = Mock()
        self.DirectCheckButton = Mock()
        self.DirectEntry = Mock()
        self.DirectScrolledList = Mock()
        self.DirectSlider = Mock()
        self.DirectOptionMenu = Mock()
        self.DirectDialog = Mock()
        self.OnscreenText = Mock()
        self.DGG = Mock()
        
        # __all__を追加してimport *をサポート
        self.__all__ = [
            'DirectFrame', 'DirectButton', 'DirectLabel', 'DirectCheckButton',
            'DirectEntry', 'DirectScrolledList', 'DirectSlider', 'DirectOptionMenu',
            'DirectDialog', 'OnscreenText', 'DGG'
        ]
    
    def __getattr__(self, name):
        return Mock()
    
    def __iter__(self):
        return iter(self.__all__ if hasattr(self, '__all__') else [])
    
    def __dir__(self):
        return self.__all__ if hasattr(self, '__all__') else []

# Panda3D関連のモジュールをすべてモック化
panda3d_modules = [
    'panda3d',
    'panda3d.core',
    'direct',
    'direct.showbase',
    'direct.showbase.DirectObject',
    'direct.showbase.ShowBase',
    'direct.gui',
    'direct.gui.DirectGui',
    'direct.gui.DirectFrame',
    'direct.gui.DirectButton',
    'direct.gui.DirectLabel',
    'direct.gui.OnscreenText',
    'direct.gui.DirectDialog',
    'direct.gui.DirectCheckButton',
    'direct.gui.DirectScrolledList',
    'direct.gui.DirectEntry',
    'direct.gui.DirectSlider',
    'direct.gui.DirectOptionMenu',
    'direct.task',
    'direct.task.TaskManagerGlobal',
    'direct.interval',
    'direct.interval.IntervalGlobal',
]

# モジュールをsys.modulesに登録
for module_name in panda3d_modules:
    mock_module = MockModule()
    sys.modules[module_name] = mock_module

# DirectObjectを特別に設定
sys.modules['direct.showbase.DirectObject'].DirectObject = MockDirectObject
sys.modules['direct.gui.OnscreenText'].OnscreenText = Mock

# builtins.baseをモック化
if 'builtins' not in sys.modules:
    sys.modules['builtins'] = MockModule()
sys.modules['builtins'].base = MockShowBase()

@pytest.fixture(autouse=True)
def mock_panda3d():
    """Panda3D関連の自動モック化フィクスチャ"""
    yield