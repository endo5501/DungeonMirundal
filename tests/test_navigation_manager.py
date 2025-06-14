"""ナビゲーション管理システムのテスト"""

import pytest
from unittest.mock import Mock, patch

from src.navigation.navigation_manager import (
    NavigationManager, MovementType, MovementResult, MovementEvent
)
from src.dungeon.dungeon_manager import DungeonManager, DungeonState, PlayerPosition
from src.dungeon.dungeon_generator import Direction, CellType, DungeonAttribute
from src.character.party import Party
from src.character.character import Character
from src.character.stats import BaseStats


class TestNavigationManager:
    """ナビゲーション管理システムのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.nav_manager = NavigationManager()
        
        # モックのダンジョンマネージャー作成
        self.dungeon_manager = Mock(spec=DungeonManager)
        self.nav_manager.set_dungeon_manager(self.dungeon_manager)
        
        # テスト用パーティ作成
        stats = BaseStats(strength=15, agility=12, intelligence=14, faith=10, luck=13)
        character = Character.create_character("NavHero", "human", "fighter", stats)
        self.party = Party(party_id="nav_party", name="NavParty")
        self.party.add_character(character)
        self.nav_manager.set_party(self.party)
        
        # モックのダンジョン状態
        self.dungeon_state = Mock(spec=DungeonState)
        self.dungeon_state.player_position = PlayerPosition(x=5, y=5, level=1)
        self.dungeon_state.levels = {}
        self.dungeon_state.encounters_faced = 0
        self.dungeon_state.traps_triggered = 0
        self.dungeon_manager.current_dungeon = self.dungeon_state
    
    def test_navigation_manager_initialization(self):
        """ナビゲーションマネージャー初期化テスト"""
        nav_mgr = NavigationManager()
        
        assert nav_mgr.dungeon_manager is None
        assert nav_mgr.current_party is None
        assert nav_mgr.navigation_state.step_count == 0
        assert nav_mgr.navigation_state.sneak_mode == False
        assert nav_mgr.navigation_state.auto_map_enabled == True
    
    def test_set_dungeon_manager(self):
        """ダンジョンマネージャー設定テスト"""
        nav_mgr = NavigationManager()
        dungeon_mgr = Mock(spec=DungeonManager)
        
        nav_mgr.set_dungeon_manager(dungeon_mgr)
        
        assert nav_mgr.dungeon_manager == dungeon_mgr
    
    def test_set_party(self):
        """パーティ設定テスト"""
        nav_mgr = NavigationManager()
        
        nav_mgr.set_party(self.party)
        
        assert nav_mgr.current_party == self.party
    
    def test_move_player_success(self):
        """プレイヤー移動成功テスト"""
        # ダンジョンマネージャーの移動成功をモック
        self.dungeon_manager.move_player.return_value = (True, "移動しました")
        
        # セルモック（トラップなし、宝箱なし）
        mock_cell = Mock()
        mock_cell.has_trap = False
        mock_cell.has_treasure = False
        mock_cell.cell_type = CellType.FLOOR
        self.dungeon_manager.get_current_cell.return_value = mock_cell
        
        # 移動実行
        result = self.nav_manager.move_player(Direction.NORTH)
        
        assert result.result == MovementResult.SUCCESS
        assert "移動しました" in result.message
        assert self.nav_manager.navigation_state.step_count == 1
    
    def test_move_player_blocked_by_wall(self):
        """壁による移動阻止テスト"""
        # ダンジョンマネージャーの移動失敗をモック
        self.dungeon_manager.move_player.return_value = (False, "壁があり移動できません")
        
        # 移動実行
        result = self.nav_manager.move_player(Direction.NORTH)
        
        assert result.result == MovementResult.BLOCKED_BY_WALL
        assert "壁があり移動できません" in result.message
        assert self.nav_manager.navigation_state.step_count == 0  # 移動していない
    
    def test_move_player_no_dungeon(self):
        """ダンジョンなしでの移動テスト"""
        # ダンジョンマネージャーにダンジョンなし
        self.dungeon_manager.current_dungeon = None
        
        # 移動実行
        result = self.nav_manager.move_player(Direction.NORTH)
        
        assert result.result == MovementResult.INVALID_TARGET
        assert "ダンジョンに入っていません" in result.message
    
    def test_move_player_treasure_found(self):
        """宝箱発見テスト"""
        # ダンジョンマネージャーの移動成功をモック
        self.dungeon_manager.move_player.return_value = (True, "移動しました")
        
        # 宝箱があるセルをモック
        mock_cell = Mock()
        mock_cell.has_trap = False
        mock_cell.has_treasure = True
        mock_cell.treasure_id = "test_treasure"
        mock_cell.cell_type = CellType.FLOOR
        self.dungeon_manager.get_current_cell.return_value = mock_cell
        
        # 移動実行
        result = self.nav_manager.move_player(Direction.NORTH)
        
        assert result.result == MovementResult.TREASURE_FOUND
        assert "宝箱を発見しました" in result.message
        assert result.additional_data["treasure_id"] == "test_treasure"
    
    def test_move_player_stairs_found(self):
        """階段発見テスト"""
        # ダンジョンマネージャーの移動成功をモック
        self.dungeon_manager.move_player.return_value = (True, "移動しました")
        
        # 階段があるセルをモック
        mock_cell = Mock()
        mock_cell.has_trap = False
        mock_cell.has_treasure = False
        mock_cell.cell_type = CellType.STAIRS_UP
        self.dungeon_manager.get_current_cell.return_value = mock_cell
        
        # 移動実行
        result = self.nav_manager.move_player(Direction.NORTH)
        
        assert result.result == MovementResult.STAIRS_FOUND
        assert "上り階段を発見しました" in result.message
        assert result.additional_data["stairs_type"] == "stairs_up"
    
    @patch('random.random')
    def test_move_player_trap_triggered(self, mock_random):
        """トラップ発動テスト"""
        # トラップ発動するように乱数を設定
        mock_random.return_value = 0.9  # 回避失敗
        
        # ダンジョンマネージャーの移動成功をモック
        self.dungeon_manager.move_player.return_value = (True, "移動しました")
        
        # トラップがあるセルをモック
        mock_cell = Mock()
        mock_cell.has_trap = True
        mock_cell.trap_type = "poison"
        mock_cell.has_treasure = False
        mock_cell.cell_type = CellType.FLOOR
        self.dungeon_manager.get_current_cell.return_value = mock_cell
        
        # 移動実行
        result = self.nav_manager.move_player(Direction.NORTH)
        
        assert result.result == MovementResult.TRAP_TRIGGERED
        assert "毒ガストラップが発動" in result.message
        assert result.additional_data["trap_type"] == "poison"
    
    @patch('random.random')
    def test_move_player_encounter(self, mock_random):
        """エンカウンター発生テスト"""
        # エンカウンター発生するように乱数を設定
        mock_random.return_value = 0.01  # エンカウンター発生
        
        # ダンジョンマネージャーの移動成功をモック
        self.dungeon_manager.move_player.return_value = (True, "移動しました")
        
        # 通常セルをモック
        mock_cell = Mock()
        mock_cell.has_trap = False
        mock_cell.has_treasure = False
        mock_cell.cell_type = CellType.FLOOR
        self.dungeon_manager.get_current_cell.return_value = mock_cell
        
        # ダンジョンレベルをモック
        mock_level = Mock()
        mock_level.encounter_rate = 0.1
        self.dungeon_state.levels = {1: mock_level}
        
        # 移動実行
        result = self.nav_manager.move_player(Direction.NORTH)
        
        assert result.result == MovementResult.ENCOUNTER
        assert "モンスターと遭遇しました" in result.message
    
    def test_turn_player_success(self):
        """プレイヤー回転成功テスト"""
        # ダンジョンマネージャーの回転成功をモック
        self.dungeon_manager.turn_player.return_value = True
        
        # 回転実行
        success = self.nav_manager.turn_player(Direction.EAST)
        
        assert success == True
        assert len(self.nav_manager.movement_history) == 1
        assert self.nav_manager.movement_history[0].message == "eastを向きました"
    
    def test_turn_player_no_dungeon_manager(self):
        """ダンジョンマネージャーなしでの回転テスト"""
        nav_mgr = NavigationManager()
        
        success = nav_mgr.turn_player(Direction.EAST)
        
        assert success == False
    
    def test_use_stairs_up_success(self):
        """上り階段使用成功テスト"""
        # 現在位置に上り階段があるセルをモック
        mock_cell = Mock()
        mock_cell.cell_type = CellType.STAIRS_UP
        self.dungeon_manager.get_current_cell.return_value = mock_cell
        
        # 階段使用成功をモック
        self.dungeon_manager.change_level.return_value = (True, "レベル0に上がりました")
        
        # 階段使用実行
        result = self.nav_manager.use_stairs("up")
        
        assert result.result == MovementResult.SUCCESS
        assert "レベル0に上がりました" in result.message
        assert result.additional_data["level_change"] == -1
    
    def test_use_stairs_down_success(self):
        """下り階段使用成功テスト"""
        # 現在位置に下り階段があるセルをモック
        mock_cell = Mock()
        mock_cell.cell_type = CellType.STAIRS_DOWN
        self.dungeon_manager.get_current_cell.return_value = mock_cell
        
        # 階段使用成功をモック
        self.dungeon_manager.change_level.return_value = (True, "レベル2に下りました")
        
        # 階段使用実行
        result = self.nav_manager.use_stairs("down")
        
        assert result.result == MovementResult.SUCCESS
        assert "レベル2に下りました" in result.message
        assert result.additional_data["level_change"] == 1
    
    def test_use_stairs_wrong_type(self):
        """間違った階段タイプでの使用テスト"""
        # 現在位置に上り階段があるが、下り階段を使おうとする
        mock_cell = Mock()
        mock_cell.cell_type = CellType.STAIRS_UP
        self.dungeon_manager.get_current_cell.return_value = mock_cell
        
        # 階段使用実行
        result = self.nav_manager.use_stairs("down")
        
        assert result.result == MovementResult.INVALID_TARGET
        assert "対応する階段がありません" in result.message
    
    def test_set_movement_mode_sneak(self):
        """忍び足モード設定テスト"""
        self.nav_manager.set_movement_mode(sneak=True, auto_map=True)
        
        assert self.nav_manager.navigation_state.sneak_mode == True
        assert self.nav_manager.navigation_state.movement_speed == 0.5
        assert self.nav_manager.navigation_state.encounter_rate == 0.3
    
    def test_set_movement_mode_normal(self):
        """通常モード設定テスト"""
        # 最初に忍び足モードに設定
        self.nav_manager.set_movement_mode(sneak=True)
        
        # 通常モードに戻す
        self.nav_manager.set_movement_mode(sneak=False)
        
        assert self.nav_manager.navigation_state.sneak_mode == False
        assert self.nav_manager.navigation_state.movement_speed == 1.0
        assert self.nav_manager.navigation_state.encounter_rate == 1.0
    
    def test_get_movement_history(self):
        """移動履歴取得テスト"""
        # 履歴に手動でイベントを追加
        event1 = MovementEvent(
            result=MovementResult.SUCCESS,
            message="北に移動",
            old_position=(5, 5, 1),
            new_position=(5, 4, 1)
        )
        event2 = MovementEvent(
            result=MovementResult.SUCCESS,
            message="東に移動",
            old_position=(5, 4, 1),
            new_position=(6, 4, 1)
        )
        
        self.nav_manager._add_to_history(event1)
        self.nav_manager._add_to_history(event2)
        
        # 履歴取得
        history = self.nav_manager.get_movement_history(limit=5)
        
        assert len(history) == 2
        assert history[0] == event1
        assert history[1] == event2
    
    def test_get_navigation_status(self):
        """ナビゲーション状態取得テスト"""
        # 状態を変更
        self.nav_manager.navigation_state.step_count = 50
        self.nav_manager.navigation_state.last_encounter_step = 30
        self.nav_manager.set_movement_mode(sneak=True)
        
        # 状態取得
        status = self.nav_manager.get_navigation_status()
        
        assert status['step_count'] == 50
        assert status['sneak_mode'] == True
        assert status['last_encounter_step'] == 30
        assert status['steps_since_encounter'] == 20
        assert status['movement_speed'] == 0.5
        assert status['encounter_rate'] == 0.3
    
    def test_movement_history_size_limit(self):
        """移動履歴サイズ制限テスト"""
        # 制限を小さく設定
        self.nav_manager.max_history_size = 3
        
        # 5つのイベントを追加
        for i in range(5):
            event = MovementEvent(
                result=MovementResult.SUCCESS,
                message=f"移動{i}",
                old_position=(i, i, 1),
                new_position=(i+1, i+1, 1)
            )
            self.nav_manager._add_to_history(event)
        
        # 履歴は最大サイズに制限される
        assert len(self.nav_manager.movement_history) == 3
        
        # 最新の3つが保持されている
        messages = [event.message for event in self.nav_manager.movement_history]
        assert messages == ["移動2", "移動3", "移動4"]


class TestMovementTypes:
    """移動タイプのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.nav_manager = NavigationManager()
    
    def test_get_speed_multiplier_walk(self):
        """歩行速度倍率テスト"""
        multiplier = self.nav_manager._get_speed_multiplier(MovementType.WALK)
        assert multiplier == 1.0
    
    def test_get_speed_multiplier_run(self):
        """走行速度倍率テスト"""
        multiplier = self.nav_manager._get_speed_multiplier(MovementType.RUN)
        assert multiplier == 1.5
    
    def test_get_speed_multiplier_sneak(self):
        """忍び足速度倍率テスト"""
        multiplier = self.nav_manager._get_speed_multiplier(MovementType.SNEAK)
        assert multiplier == 0.5
    
    def test_get_speed_multiplier_teleport(self):
        """テレポート速度倍率テスト"""
        multiplier = self.nav_manager._get_speed_multiplier(MovementType.TELEPORT)
        assert multiplier == 0.0
    
    def test_get_speed_multiplier_with_state_modifier(self):
        """状態修正を含む速度倍率テスト"""
        # 忍び足モードを設定（movement_speed = 0.5）
        self.nav_manager.set_movement_mode(sneak=True)
        
        # 通常歩行でも忍び足状態の影響を受ける
        multiplier = self.nav_manager._get_speed_multiplier(MovementType.WALK)
        assert multiplier == 0.5  # 1.0 * 0.5


