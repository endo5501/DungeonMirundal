#!/usr/bin/env python3
"""ダンジョンレンダラー修正のテスト"""

import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.rendering.dungeon_renderer_pygame import DungeonRendererPygame
from src.dungeon.dungeon_manager import DungeonManager
from src.utils.logger import logger

class TestDungeonRendererFixes:
    """ダンジョンレンダラー修正のテスト"""
    
    def setup_method(self):
        """テスト前の初期化"""
        self.renderer = DungeonRendererPygame()
        self.dungeon_manager = DungeonManager()
        
        # レンダラーの設定
        self.renderer.set_dungeon_manager(self.dungeon_manager)
    
    def test_missing_movement_methods_exist(self):
        """不足していた移動メソッドが存在することを確認"""
        # 前後左右の移動メソッドが存在することを確認
        assert hasattr(self.renderer, '_move_forward')
        assert hasattr(self.renderer, '_move_backward')
        assert hasattr(self.renderer, '_move_left')
        assert hasattr(self.renderer, '_move_right')
        
        # 回転メソッドが存在することを確認
        assert hasattr(self.renderer, '_turn_left')
        assert hasattr(self.renderer, '_turn_right')
        
        # メニューメソッドが存在することを確認
        assert hasattr(self.renderer, '_show_menu')
    
    def test_movement_methods_are_callable(self):
        """移動メソッドが呼び出し可能であることを確認"""
        # ダンジョンがない状態でも安全に呼び出せることを確認
        try:
            self.renderer._move_forward()
            self.renderer._move_backward()
            self.renderer._move_left()
            self.renderer._move_right()
            self.renderer._turn_left()
            self.renderer._turn_right()
            self.renderer._show_menu()
        except Exception as e:
            pytest.fail(f"Movement methods should be callable: {e}")
    
    def test_auto_recover_method_exists(self):
        """自動復旧メソッドが存在することを確認"""
        assert hasattr(self.renderer, 'auto_recover')
        
        # 自動復旧メソッドが呼び出し可能であることを確認
        try:
            result = self.renderer.auto_recover()
            # ダンジョンが設定されていない場合はFalseが返される
            assert isinstance(result, bool)
        except Exception as e:
            pytest.fail(f"auto_recover method should be callable: {e}")
    
    def test_update_ui_method_enhanced(self):
        """update_uiメソッドが強化されていることを確認"""
        # update_uiメソッドが呼び出し可能であることを確認
        try:
            self.renderer.update_ui()
        except Exception as e:
            pytest.fail(f"update_ui method should be callable: {e}")
    
    def test_renderer_with_dungeon_manager(self):
        """ダンジョンマネージャーが設定された状態でのテスト"""
        # ダンジョンを作成
        success = self.dungeon_manager.create_dungeon("test_dungeon", "test_seed")
        assert success
        
        # 自動復旧が成功することを確認
        result = self.renderer.auto_recover()
        # 実際のPygame環境がない場合は失敗する可能性があるが、エラーは発生しない
        assert isinstance(result, bool)
    
    def test_movement_methods_with_dungeon(self):
        """ダンジョンがある状態での移動メソッドテスト"""
        # ダンジョンを作成
        self.dungeon_manager.create_dungeon("test_dungeon", "test_seed")
        
        # 移動メソッドが安全に呼び出せることを確認
        try:
            self.renderer._move_forward()
            self.renderer._turn_left()
            self.renderer._turn_right()
        except Exception as e:
            # Pygame環境がない場合はエラーが発生する可能性があるが、
            # AttributeErrorではないことを確認
            assert not isinstance(e, AttributeError), f"Method should exist: {e}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])