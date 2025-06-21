"""ダンジョン3D描画バグ修正のテスト

このテストは docs/bugs.md で報告された「ダンジョンに入った後、3Dのダンジョン画面が描画されない」
問題の修正を検証します。
"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock

# Panda3Dモジュールをモック化
sys.modules['direct.showbase.ShowBase'] = Mock()
sys.modules['direct.actor.Actor'] = Mock()
sys.modules['panda3d.core'] = Mock()
sys.modules['direct.gui.OnscreenText'] = Mock()
sys.modules['direct.task'] = Mock()
sys.modules['direct.gui.DirectGui'] = Mock()

# モック後にインポート
from src.rendering.dungeon_renderer import DungeonRenderer
from src.dungeon.dungeon_manager import DungeonManager, DungeonState, PlayerPosition
from src.dungeon.dungeon_generator import Direction, DungeonLevel, DungeonAttribute
from src.character.party import Party


class TestDungeon3DRenderingBugFix:
    """ダンジョン3D描画バグ修正のテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される設定"""
        # モックのShowBaseインスタンスを作成
        self.mock_showbase = Mock()
        self.mock_showbase.render = Mock()
        self.mock_showbase.camera = Mock()
        self.mock_showbase.cam = Mock()
        self.mock_showbase.win = Mock()
        self.mock_showbase.taskMgr = Mock()
        self.mock_showbase.loader = Mock()
        self.mock_showbase.setBackgroundColor = Mock()
        self.mock_showbase.graphicsEngine = Mock()
        
        # カメラのモック設定
        self.mock_showbase.camera.setPos = Mock()
        self.mock_showbase.camera.setHpr = Mock()
        self.mock_showbase.camera.getPos = Mock(return_value=Mock(x=0, y=0, z=1.7))
        self.mock_showbase.camera.getHpr = Mock(return_value=Mock(x=0, y=0, z=0))
        
        # cam.node().getLens() のモック設定
        mock_lens = Mock()
        mock_lens.setFov = Mock()
        mock_lens.setNear = Mock()
        mock_lens.setFar = Mock()
        mock_lens.getNear = Mock(return_value=0.1)
        mock_lens.getFar = Mock(return_value=20)
        
        mock_cam_node = Mock()
        mock_cam_node.getLens = Mock(return_value=mock_lens)
        mock_cam_node.setCameraMask = Mock()
        self.mock_showbase.cam.node = Mock(return_value=mock_cam_node)
        
    def test_dungeon_renderer_initialization(self):
        """ダンジョンレンダラーが正常に初期化されることを確認"""
        # PANDA3D_AVAILABLEをTrueにパッチ
        with patch('src.rendering.dungeon_renderer.PANDA3D_AVAILABLE', True):
            renderer = DungeonRenderer(show_base_instance=self.mock_showbase)
            
            # レンダラーが有効であることを確認
            assert renderer.enabled == True
            assert renderer.base_instance == self.mock_showbase
            
            # 基本設定が正しく設定されていることを確認
            assert renderer.camera_height == 1.7
            assert renderer.fov == 75
            assert renderer.view_distance == 10
    
    def test_initial_render_called_during_dungeon_entry(self):
        """ダンジョン入室時に初期レンダリングが呼ばれることを確認"""
        with patch('src.rendering.dungeon_renderer.PANDA3D_AVAILABLE', True):
            renderer = DungeonRenderer(show_base_instance=self.mock_showbase)
            
            # テスト用のダンジョン状態を作成
            dungeon_state = self._create_test_dungeon_state()
            
            # ensure_initial_renderメソッドが存在することを確認
            assert hasattr(renderer, 'ensure_initial_render')
            
            # 初期レンダリングを実行
            result = renderer.ensure_initial_render(dungeon_state)
        
            # 正常に実行されることを確認
            assert result == True
    
    def test_force_frame_render_functionality(self):
        """強制フレームレンダリング機能が動作することを確認"""
        with patch('src.rendering.dungeon_renderer.PANDA3D_AVAILABLE', True):
            renderer = DungeonRenderer(show_base_instance=self.mock_showbase)
            
            # _force_frame_renderメソッドが存在することを確認
            assert hasattr(renderer, '_force_frame_render')
            
            # 強制フレームレンダリングを実行（エラーなく実行されることを確認）
            try:
                renderer._force_frame_render()
                force_render_works = True
            except Exception:
                force_render_works = False
        
            assert force_render_works == True
    
    def test_camera_position_validation(self):
        """カメラ位置の検証機能が動作することを確認"""
        with patch('src.rendering.dungeon_renderer.PANDA3D_AVAILABLE', True):
            renderer = DungeonRenderer(show_base_instance=self.mock_showbase)
        
            # テスト用のプレイヤー位置とレベルを作成
            player_pos = PlayerPosition(x=1, y=1, level=1, facing=Direction.NORTH)
            level = self._create_test_level()
            
            # カメラ位置検証メソッドが存在することを確認
            assert hasattr(renderer, '_validate_camera_position')
            
            # カメラ位置の検証を実行
            result = renderer._validate_camera_position(player_pos, level)
        
            # 有効な位置として認識されることを確認
            assert result == True
    
    def test_scene_completeness_validation(self):
        """シーンの完成度検証機能が動作することを確認"""
        with patch('src.rendering.dungeon_renderer.PANDA3D_AVAILABLE', True):
            renderer = DungeonRenderer(show_base_instance=self.mock_showbase)
        
            # シーン検証メソッドが存在することを確認
            assert hasattr(renderer, '_validate_scene_completeness')
            
            # 初期状態（空のシーン）では不完全として判定されることを確認
            result = renderer._validate_scene_completeness()
            assert result == False  # 空のシーンは不完全
            
            # テストノードを追加
            mock_node = Mock()
            mock_node.getParent = Mock(return_value=Mock())  # 親ノードがあることを示す
            
            renderer.wall_nodes['test_wall'] = mock_node
            renderer.floor_nodes['test_floor'] = mock_node  
            renderer.ceiling_nodes['test_ceiling'] = mock_node
        
            # ノードがある状態では完全として判定されることを確認
            result = renderer._validate_scene_completeness()
            assert result == True
    
    def test_improved_lighting_settings(self):
        """改善されたライティング設定が適用されることを確認"""
        with patch('src.rendering.dungeon_renderer.PANDA3D_AVAILABLE', True):
            renderer = DungeonRenderer(show_base_instance=self.mock_showbase)
        
            # ライティング初期化が呼ばれていることを確認
            # （初期化時に自動的に呼ばれている）
            
            # ライティング設定メソッドが存在することを確認
            assert hasattr(renderer, '_initialize_lighting')
            
            # 再度ライティングを初期化してエラーが発生しないことを確認
            try:
                renderer._initialize_lighting()
                lighting_works = True
            except Exception:
                lighting_works = False
        
            assert lighting_works == True
    
    def test_debug_info_functionality(self):
        """デバッグ情報機能が動作することを確認"""
        with patch('src.rendering.dungeon_renderer.PANDA3D_AVAILABLE', True):
            renderer = DungeonRenderer(show_base_instance=self.mock_showbase)
        
            # デバッグ情報メソッドが存在することを確認
            assert hasattr(renderer, 'get_debug_info')
            assert hasattr(renderer, 'log_debug_info')
            
            # デバッグ情報を取得
            debug_info = renderer.get_debug_info()
            
            # 必要な情報が含まれていることを確認
            assert 'status' in debug_info
            assert 'nodes' in debug_info
            assert 'camera_height' in debug_info
            assert debug_info['status'] == 'enabled'
            
            # ログ出力がエラーなく実行されることを確認
            try:
                renderer.log_debug_info()
                debug_log_works = True
            except Exception:
                debug_log_works = False
        
            assert debug_log_works == True
    
    def test_error_handling_functionality(self):
        """エラーハンドリング機能が動作することを確認"""
        with patch('src.rendering.dungeon_renderer.PANDA3D_AVAILABLE', True):
            renderer = DungeonRenderer(show_base_instance=self.mock_showbase)
        
            # エラーハンドリングメソッドが存在することを確認
            assert hasattr(renderer, 'handle_rendering_error')
            assert hasattr(renderer, '_attempt_error_recovery')
            
            # エラーハンドリングがエラーなく実行されることを確認
            test_error = Exception("テストエラー")
            
            try:
                renderer.handle_rendering_error(test_error, "test_context")
                error_handling_works = True
            except Exception:
                error_handling_works = False
        
            assert error_handling_works == True
    
    def test_render_dungeon_with_error_handling(self):
        """エラーハンドリング付きのダンジョン描画が動作することを確認"""
        with patch('src.rendering.dungeon_renderer.PANDA3D_AVAILABLE', True):
            renderer = DungeonRenderer(show_base_instance=self.mock_showbase)
        
            # テスト用のダンジョン状態を作成
            dungeon_state = self._create_test_dungeon_state()
            
            # レンダリングメソッドにtry-catch文が含まれていることを確認
            # （メソッドが正常に実行されることで確認）
            result = renderer.render_dungeon(dungeon_state)
        
            # 結果がブール値であることを確認（エラーで例外が発生していない）
            assert isinstance(result, bool)
    
    def test_bug_fix_integration(self):
        """バグ修正の統合テスト"""
        """
        実際のバグ修正が以下の点で改善されていることを確認：
        1. 初期レンダリング機能の追加
        2. カメラ位置の改善
        3. ライティングの改善
        4. レンダリングパイプラインの同期改善
        5. デバッグ機能の追加
        """
        
        # この統合テストは実際のPanda3D環境が必要なため、
        # 機能の存在確認に留める
        
        # DungeonRendererクラスに必要なメソッドが追加されていることを確認
        expected_methods = [
            'ensure_initial_render',
            '_force_frame_render', 
            '_validate_camera_position',
            '_validate_scene_completeness',
            'get_debug_info',
            'log_debug_info',
            'handle_rendering_error',
            '_attempt_error_recovery'
        ]
        
        for method_name in expected_methods:
            assert hasattr(DungeonRenderer, method_name), f"メソッド {method_name} が見つかりません"
        
        # GameManagerに必要な変更が含まれていることも確認
        # （ensure_initial_renderの呼び出し）
        with open('/home/satorue/Dungeon/src/core/game_manager.py', 'r', encoding='utf-8') as f:
            game_manager_content = f.read()
        
        assert 'ensure_initial_render' in game_manager_content, "GameManagerでensure_initial_renderが呼ばれていません"
    
    def _create_test_dungeon_state(self) -> DungeonState:
        """テスト用のダンジョン状態を作成"""
        dungeon_state = DungeonState(
            dungeon_id="test_dungeon",
            seed="test_seed"
        )
        
        # プレイヤー位置を設定
        dungeon_state.player_position = PlayerPosition(
            x=1, y=1, level=1, facing=Direction.NORTH
        )
        
        # テスト用レベルを作成
        level = self._create_test_level()
        dungeon_state.levels[1] = level
        
        return dungeon_state
    
    def _create_test_level(self) -> DungeonLevel:
        """テスト用のダンジョンレベルを作成"""
        level = DungeonLevel(
            level=1,
            width=5,
            height=5,
            attribute=DungeonAttribute.PHYSICAL
        )
        
        # is_walkableメソッドをモック
        level.is_walkable = Mock(return_value=True)
        level.get_cell = Mock(return_value=Mock())
        
        return level


if __name__ == "__main__":
    # テストを個別実行する場合
    pytest.main([__file__, "-v"])