class TestAutoMap:
    """オートマップ機能のテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.nav_manager = NavigationManager()
        
        # モックのダンジョンマネージャー作成
        self.dungeon_manager = Mock(spec=DungeonManager)
        self.nav_manager.set_dungeon_manager(self.dungeon_manager)
        
        # モックのダンジョン状態
        self.dungeon_state = Mock(spec=DungeonState)
        self.dungeon_state.player_position = PlayerPosition(x=5, y=5, level=1)
        self.dungeon_state.discovered_cells = {1: [(5, 5), (5, 4), (6, 5)]}
        self.dungeon_manager.current_dungeon = self.dungeon_state
        
        # モックのレベル
        self.mock_level = Mock()
        self.dungeon_state.levels = {1: self.mock_level}
    
    def test_get_auto_map_data_enabled(self):
        """オートマップデータ取得テスト（有効時）"""
        # オートマップ有効
        self.nav_manager.navigation_state.auto_map_enabled = True
        
        # セルの詳細をモック
        def mock_get_cell(x, y):
            mock_cell = Mock()
            mock_cell.cell_type = CellType.FLOOR
            mock_cell.has_treasure = False
            mock_cell.has_trap = False
            mock_cell.visited = True
            return mock_cell
        
        self.mock_level.get_cell = mock_get_cell
        
        # オートマップデータ取得
        map_data = self.nav_manager.get_auto_map_data()
        
        assert map_data['level'] == 1
        assert map_data['player_position'] == (5, 5)
        assert map_data['player_facing'] == Direction.NORTH.value
        assert len(map_data['discovered_cells']) == 3
        assert '5,5' in map_data['cell_details']
    
    def test_get_auto_map_data_disabled(self):
        """オートマップデータ取得テスト（無効時）"""
        # オートマップ無効
        self.nav_manager.navigation_state.auto_map_enabled = False
        
        # オートマップデータ取得
        map_data = self.nav_manager.get_auto_map_data()
        
        assert map_data == {}
    
    def test_get_auto_map_data_no_dungeon(self):
        """ダンジョンなしでのオートマップデータ取得テスト"""
        # ダンジョンマネージャーにダンジョンなし
        self.dungeon_manager.current_dungeon = None
        
        # オートマップデータ取得
        map_data = self.nav_manager.get_auto_map_data()
        
        assert map_data == {}