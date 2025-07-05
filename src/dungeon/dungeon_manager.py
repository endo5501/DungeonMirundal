"""ダンジョン管理システム"""

from typing import Dict, Optional, Tuple, List, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import os
import random

from .dungeon_generator import DungeonGenerator, DungeonLevel, DungeonCell, CellType, Direction
from .trap_system import trap_system, TrapType
from .treasure_system import treasure_system, TreasureType
from .boss_system import boss_system, BossEncounter
from src.character.party import Party
from src.character.character import Character
from src.utils.logger import logger

# ダンジョン管理定数
DEFAULT_SAVE_DIR = "saves/dungeons"
DEFAULT_VISION_RANGE = 1
DEFAULT_MAX_LEVEL = 20
MIN_LEVEL = 1


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
    
    def __init__(self, save_directory: str = DEFAULT_SAVE_DIR):
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
            target_level >= MIN_LEVEL):
            
            # 目標レベルが存在しない場合は生成
            if target_level not in self.current_dungeon.levels:
                new_level = self.generator.generate_level(target_level, self.current_dungeon.dungeon_id)
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
              target_level <= DEFAULT_MAX_LEVEL):
            
            # 目標レベルが存在しない場合は生成
            if target_level not in self.current_dungeon.levels:
                new_level = self.generator.generate_level(target_level, self.current_dungeon.dungeon_id)
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
    
    def get_visible_cells(self, vision_range: int = DEFAULT_VISION_RANGE) -> List[Tuple[int, int, DungeonCell]]:
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
        # dungeon_generatorの同名メソッドを再利用
        from .dungeon_generator import dungeon_generator
        return dungeon_generator._direction_to_delta(direction)
    
    # === Phase 5: パーティ状態管理機能 ===
    
    def check_party_status(self, party) -> Dict[str, Any]:
        """パーティ状態をチェック"""
        if not party:
            return {"can_continue": False, "reason": "パーティが設定されていません"}
        
        living_members = party.get_living_characters()
        total_members = len(party.members)
        
        status = {
            "can_continue": len(living_members) > 0,
            "living_count": len(living_members),
            "total_count": total_members,
            "all_dead": len(living_members) == 0,
            "needs_healing": False,
            "critically_injured": [],
            "dead_members": []
        }
        
        # 詳細な状態分析
        for member in party.members:
            if not member.is_alive():
                status["dead_members"].append(member.name)
            elif member.derived_stats.current_hp <= member.derived_stats.max_hp * 0.2:
                # HP20%以下は重傷
                status["critically_injured"].append(member.name)
                status["needs_healing"] = True
        
        return status
    
    def should_force_retreat(self, party) -> Tuple[bool, str]:
        """強制的な撤退が必要かチェック"""
        status = self.check_party_status(party)
        
        if status["all_dead"]:
            return True, "パーティ全滅"
        
        if status["living_count"] == 1 and status["critically_injured"]:
            return True, "残り1名が重傷"
        
        return False, ""
    
    def handle_member_death(self, party, dead_character_name: str):
        """メンバー死亡時の処理"""
        logger.warning(f"ダンジョン内でメンバー死亡: {dead_character_name}")
        
        # パーティ状態をチェック
        should_retreat, reason = self.should_force_retreat(party)
        
        if should_retreat:
            logger.critical(f"強制撤退条件: {reason}")
            # GameManagerに強制撤退を通知（コールバック経由）
            if hasattr(self, 'force_retreat_callback') and self.force_retreat_callback:
                self.force_retreat_callback(reason)
    
    def set_force_retreat_callback(self, callback):
        """強制撤退コールバックを設定"""
        self.force_retreat_callback = callback
    
    # === Phase 5 Day 25-26: トラップ・宝箱・ボス戦システム統合 ===
    
    def interact_with_current_cell(self, party: Party, character = None) -> Dict[str, Any]:
        """現在位置のセルとのインタラクション"""
        current_cell = self.get_current_cell()
        if not current_cell:
            return {"success": False, "message": "現在位置が無効です"}
        
        result = {"success": True, "message": "", "interactions": []}
        
        # トラップチェック
        if current_cell.has_trap and current_cell.trap_type:
            trap_result = self._handle_trap_interaction(current_cell, party)
            result["interactions"].append(trap_result)
        
        # 宝箱チェック
        if current_cell.has_treasure and current_cell.treasure_id:
            treasure_result = self._handle_treasure_interaction(current_cell, party, character)
            result["interactions"].append(treasure_result)
        
        # ボス戦チェック
        if current_cell.cell_type == CellType.BOSS:
            boss_result = self._handle_boss_interaction(current_cell, party)
            result["interactions"].append(boss_result)
        
        if not result["interactions"]:
            result["message"] = "特に何もない"
        else:
            result["message"] = f"{len(result['interactions'])}個のインタラクションが発生"
        
        return result
    
    def _handle_trap_interaction(self, cell: DungeonCell, party: Party) -> Dict[str, Any]:
        """トラップとのインタラクション"""
        try:
            trap_type = TrapType(cell.trap_type)
        except ValueError:
            logger.warning(f"無効なトラップタイプ: {cell.trap_type}")
            return {"type": "trap", "success": False, "message": "無効なトラップです"}
        
        # トラップ発見判定
        living_members = party.get_living_characters()
        detected = False
        detector = None
        
        for member in living_members:
            if trap_system.can_detect_trap(member, trap_type):
                detected = True
                detector = member
                break
        
        if detected:
            # 解除試行
            if trap_system.can_disarm_trap(detector, trap_type):
                logger.info(f"{detector.name}がトラップを解除しました")
                cell.has_trap = False
                cell.trap_type = None
                return {
                    "type": "trap", 
                    "success": True, 
                    "message": f"{detector.name}がトラップを発見・解除した！",
                    "disarmed": True
                }
            else:
                logger.info(f"{detector.name}がトラップを発見しましたが解除に失敗")
                # 発見したが解除失敗 - 発動
                trap_result = trap_system.activate_trap(trap_type, party, self.current_dungeon.player_position.level)
                trap_result["type"] = "trap"
                trap_result["detected"] = True
                trap_result["disarm_failed"] = True
                return trap_result
        else:
            # 発見失敗 - 発動
            trap_result = trap_system.activate_trap(trap_type, party, self.current_dungeon.player_position.level)
            trap_result["type"] = "trap"
            trap_result["detected"] = False
            return trap_result
    
    def _handle_treasure_interaction(self, cell: DungeonCell, party: Party, opener_character = None) -> Dict[str, Any]:
        """宝箱とのインタラクション"""
        treasure_id = cell.treasure_id
        
        # 宝箱タイプを決定（既存の場合は保持、新規の場合は生成）
        treasure_type = getattr(cell, 'treasure_type', None)
        if not treasure_type:
            treasure_type = treasure_system.generate_treasure_type(self.current_dungeon.player_position.level)
            cell.treasure_type = treasure_type
        else:
            try:
                treasure_type = TreasureType(treasure_type)
            except ValueError:
                treasure_type = treasure_system.generate_treasure_type(self.current_dungeon.player_position.level)
        
        # 宝箱開封
        treasure_result = treasure_system.open_treasure(
            treasure_id, 
            treasure_type, 
            party, 
            self.current_dungeon.player_position.level,
            opener_character
        )
        treasure_result["type"] = "treasure"
        
        # ミミックの場合は戦闘発生
        if treasure_result.get("mimic"):
            treasure_result["start_combat"] = True
            treasure_result["mimic_monster"] = self._generate_mimic_monster()
        
        # 開封成功時はセルから宝箱を除去
        if treasure_result.get("success") and not treasure_result.get("mimic"):
            cell.has_treasure = False
            cell.treasure_id = None
            if hasattr(cell, 'treasure_type'):
                delattr(cell, 'treasure_type')
        
        return treasure_result
    
    def _handle_boss_interaction(self, cell: DungeonCell, party: Party) -> Dict[str, Any]:
        """ボス戦とのインタラクション"""
        dungeon_level = self.current_dungeon.player_position.level
        
        # ボス生成
        boss_id = boss_system.generate_boss_for_level(dungeon_level)
        if not boss_id:
            logger.warning(f"レベル {dungeon_level} に適したボスが見つかりません")
            return {"type": "boss", "success": False, "message": "ボスが見つかりません"}
        
        # ボス戦エンカウンター作成
        encounter_id = f"boss_{self.current_dungeon.dungeon_id}_{dungeon_level}_{cell.x}_{cell.y}"
        encounter = boss_system.create_boss_encounter(boss_id, dungeon_level, encounter_id)
        
        if not encounter:
            return {"type": "boss", "success": False, "message": "ボス戦の準備に失敗しました"}
        
        # ボスモンスター初期化
        boss_monster = encounter.initialize_boss_monster()
        
        return {
            "type": "boss",
            "success": True,
            "message": f"強大な敵「{encounter.boss_data.name}」が現れた！",
            "start_combat": True,
            "boss_encounter": encounter,
            "boss_monster": boss_monster,
            "encounter_id": encounter_id
        }
    
    def _generate_mimic_monster(self):
        """ミミックモンスターを生成"""
        from src.monsters.monster import Monster, MonsterStats, MonsterType, MonsterSize
        
        level = self.current_dungeon.player_position.level
        stats = MonsterStats(
            level=level + 2,
            hit_points=40 + level * 8,
            armor_class=12 + level,
            attack_bonus=2 + level,
            damage_dice="1d8",
            strength=12 + level * 2,
            agility=10 + level,
            intelligence=5,
            faith=3,
            luck=8
        )
        
        mimic = Monster(
            monster_id=f"mimic_{level}",
            name="ミミック",
            description="宝箱に擬態した奸計深いモンスター",
            monster_type=MonsterType.ABERRATION,
            size=MonsterSize.MEDIUM,
            stats=stats,
            experience_value=30 + level * 5
        )
        
        return mimic
    
    def check_for_secret_interactions(self, party: Party) -> Dict[str, Any]:
        """隠された要素との相互作用をチェック"""
        current_cell = self.get_current_cell()
        if not current_cell:
            return {"success": False, "message": "現在位置が無効です"}
        
        interactions = []
        
        # 隠し通路チェック
        if self._check_secret_passage():
            interactions.append({
                "type": "secret_passage",
                "message": "隠し通路を発見した！",
                "action_available": True
            })
        
        # 隠し宝箱チェック
        if self._check_secret_treasure(party):
            interactions.append({
                "type": "secret_treasure", 
                "message": "隠された宝箱を発見した！",
                "action_available": True
            })
        
        return {
            "success": True,
            "interactions": interactions,
            "count": len(interactions)
        }
    
    def _check_secret_passage(self) -> bool:
        """隠し通路の発見判定"""
        # 簡易実装: 各セルで5%の確率で隠し通路
        return random.random() < 0.05
    
    def _check_secret_treasure(self, party: Party) -> bool:
        """隠し宝箱の発見判定"""
        # パーティメンバーの知力・レベルに応じて発見率が変動
        living_members = party.get_living_characters()
        if not living_members:
            return False
        
        best_intelligence = max(member.base_stats.intelligence for member in living_members)
        best_level = max(member.experience.level for member in living_members)
        
        discovery_rate = 0.02 + (best_intelligence - 10) * 0.005 + best_level * 0.001
        
        return random.random() < discovery_rate
    
    def complete_boss_encounter(self, encounter_id: str, victory: bool, party: Party) -> Dict[str, Any]:
        """ボス戦完了処理"""
        result = boss_system.complete_boss_encounter(encounter_id, victory)
        
        if victory and "rewards" in result:
            rewards = result["rewards"]
            
            # 経験値付与
            if "experience" in rewards:
                for character in party.get_living_characters():
                    character.add_experience(rewards["experience"])
            
            # 金貨付与
            if "gold" in rewards:
                party.gold += rewards["gold"]
            
            # アイテム付与
            if "items" in rewards:
                for item_name in rewards["items"]:
                    # 実際のアイテム生成は省略
                    logger.info(f"特別アイテム「{item_name}」を獲得しました")
        
        return result


# グローバルインスタンス
dungeon_manager = DungeonManager()