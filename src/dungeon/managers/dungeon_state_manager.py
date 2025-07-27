"""ダンジョン状態管理"""

from typing import Dict, Optional, Tuple, List, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import os

from ..dungeon_generator import DungeonGenerator, DungeonLevel, Direction
from src.character.party import Party
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


class DungeonStateManager:
    """ダンジョン状態管理"""
    
    def __init__(self, save_directory: str = "saves/dungeons"):
        self.save_directory = save_directory
        self.generator = DungeonGenerator()
        self.active_dungeons: Dict[str, DungeonState] = {}
        self.current_dungeon: Optional[DungeonState] = None
        
        # セーブディレクトリを作成
        os.makedirs(self.save_directory, exist_ok=True)
        
        logger.debug("DungeonStateManager初期化完了")
    
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
        first_level = self.generator.generate_level(1, dungeon_id)
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
        
        # 作成直後にファイル保存
        try:
            self.save_dungeon(dungeon_id)
            logger.info(f"ダンジョン{dungeon_id}のファイル保存が完了しました")
        except Exception as save_error:
            logger.warning(f"ダンジョン{dungeon_id}のファイル保存に失敗しましたが、メモリ上では利用可能です: {save_error}")
        
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
            # 自動復旧: 新規作成を試行
            logger.info(f"ダンジョン{dungeon_id}の自動復旧を試行します")
            try:
                return self.create_dungeon(dungeon_id, dungeon_id)
            except Exception as recovery_error:
                logger.error(f"ダンジョン自動復旧に失敗: {recovery_error}")
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
    
    def get_current_dungeon(self) -> Optional[DungeonState]:
        """現在のダンジョン状態を取得"""
        return self.current_dungeon
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        try:
            # アクティブなダンジョンを保存
            for dungeon_id in list(self.active_dungeons.keys()):
                self.save_dungeon(dungeon_id)
            
            # 現在のダンジョンをクリア
            self.current_dungeon = None
            
            # アクティブダンジョンをクリア
            self.active_dungeons.clear()
            
            # ジェネレーターをクリア
            self.generator = None
            
            logger.info("DungeonStateManager リソースをクリーンアップしました")
        except Exception as e:
            logger.error(f"DungeonStateManager クリーンアップ中にエラー: {e}")