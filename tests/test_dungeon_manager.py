"""ダンジョン管理システムのテスト"""

import pytest
import tempfile
import shutil
import os
from unittest.mock import Mock

from src.dungeon.dungeon_manager import (
    DungeonManager, DungeonState, PlayerPosition, DungeonStatus
)
from src.dungeon.dungeon_generator import Direction, CellType
from src.character.party import Party
from src.character.character import Character
from src.character.stats import BaseStats


class TestPlayerPosition:
    """プレイヤー位置のテスト"""
    
    def test_player_position_creation(self):
        """プレイヤー位置作成テスト"""
        pos = PlayerPosition(x=5, y=3, level=1, facing=Direction.NORTH)
        
        assert pos.x == 5
        assert pos.y == 3
        assert pos.level == 1
        assert pos.facing == Direction.NORTH
    
    def test_player_position_serialization(self):
        """プレイヤー位置シリアライゼーションテスト"""
        pos = PlayerPosition(x=10, y=8, level=2, facing=Direction.EAST)
        
        # 辞書変換
        pos_dict = pos.to_dict()
        assert pos_dict['x'] == 10
        assert pos_dict['y'] == 8
        assert pos_dict['level'] == 2
        assert pos_dict['facing'] == 'east'
        
        # 辞書から復元
        restored_pos = PlayerPosition.from_dict(pos_dict)
        assert restored_pos.x == pos.x
        assert restored_pos.y == pos.y
        assert restored_pos.level == pos.level
        assert restored_pos.facing == pos.facing


class TestDungeonState:
    """ダンジョン状態のテスト"""
    
    def test_dungeon_state_creation(self):
        """ダンジョン状態作成テスト"""
        state = DungeonState(dungeon_id="test_dungeon", seed="test_seed")
        
        assert state.dungeon_id == "test_dungeon"
        assert state.seed == "test_seed"
        assert state.status == DungeonStatus.ACTIVE
        assert state.player_position is None
        assert len(state.levels) == 0
        assert state.steps_taken == 0
    
    def test_dungeon_state_with_position(self):
        """プレイヤー位置付きダンジョン状態テスト"""
        pos = PlayerPosition(x=1, y=1, level=1)
        state = DungeonState(
            dungeon_id="positioned_dungeon",
            seed="positioned_seed",
            player_position=pos
        )
        
        assert state.player_position == pos
        assert state.player_position.x == 1
        assert state.player_position.y == 1
    
    def test_dungeon_state_serialization(self):
        """ダンジョン状態シリアライゼーションテスト"""
        pos = PlayerPosition(x=5, y=7, level=3)
        state = DungeonState(
            dungeon_id="serialization_test",
            seed="serialization_seed",
            player_position=pos,
            steps_taken=100,
            encounters_faced=15
        )
        
        # 辞書変換
        state_dict = state.to_dict()
        assert state_dict['dungeon_id'] == "serialization_test"
        assert state_dict['seed'] == "serialization_seed"
        assert state_dict['steps_taken'] == 100
        assert state_dict['encounters_faced'] == 15
        
        # 辞書から復元
        restored_state = DungeonState.from_dict(state_dict)
        assert restored_state.dungeon_id == state.dungeon_id
        assert restored_state.seed == state.seed
        assert restored_state.steps_taken == state.steps_taken
        assert restored_state.player_position.x == pos.x


