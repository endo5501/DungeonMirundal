"""ダンジョン管理システム"""

from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass, field
from enum import Enum
import json
import os

from .dungeon_generator import DungeonGenerator, DungeonLevel, DungeonCell, CellType, Direction
from src.character.party import Party
from src.character.character import Character
from src.utils.logger import logger


class DungeonStatus(Enum):
    """ダンジョンステータス"""
    ACTIVE = "active"           # 探索中
    COMPLETED = "completed"     # 完了
    ABANDONED = "abandoned"     # 放棄


@dataclass
class PlayerPosition:
    """プレイヤー位置情報"""
    x: int
    y: int
    level: int
    facing: Direction = Direction.NORTH
    
    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            'x': self.x,
            'y': self.y,
            'level': self.level,
            'facing': self.facing.value
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PlayerPosition':
        """辞書から復元"""
        return cls(
            x=data['x'],
            y=data['y'],
            level=data['level'],
            facing=Direction(data['facing'])
        )


@dataclass
class DungeonState:
    """ダンジョン状態"""
    dungeon_id: str
    seed: str
    status: DungeonStatus = DungeonStatus.ACTIVE
    player_position: Optional[PlayerPosition] = None
    levels: Dict[int, DungeonLevel] = field(default_factory=dict)
    discovered_cells: Dict[int, List[Tuple[int, int]]] = field(default_factory=dict)
    completed_levels: List[int] = field(default_factory=list)
    
    # 探索統計
    steps_taken: int = 0
    encounters_faced: int = 0
    treasures_found: int = 0
    traps_triggered: int = 0
    
    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            'dungeon_id': self.dungeon_id,
            'seed': self.seed,
            'status': self.status.value,
            'player_position': self.player_position.to_dict() if self.player_position else None,
            'levels': {str(level): level_data.to_dict() for level, level_data in self.levels.items()},
            'discovered_cells': {str(level): cells for level, cells in self.discovered_cells.items()},
            'completed_levels': self.completed_levels,
            'steps_taken': self.steps_taken,
            'encounters_faced': self.encounters_faced,
            'treasures_found': self.treasures_found,
            'traps_triggered': self.traps_triggered
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DungeonState':
        """辞書から復元"""
        state = cls(
            dungeon_id=data['dungeon_id'],
            seed=data['seed'],
            status=DungeonStatus(data['status'])
        )
        
        if data.get('player_position'):
            state.player_position = PlayerPosition.from_dict(data['player_position'])
        
        # レベルデータ復元
        for level_str, level_data in data.get('levels', {}).items():
            level = int(level_str)
            state.levels[level] = DungeonLevel.from_dict(level_data)
        
        # 発見セル復元
        for level_str, cells in data.get('discovered_cells', {}).items():
            level = int(level_str)
            state.discovered_cells[level] = cells
        
        state.completed_levels = data.get('completed_levels', [])
        state.steps_taken = data.get('steps_taken', 0)
        state.encounters_faced = data.get('encounters_faced', 0)
        state.treasures_found = data.get('treasures_found', 0)
        state.traps_triggered = data.get('traps_triggered', 0)
        
        return state


