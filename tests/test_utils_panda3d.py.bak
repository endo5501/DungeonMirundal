"""テスト用のユーティリティ関数"""

import sys
from unittest.mock import Mock, MagicMock


def setup_panda3d_mocks():
    """Panda3Dのモックを設定"""
    # 基本モジュールのモック
    mock_modules = {
        'direct': Mock(),
        'direct.showbase': Mock(),
        'direct.showbase.ShowBase': Mock(),
        'direct.actor': Mock(),
        'direct.actor.Actor': Mock(),
        'direct.gui': Mock(),
        'panda3d': Mock(),
        'panda3d.core': Mock(),
    }
    
    # DirectGuiクラスのモック
    mock_direct_gui = Mock()
    
    # 重要なUI要素のモック
    mock_direct_gui.DirectButton = MagicMock()
    mock_direct_gui.DirectFrame = MagicMock()
    mock_direct_gui.DirectLabel = MagicMock()
    mock_direct_gui.DirectScrolledList = MagicMock()
    mock_direct_gui.DirectDialog = MagicMock()
    mock_direct_gui.DGG = Mock()
    
    # OnscreenTextのモック
    mock_direct_gui.OnscreenText = MagicMock()
    
    mock_modules['direct.gui.DirectGui'] = mock_direct_gui
    mock_modules['direct.gui.OnscreenText'] = Mock()
    
    # panda3d.coreの重要なクラス
    mock_panda3d_core = Mock()
    mock_panda3d_core.Vec3 = MagicMock()
    mock_panda3d_core.TextNode = Mock()
    mock_panda3d_core.TextNode.ALeft = 0
    mock_panda3d_core.TextNode.ACenter = 1
    mock_panda3d_core.TextNode.ARight = 2
    
    mock_modules['panda3d.core'] = mock_panda3d_core
    
    # sys.modulesに設定
    for module_name, mock_module in mock_modules.items():
        sys.modules[module_name] = mock_module
    
    # direct.gui.DirectGuiから直接インポートできるようにグローバル設定
    import builtins
    builtins.DirectButton = mock_direct_gui.DirectButton
    builtins.DirectFrame = mock_direct_gui.DirectFrame
    builtins.DirectLabel = mock_direct_gui.DirectLabel
    builtins.DirectScrolledList = mock_direct_gui.DirectScrolledList
    builtins.DirectDialog = mock_direct_gui.DirectDialog
    builtins.OnscreenText = mock_direct_gui.OnscreenText
    builtins.Vec3 = mock_panda3d_core.Vec3
    builtins.TextNode = mock_panda3d_core.TextNode
    
    # baseオブジェクトのモック
    mock_base = Mock()
    mock_loader = Mock()
    mock_loader.loadFont = Mock(return_value=None)
    mock_base.loader = mock_loader
    builtins.base = mock_base
    
    return mock_modules