class TestDungeonManager:
    """ダンジョン管理システムのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        # 一時ディレクトリを作成
        self.temp_dir = tempfile.mkdtemp()
        self.manager = DungeonManager(save_directory=self.temp_dir)
        
        # テスト用パーティ作成
        stats = BaseStats(strength=15, agility=12, intelligence=14, faith=10, luck=13)
        self.character = Character.create_character("TestHero", "human", "fighter", stats)
        self.party = Party(party_id="test_party", name="TestParty")
        self.party.add_character(self.character)
    
    def teardown_method(self):
        """各テストメソッドの後に実行"""
        # 一時ディレクトリを削除
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_dungeon_manager_initialization(self):
        """ダンジョンマネージャー初期化テスト"""
        assert self.manager.save_directory == self.temp_dir
        assert len(self.manager.active_dungeons) == 0
        assert self.manager.current_dungeon is None
        assert os.path.exists(self.temp_dir)
    
    def test_create_dungeon(self):
        """ダンジョン作成テスト"""
        dungeon_state = self.manager.create_dungeon("test_dungeon", "test_seed")
        
        assert dungeon_state.dungeon_id == "test_dungeon"
        assert dungeon_state.seed == "test_seed"
        assert dungeon_state.status == DungeonStatus.ACTIVE
        assert 1 in dungeon_state.levels
        assert dungeon_state.player_position is not None
        assert dungeon_state.player_position.level == 1
        
        # マネージャーに登録されているかチェック
        assert "test_dungeon" in self.manager.active_dungeons
    
    def test_create_duplicate_dungeon(self):
        """重複ダンジョン作成テスト"""
        # 最初のダンジョン作成
        first_dungeon = self.manager.create_dungeon("duplicate_test", "seed1")
        
        # 同じIDで再作成（既存のものが返される）
        second_dungeon = self.manager.create_dungeon("duplicate_test", "seed2")
        
        assert first_dungeon == second_dungeon
        assert first_dungeon.seed == "seed1"  # 最初のシードが保持される
    
    def test_enter_dungeon_success(self):
        """ダンジョン入場成功テスト"""
        # ダンジョン作成
        self.manager.create_dungeon("enter_test", "enter_seed")
        
        # パーティをモック（探索準備完了状態）
        self.party.is_exploration_ready = Mock(return_value=True)
        
        # ダンジョン入場
        success = self.manager.enter_dungeon("enter_test", self.party)
        
        assert success == True
        assert self.manager.current_dungeon is not None
        assert self.manager.current_dungeon.dungeon_id == "enter_test"
    
    def test_enter_nonexistent_dungeon(self):
        """存在しないダンジョンへの入場テスト"""
        self.party.is_exploration_ready = Mock(return_value=True)
        
        success = self.manager.enter_dungeon("nonexistent", self.party)
        
        assert success == False
        assert self.manager.current_dungeon is None
    
    def test_enter_dungeon_unready_party(self):
        """準備不足パーティでのダンジョン入場テスト"""
        self.manager.create_dungeon("unready_test", "unready_seed")
        
        # パーティを準備不足状態にモック
        self.party.is_exploration_ready = Mock(return_value=False)
        
        success = self.manager.enter_dungeon("unready_test", self.party)
        
        assert success == False
        assert self.manager.current_dungeon is None
    
    def test_exit_dungeon(self):
        """ダンジョン退出テスト"""
        # ダンジョン作成・入場
        self.manager.create_dungeon("exit_test", "exit_seed")
        self.party.is_exploration_ready = Mock(return_value=True)
        self.manager.enter_dungeon("exit_test", self.party)
        
        # 退出
        success = self.manager.exit_dungeon()
        
        assert success == True
        assert self.manager.current_dungeon is None
    
    def test_exit_dungeon_no_active(self):
        """アクティブダンジョンなしでの退出テスト"""
        success = self.manager.exit_dungeon()
        
        assert success == False
    
    def test_turn_player(self):
        """プレイヤー回転テスト"""
        # ダンジョン準備
        self.manager.create_dungeon("turn_test", "turn_seed")
        self.party.is_exploration_ready = Mock(return_value=True)
        self.manager.enter_dungeon("turn_test", self.party)
        
        # 初期方向確認
        initial_facing = self.manager.current_dungeon.player_position.facing
        
        # 回転実行
        success = self.manager.turn_player(Direction.EAST)
        
        assert success == True
        assert self.manager.current_dungeon.player_position.facing == Direction.EAST
        assert self.manager.current_dungeon.player_position.facing != initial_facing
    
    def test_turn_player_no_dungeon(self):
        """ダンジョンなしでのプレイヤー回転テスト"""
        success = self.manager.turn_player(Direction.SOUTH)
        
        assert success == False
    
    def test_get_current_cell(self):
        """現在セル取得テスト"""
        # ダンジョン準備
        self.manager.create_dungeon("cell_test", "cell_seed")
        self.party.is_exploration_ready = Mock(return_value=True)
        self.manager.enter_dungeon("cell_test", self.party)
        
        # 現在セル取得
        current_cell = self.manager.get_current_cell()
        
        assert current_cell is not None
        assert current_cell.x == self.manager.current_dungeon.player_position.x
        assert current_cell.y == self.manager.current_dungeon.player_position.y
    
    def test_get_current_cell_no_dungeon(self):
        """ダンジョンなしでの現在セル取得テスト"""
        current_cell = self.manager.get_current_cell()
        
        assert current_cell is None
    
    def test_get_visible_cells(self):
        """視界内セル取得テスト"""
        # ダンジョン準備
        self.manager.create_dungeon("visible_test", "visible_seed")
        self.party.is_exploration_ready = Mock(return_value=True)
        self.manager.enter_dungeon("visible_test", self.party)
        
        # 視界内セル取得
        visible_cells = self.manager.get_visible_cells(vision_range=1)
        
        assert len(visible_cells) > 0
        
        # 各セルの形式チェック
        for x, y, cell in visible_cells:
            assert isinstance(x, int)
            assert isinstance(y, int)
            assert cell is not None
    
    def test_get_dungeon_info(self):
        """ダンジョン情報取得テスト"""
        # ダンジョン作成
        self.manager.create_dungeon("info_test", "info_seed")
        
        # ダンジョン情報取得
        info = self.manager.get_dungeon_info("info_test")
        
        assert info is not None
        assert info['dungeon_id'] == "info_test"
        assert info['status'] == DungeonStatus.ACTIVE.value
        assert info['current_level'] == 1
        assert info['levels_explored'] == 1
        assert info['steps_taken'] == 0
    
    def test_get_dungeon_info_nonexistent(self):
        """存在しないダンジョンの情報取得テスト"""
        info = self.manager.get_dungeon_info("nonexistent")
        
        assert info is None
    
    def test_save_and_load_dungeon(self):
        """ダンジョン保存・読み込みテスト"""
        # ダンジョン作成
        original_state = self.manager.create_dungeon("save_test", "save_seed")
        original_state.steps_taken = 50
        original_state.encounters_faced = 5
        
        # 保存
        save_success = self.manager.save_dungeon("save_test")
        assert save_success == True
        
        # 保存ファイルの存在確認
        save_path = os.path.join(self.temp_dir, "save_test.json")
        assert os.path.exists(save_path)
        
        # アクティブダンジョンをクリア
        self.manager.active_dungeons.clear()
        
        # 読み込み
        loaded_state = self.manager.load_dungeon("save_test")
        
        assert loaded_state is not None
        assert loaded_state.dungeon_id == "save_test"
        assert loaded_state.seed == "save_seed"
        assert loaded_state.steps_taken == 50
        assert loaded_state.encounters_faced == 5
        
        # マネージャーに登録されているかチェック
        assert "save_test" in self.manager.active_dungeons
    
    def test_save_nonexistent_dungeon(self):
        """存在しないダンジョンの保存テスト"""
        save_success = self.manager.save_dungeon("nonexistent")
        
        assert save_success == False
    
    def test_load_nonexistent_dungeon(self):
        """存在しないダンジョンファイルの読み込みテスト（自動復旧機能）"""
        loaded_state = self.manager.load_dungeon("nonexistent")
        
        # 自動復旧機能により、ダンジョンが新規作成される
        assert loaded_state is not None
        assert loaded_state.dungeon_id == "nonexistent"
        assert loaded_state.seed == "nonexistent"
        assert loaded_state.status == DungeonStatus.ACTIVE
        
        # active_dungeonsにも登録される
        assert "nonexistent" in self.manager.active_dungeons


class TestDungeonManagerMovement:
    """ダンジョン管理システムの移動テスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = DungeonManager(save_directory=self.temp_dir)
        
        # テスト用パーティ作成
        stats = BaseStats(strength=15, agility=12, intelligence=14, faith=10, luck=13)
        character = Character.create_character("MoveHero", "human", "fighter", stats)
        self.party = Party(party_id="move_party", name="MoveParty")
        self.party.add_character(character)
        self.party.is_exploration_ready = Mock(return_value=True)
        
        # ダンジョン準備
        self.manager.create_dungeon("movement_test", "movement_seed")
        self.manager.enter_dungeon("movement_test", self.party)
    
    def teardown_method(self):
        """各テストメソッドの後に実行"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_move_player_basic(self):
        """基本的なプレイヤー移動テスト"""
        # 初期位置を記録
        initial_pos = self.manager.current_dungeon.player_position
        initial_x, initial_y = initial_pos.x, initial_pos.y
        initial_steps = self.manager.current_dungeon.steps_taken
        
        # 移動可能な方向を探す
        current_level = self.manager.current_dungeon.levels[1]
        current_cell = current_level.get_cell(initial_x, initial_y)
        
        # 壁のない方向を見つける
        move_direction = None
        for direction in Direction:
            if not current_cell.walls.get(direction, True):
                # 移動先も歩行可能かチェック
                dx, dy = self.manager._direction_to_delta(direction)
                new_x, new_y = initial_x + dx, initial_y + dy
                if (0 <= new_x < current_level.width and 
                    0 <= new_y < current_level.height and
                    current_level.is_walkable(new_x, new_y)):
                    move_direction = direction
                    break
        
        if move_direction:
            # 移動実行
            success, message = self.manager.move_player(move_direction)
            
            assert success == True
            assert "移動しました" in message
            assert self.manager.current_dungeon.steps_taken == initial_steps + 1
            
            # 位置が変更されていることを確認
            new_pos = self.manager.current_dungeon.player_position
            assert (new_pos.x, new_pos.y) != (initial_x, initial_y)
    
    def test_move_player_wall_collision(self):
        """壁との衝突テスト"""
        # 初期位置を取得
        initial_pos = self.manager.current_dungeon.player_position
        current_level = self.manager.current_dungeon.levels[1]
        current_cell = current_level.get_cell(initial_pos.x, initial_pos.y)
        
        # 壁のある方向を探す
        wall_direction = None
        for direction in Direction:
            if current_cell.walls.get(direction, True):
                wall_direction = direction
                break
        
        if wall_direction:
            # 壁に向かって移動を試行
            success, message = self.manager.move_player(wall_direction)
            
            assert success == False
            assert "壁があり移動できません" in message
    
    def test_move_player_boundary(self):
        """境界外移動テスト"""
        # プレイヤーを境界近くに移動
        pos = self.manager.current_dungeon.player_position
        current_level = self.manager.current_dungeon.levels[1]
        
        # 左上角に移動
        pos.x, pos.y = 0, 0
        
        # さらに左（境界外）への移動を試行
        success, message = self.manager.move_player(Direction.WEST)
        
        assert success == False
        assert "境界" in message
    
    def test_move_player_no_dungeon(self):
        """ダンジョンなしでの移動テスト"""
        # ダンジョンから退出
        self.manager.exit_dungeon()
        
        # 移動を試行
        success, message = self.manager.move_player(Direction.NORTH)
        
        assert success == False
        assert "ダンジョンに入っていません" in message