class DungeonManager:
    """ダンジョン管理システム"""
    
    def __init__(self, save_directory: str = "saves/dungeons"):
        self.save_directory = save_directory
        self.generator = DungeonGenerator()
        self.active_dungeons: Dict[str, DungeonState] = {}
        self.current_dungeon: Optional[DungeonState] = None
        
        # 地上部帰還コールバック
        self.return_to_overworld_callback = None
        
        # セーブディレクトリを作成
        os.makedirs(self.save_directory, exist_ok=True)
        
        logger.info("DungeonManager初期化完了")
    
    def set_return_to_overworld_callback(self, callback):
        """地上部帰還コールバックを設定"""
        self.return_to_overworld_callback = callback
        logger.debug("地上部帰還コールバックを設定しました")
    
    def create_dungeon(self, dungeon_id: str, seed: str = "default") -> DungeonState:
        """新しいダンジョンを作成"""
        # 既存のダンジョンチェック
        if dungeon_id in self.active_dungeons:
            logger.warning(f"ダンジョン{dungeon_id}は既に存在します")
            return self.active_dungeons[dungeon_id]
        
        # ダンジョン状態作成
        dungeon_state = DungeonState(
            dungeon_id=dungeon_id,
            seed=seed
        )
        
        # ジェネレーターの初期化
        self.generator = DungeonGenerator(seed)
        
        # 最初のレベルを生成
        first_level = self.generator.generate_level(1)
        dungeon_state.levels[1] = first_level
        
        # プレイヤー位置を設定
        if first_level.start_position:
            dungeon_state.player_position = PlayerPosition(
                x=first_level.start_position[0],
                y=first_level.start_position[1],
                level=1
            )
        
        # 開始位置を発見済みにする
        if first_level.start_position:
            dungeon_state.discovered_cells[1] = [first_level.start_position]
        
        self.active_dungeons[dungeon_id] = dungeon_state
        logger.info(f"ダンジョン{dungeon_id}を作成しました")
        
        return dungeon_state
    
    def enter_dungeon(self, dungeon_id: str, party: Party) -> bool:
        """ダンジョンに入る"""
        if dungeon_id not in self.active_dungeons:
            logger.error(f"ダンジョン{dungeon_id}が見つかりません")
            return False
        
        dungeon_state = self.active_dungeons[dungeon_id]
        
        # ダンジョンの状態チェック
        if dungeon_state.status != DungeonStatus.ACTIVE:
            logger.error(f"ダンジョン{dungeon_id}は探索不可能です: {dungeon_state.status}")
            return False
        
        # パーティの状態チェック
        if not party.is_exploration_ready():
            logger.error("パーティがダンジョン探索に適していません")
            return False
        
        self.current_dungeon = dungeon_state
        logger.info(f"パーティ{party.name}がダンジョン{dungeon_id}に入りました")
        
        return True
    
    def exit_dungeon(self) -> bool:
        """ダンジョンから出る"""
        if not self.current_dungeon:
            logger.warning("現在アクティブなダンジョンがありません")
            return False
        
        # ダンジョン状態を保存
        self.save_dungeon(self.current_dungeon.dungeon_id)
        
        logger.info(f"ダンジョン{self.current_dungeon.dungeon_id}から退出しました")
        self.current_dungeon = None
        
        return True
    
    def return_to_overworld(self) -> bool:
        """地上部に帰還"""
        if not self.current_dungeon:
            logger.warning("現在アクティブなダンジョンがありません")
            return False
        
        # ダンジョンを退出
        success = self.exit_dungeon()
        
        if success and self.return_to_overworld_callback:
            # 地上部帰還コールバックを実行
            logger.info("地上部帰還処理を開始します")
            return self.return_to_overworld_callback()
        
        return success
    
    def move_player(self, direction: Direction) -> Tuple[bool, str]:
        """プレイヤーを移動"""
        if not self.current_dungeon or not self.current_dungeon.player_position:
            return False, "ダンジョンに入っていません"
        
        pos = self.current_dungeon.player_position
        current_level = self.current_dungeon.levels.get(pos.level)
        
        if not current_level:
            return False, "現在のレベルが見つかりません"
        
        # 移動先座標を計算
        dx, dy = self._direction_to_delta(direction)
        new_x, new_y = pos.x + dx, pos.y + dy
        
        # 境界チェック
        if not (0 <= new_x < current_level.width and 0 <= new_y < current_level.height):
            return False, "ダンジョンの境界です"
        
        # 現在のセルから移動可能かチェック
        current_cell = current_level.get_cell(pos.x, pos.y)
        if not current_cell or current_cell.walls.get(direction, True):
            return False, "壁があり移動できません"
        
        # 移動先セルが歩行可能かチェック
        target_cell = current_level.get_cell(new_x, new_y)
        if not target_cell or not current_level.is_walkable(new_x, new_y):
            return False, "移動先に進めません"
        
        # 移動実行
        pos.x, pos.y = new_x, new_y
        self.current_dungeon.steps_taken += 1
        
        # セルを発見済みにする
        if pos.level not in self.current_dungeon.discovered_cells:
            self.current_dungeon.discovered_cells[pos.level] = []
        
        if (new_x, new_y) not in self.current_dungeon.discovered_cells[pos.level]:
            self.current_dungeon.discovered_cells[pos.level].append((new_x, new_y))
            target_cell.discovered = True
        
        target_cell.visited = True
        
        logger.debug(f"プレイヤーが移動: ({pos.x}, {pos.y}) レベル{pos.level}")
        return True, f"移動しました"
    
    def turn_player(self, direction: Direction) -> bool:
        """プレイヤーの向きを変更"""
        if not self.current_dungeon or not self.current_dungeon.player_position:
            return False
        
        self.current_dungeon.player_position.facing = direction
        logger.debug(f"プレイヤーが{direction.value}を向きました")
        return True
    
    def change_level(self, target_level: int) -> Tuple[bool, str]:
        """レベルを変更（階段使用）"""
        if not self.current_dungeon or not self.current_dungeon.player_position:
            return False, "ダンジョンに入っていません"
        
        pos = self.current_dungeon.player_position
        current_level = self.current_dungeon.levels.get(pos.level)
        
        if not current_level:
            return False, "現在のレベルが見つかりません"
        
        # 現在位置の階段チェック
        current_cell = current_level.get_cell(pos.x, pos.y)
        if not current_cell:
            return False, "現在位置が無効です"
        
        # 上階段チェック
        if (target_level == pos.level - 1 and 
            current_cell.cell_type == CellType.STAIRS_UP and
            target_level >= 1):
            
            # 目標レベルが存在しない場合は生成
            if target_level not in self.current_dungeon.levels:
                new_level = self.generator.generate_level(target_level)
                self.current_dungeon.levels[target_level] = new_level
            
            # プレイヤー位置を下階段に設定
            target_level_data = self.current_dungeon.levels[target_level]
            if target_level_data.stairs_down_position:
                pos.x, pos.y = target_level_data.stairs_down_position
                pos.level = target_level
                return True, f"レベル{target_level}に上がりました"
        
        # 下階段チェック
        elif (target_level == pos.level + 1 and 
              current_cell.cell_type == CellType.STAIRS_DOWN and
              target_level <= 20):
            
            # 目標レベルが存在しない場合は生成
            if target_level not in self.current_dungeon.levels:
                new_level = self.generator.generate_level(target_level)
                self.current_dungeon.levels[target_level] = new_level
            
            # プレイヤー位置を上階段に設定
            target_level_data = self.current_dungeon.levels[target_level]
            if target_level_data.stairs_up_position:
                pos.x, pos.y = target_level_data.stairs_up_position
                pos.level = target_level
                return True, f"レベル{target_level}に下りました"
        
        return False, "ここには階段がありません"
    
    def get_current_cell(self) -> Optional[DungeonCell]:
        """現在位置のセルを取得"""
        if not self.current_dungeon or not self.current_dungeon.player_position:
            return None
        
        pos = self.current_dungeon.player_position
        current_level = self.current_dungeon.levels.get(pos.level)
        
        if not current_level:
            return None
        
        return current_level.get_cell(pos.x, pos.y)
    
    def get_visible_cells(self, vision_range: int = 1) -> List[Tuple[int, int, DungeonCell]]:
        """視界内のセルを取得"""
        if not self.current_dungeon or not self.current_dungeon.player_position:
            return []
        
        pos = self.current_dungeon.player_position
        current_level = self.current_dungeon.levels.get(pos.level)
        
        if not current_level:
            return []
        
        visible_cells = []
        
        # 視界範囲内のセルを取得
        for dx in range(-vision_range, vision_range + 1):
            for dy in range(-vision_range, vision_range + 1):
                x, y = pos.x + dx, pos.y + dy
                
                if 0 <= x < current_level.width and 0 <= y < current_level.height:
                    cell = current_level.get_cell(x, y)
                    if cell:
                        visible_cells.append((x, y, cell))
        
        return visible_cells
    
    def save_dungeon(self, dungeon_id: str) -> bool:
        """ダンジョン状態を保存"""
        if dungeon_id not in self.active_dungeons:
            logger.error(f"ダンジョン{dungeon_id}が見つかりません")
            return False
        
        dungeon_state = self.active_dungeons[dungeon_id]
        save_path = os.path.join(self.save_directory, f"{dungeon_id}.json")
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(dungeon_state.to_dict(), f, ensure_ascii=False, indent=2)
            
            logger.info(f"ダンジョン{dungeon_id}を保存しました: {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"ダンジョン保存に失敗: {e}")
            return False
    
    def load_dungeon(self, dungeon_id: str) -> Optional[DungeonState]:
        """ダンジョン状態を読み込み"""
        save_path = os.path.join(self.save_directory, f"{dungeon_id}.json")
        
        if not os.path.exists(save_path):
            logger.warning(f"ダンジョンファイルが見つかりません: {save_path}")
            return None
        
        try:
            with open(save_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            dungeon_state = DungeonState.from_dict(data)
            self.active_dungeons[dungeon_id] = dungeon_state
            
            # ジェネレーターを復元
            self.generator = DungeonGenerator(dungeon_state.seed)
            
            logger.info(f"ダンジョン{dungeon_id}を読み込みました")
            return dungeon_state
            
        except Exception as e:
            logger.error(f"ダンジョン読み込みに失敗: {e}")
            return None
    
    def get_dungeon_info(self, dungeon_id: str) -> Optional[dict]:
        """ダンジョン情報を取得"""
        if dungeon_id not in self.active_dungeons:
            return None
        
        state = self.active_dungeons[dungeon_id]
        
        return {
            'dungeon_id': state.dungeon_id,
            'status': state.status.value,
            'current_level': state.player_position.level if state.player_position else None,
            'levels_explored': len(state.levels),
            'steps_taken': state.steps_taken,
            'encounters_faced': state.encounters_faced,
            'treasures_found': state.treasures_found,
            'traps_triggered': state.traps_triggered
        }
    
    def _direction_to_delta(self, direction: Direction) -> Tuple[int, int]:
        """方向をデルタ座標に変換"""
        direction_map = {
            Direction.NORTH: (0, -1),
            Direction.SOUTH: (0, 1),
            Direction.EAST: (1, 0),
            Direction.WEST: (-1, 0)
        }
        return direction_map[direction]


# グローバルインスタンス
dungeon_manager = DungeonManager()