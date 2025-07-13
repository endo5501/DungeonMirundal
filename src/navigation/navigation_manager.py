"""ナビゲーション管理システム"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import time
import random

from src.dungeon.dungeon_manager import DungeonManager, DungeonState, PlayerPosition
from src.dungeon.dungeon_generator import Direction, CellType, DungeonLevel, DungeonCell
from src.character.party import Party
from src.utils.logger import logger

# ナビゲーションシステム定数
DEFAULT_MOVEMENT_SPEED = 1.0
DEFAULT_ENCOUNTER_RATE = 1.0
DEFAULT_STEP_COUNT = 0
DEFAULT_POSITION = (0, 0, 0)
MAX_HISTORY_SIZE = 100
BASE_ENCOUNTER_RATE = 0.05
ENCOUNTER_STEP_THRESHOLD = 20
ANIMATION_DURATION = 0.3
DEFAULT_VISION_RANGE = 2
SNEAK_SPEED_MULTIPLIER = 0.5
SNEAK_ENCOUNTER_REDUCTION = 0.3
WALK_SPEED_MULTIPLIER = 1.0
RUN_SPEED_MULTIPLIER = 1.5
TELEPORT_SPEED_MULTIPLIER = 0.0
TRAP_AVOID_CHANCE_BASE = 0.1
TRAP_AVOID_CHANCE_SNEAK = 0.3
AGILITY_BASE_VALUE = 10
AGILITY_BONUS_RATE = 0.01
ENCOUNTER_SNEAK_MULTIPLIER = 0.5
ENCOUNTER_RUN_MULTIPLIER = 1.5
ENCOUNTER_STEP_INCREASE_RATE = 0.05
FIRST_ELEMENT_INDEX = 0


class MovementType(Enum):
    """移動タイプ"""
    WALK = "walk"           # 歩行
    RUN = "run"             # 走行
    SNEAK = "sneak"         # 忍び歩き
    TELEPORT = "teleport"   # テレポート


class MovementResult(Enum):
    """移動結果"""
    SUCCESS = "success"                 # 成功
    BLOCKED_BY_WALL = "blocked_by_wall" # 壁で阻止
    OUT_OF_BOUNDS = "out_of_bounds"     # 境界外
    INVALID_TARGET = "invalid_target"   # 無効な目標
    ENCOUNTER = "encounter"             # エンカウンター発生
    TRAP_TRIGGERED = "trap_triggered"   # トラップ発動
    TREASURE_FOUND = "treasure_found"   # 宝箱発見
    STAIRS_FOUND = "stairs_found"       # 階段発見


@dataclass
class MovementEvent:
    """移動イベント"""
    result: MovementResult
    message: str
    old_position: Tuple[int, int, int]  # (x, y, level)
    new_position: Tuple[int, int, int]  # (x, y, level)
    additional_data: Optional[Dict[str, Any]] = None


@dataclass
class NavigationState:
    """ナビゲーション状態"""
    movement_speed: float = 1.0         # 移動速度倍率
    encounter_rate: float = 1.0         # エンカウンター率倍率
    auto_map_enabled: bool = True       # オートマップ有効
    step_count: int = 0                 # 歩数カウント
    last_encounter_step: int = 0        # 最後のエンカウンター歩数
    sneak_mode: bool = False            # 忍び足モード


class NavigationManager:
    """ナビゲーション管理システム"""
    
    def __init__(self):
        self.dungeon_manager: Optional[DungeonManager] = None
        self.current_party: Optional[Party] = None
        self.navigation_state = NavigationState()
        
        # 移動履歴
        self.movement_history: List[MovementEvent] = []
        self.max_history_size = MAX_HISTORY_SIZE
        
        # エンカウンター設定
        self.base_encounter_rate = BASE_ENCOUNTER_RATE
        self.encounter_step_threshold = ENCOUNTER_STEP_THRESHOLD
        
        # 移動アニメーション設定
        self.animation_enabled = True
        self.animation_duration = ANIMATION_DURATION
        
        logger.debug("NavigationManager初期化完了")
    
    def set_dungeon_manager(self, dungeon_manager: DungeonManager):
        """ダンジョンマネージャー設定"""
        self.dungeon_manager = dungeon_manager
        logger.info("ダンジョンマネージャーを設定しました")
    
    def set_party(self, party: Party):
        """パーティ設定"""
        # 循環参照防止：既に同じパーティが設定されている場合はスキップ
        if self.current_party is party:
            return
            
        self.current_party = party
        logger.info(f"パーティ{party.name}を設定しました")
    
    def move_player(self, direction: Direction, movement_type: MovementType = MovementType.WALK) -> MovementEvent:
        """プレイヤー移動"""
        # 事前チェック
        validation_result = self._validate_movement_preconditions()
        if validation_result:
            return validation_result
        
        dungeon_state = self.dungeon_manager.current_dungeon
        old_pos = dungeon_state.player_position
        old_position = (old_pos.x, old_pos.y, old_pos.level)
        
        # 移動速度の調整
        speed_multiplier = self._get_speed_multiplier(movement_type)
        
        # 基本移動処理
        success, message = self.dungeon_manager.move_player(direction)
        
        new_pos = dungeon_state.player_position
        new_position = (new_pos.x, new_pos.y, new_pos.level)
        
        if not success:
            return self._create_movement_failure_event(message, old_position)
        
        # 移動成功 - ステップカウント更新
        self.navigation_state.step_count += 1
        
        # セルイベントチェック
        cell_event = self._check_cell_events(old_position, new_position, movement_type)
        if cell_event:
            return cell_event
        
        # エンカウンターチェック
        encounter_event = self._check_encounter_event(old_position, new_position, movement_type)
        if encounter_event:
            return encounter_event
        
        # 通常の移動成功イベント作成
        return self._create_success_movement_event(movement_type, old_position, new_position)
    
    def _validate_movement_preconditions(self) -> Optional[MovementEvent]:
        """移動の事前条件をチェック"""
        if not self.dungeon_manager or not self.dungeon_manager.current_dungeon:
            return MovementEvent(
                result=MovementResult.INVALID_TARGET,
                message="ダンジョンに入っていません",
                old_position=DEFAULT_POSITION,
                new_position=DEFAULT_POSITION
            )
        
        dungeon_state = self.dungeon_manager.current_dungeon
        if not dungeon_state.player_position:
            return MovementEvent(
                result=MovementResult.INVALID_TARGET,
                message="プレイヤー位置が無効です",
                old_position=DEFAULT_POSITION,
                new_position=DEFAULT_POSITION
            )
        
        return None
    
    def _create_movement_failure_event(self, message: str, old_position: Tuple[int, int, int]) -> MovementEvent:
        """移動失敗イベントを作成"""
        result = self._determine_movement_failure(message)
        return MovementEvent(
            result=result,
            message=message,
            old_position=old_position,
            new_position=old_position
        )
    
    def _check_cell_events(self, old_position: Tuple[int, int, int], new_position: Tuple[int, int, int], movement_type: MovementType) -> Optional[MovementEvent]:
        """セルイベントをチェック"""
        current_cell = self.dungeon_manager.get_current_cell()
        if not current_cell:
            return None
        
        # トラップチェック
        trap_event = self._check_trap_event(current_cell, movement_type, old_position, new_position)
        if trap_event:
            return trap_event
        
        # 宝箱チェック
        treasure_event = self._check_treasure_event(current_cell, old_position, new_position)
        if treasure_event:
            return treasure_event
        
        # 階段チェック
        stairs_event = self._check_stairs_event(current_cell, old_position, new_position)
        if stairs_event:
            return stairs_event
        
        return None
    
    def _check_trap_event(self, current_cell: DungeonCell, movement_type: MovementType, old_position: Tuple[int, int, int], new_position: Tuple[int, int, int]) -> Optional[MovementEvent]:
        """トラップイベントをチェック"""
        trap_event = self._check_trap(current_cell, movement_type)
        if trap_event:
            return MovementEvent(
                result=MovementResult.TRAP_TRIGGERED,
                message=trap_event,
                old_position=old_position,
                new_position=new_position,
                additional_data={"trap_type": current_cell.trap_type}
            )
        return None
    
    def _check_treasure_event(self, current_cell: DungeonCell, old_position: Tuple[int, int, int], new_position: Tuple[int, int, int]) -> Optional[MovementEvent]:
        """宝箱イベントをチェック"""
        if current_cell.has_treasure:
            return MovementEvent(
                result=MovementResult.TREASURE_FOUND,
                message="宝箱を発見しました！",
                old_position=old_position,
                new_position=new_position,
                additional_data={"treasure_id": current_cell.treasure_id}
            )
        return None
    
    def _check_stairs_event(self, current_cell: DungeonCell, old_position: Tuple[int, int, int], new_position: Tuple[int, int, int]) -> Optional[MovementEvent]:
        """階段イベントをチェック"""
        if current_cell.cell_type in [CellType.STAIRS_UP, CellType.STAIRS_DOWN]:
            stairs_type = "上り階段" if current_cell.cell_type == CellType.STAIRS_UP else "下り階段"
            return MovementEvent(
                result=MovementResult.STAIRS_FOUND,
                message=f"{stairs_type}を発見しました",
                old_position=old_position,
                new_position=new_position,
                additional_data={"stairs_type": current_cell.cell_type.value}
            )
        return None
    
    def _check_encounter_event(self, old_position: Tuple[int, int, int], new_position: Tuple[int, int, int], movement_type: MovementType) -> Optional[MovementEvent]:
        """エンカウンターイベントをチェック"""
        encounter_check = self._check_encounter(movement_type)
        if encounter_check:
            self.navigation_state.last_encounter_step = self.navigation_state.step_count
            return MovementEvent(
                result=MovementResult.ENCOUNTER,
                message="モンスターと遭遇しました！",
                old_position=old_position,
                new_position=new_position,
                additional_data={"encounter_type": encounter_check}
            )
        return None
    
    def _create_success_movement_event(self, movement_type: MovementType, old_position: Tuple[int, int, int], new_position: Tuple[int, int, int]) -> MovementEvent:
        """成功した移動イベントを作成"""
        event = MovementEvent(
            result=MovementResult.SUCCESS,
            message=f"{movement_type.value}で移動しました",
            old_position=old_position,
            new_position=new_position
        )
        
        # 移動履歴に追加
        self._add_to_history(event)
        
        return event
    
    def turn_player(self, direction: Direction) -> bool:
        """プレイヤー回転"""
        if not self.dungeon_manager:
            return False
        
        success = self.dungeon_manager.turn_player(direction)
        
        if success:
            # 回転イベントを履歴に追加
            if self.dungeon_manager.current_dungeon and self.dungeon_manager.current_dungeon.player_position:
                pos = self.dungeon_manager.current_dungeon.player_position
                position = (pos.x, pos.y, pos.level)
                
                turn_event = MovementEvent(
                    result=MovementResult.SUCCESS,
                    message=f"{direction.value}を向きました",
                    old_position=position,
                    new_position=position
                )
                self._add_to_history(turn_event)
        
        return success
    
    def use_stairs(self, direction: str) -> MovementEvent:
        """階段使用"""
        if not self.dungeon_manager or not self.dungeon_manager.current_dungeon:
            return MovementEvent(
                result=MovementResult.INVALID_TARGET,
                message="ダンジョンに入っていません",
                old_position=(0, 0, 0),
                new_position=(0, 0, 0)
            )
        
        current_cell = self.dungeon_manager.get_current_cell()
        if not current_cell:
            return MovementEvent(
                result=MovementResult.INVALID_TARGET,
                message="現在位置が無効です",
                old_position=(0, 0, 0),
                new_position=(0, 0, 0)
            )
        
        dungeon_state = self.dungeon_manager.current_dungeon
        old_pos = dungeon_state.player_position
        old_position = (old_pos.x, old_pos.y, old_pos.level)
        
        # 階段の方向を確認
        if direction == "up" and current_cell.cell_type == CellType.STAIRS_UP:
            target_level = old_pos.level - 1
        elif direction == "down" and current_cell.cell_type == CellType.STAIRS_DOWN:
            target_level = old_pos.level + 1
        else:
            return MovementEvent(
                result=MovementResult.INVALID_TARGET,
                message="ここには対応する階段がありません",
                old_position=old_position,
                new_position=old_position
            )
        
        # 階段使用
        success, message = self.dungeon_manager.change_level(target_level)
        
        new_pos = dungeon_state.player_position
        new_position = (new_pos.x, new_pos.y, new_pos.level)
        
        if success:
            event = MovementEvent(
                result=MovementResult.SUCCESS,
                message=message,
                old_position=old_position,
                new_position=new_position,
                additional_data={"level_change": target_level - old_pos.level}
            )
            self._add_to_history(event)
            return event
        else:
            return MovementEvent(
                result=MovementResult.INVALID_TARGET,
                message=message,
                old_position=old_position,
                new_position=old_position
            )
    
    def set_movement_mode(self, sneak: bool = False, auto_map: bool = True):
        """移動モード設定"""
        self.navigation_state.sneak_mode = sneak
        self.navigation_state.auto_map_enabled = auto_map
        
        self._apply_movement_speed_settings(sneak)
        
        logger.debug(f"移動モード変更: 忍び足={sneak}, オートマップ={auto_map}")
    
    def _apply_movement_speed_settings(self, sneak: bool):
        """移動速度設定を適用"""
        if sneak:
            self.navigation_state.movement_speed = SNEAK_SPEED_MULTIPLIER
            self.navigation_state.encounter_rate = SNEAK_ENCOUNTER_REDUCTION
        else:
            self.navigation_state.movement_speed = DEFAULT_MOVEMENT_SPEED
            self.navigation_state.encounter_rate = DEFAULT_ENCOUNTER_RATE
    
    def get_movement_history(self, limit: int = 10) -> List[MovementEvent]:
        """移動履歴取得"""
        return self.movement_history[-limit:]
    
    def get_navigation_status(self) -> Dict[str, Any]:
        """ナビゲーション状態取得"""
        return {
            'step_count': self.navigation_state.step_count,
            'sneak_mode': self.navigation_state.sneak_mode,
            'auto_map_enabled': self.navigation_state.auto_map_enabled,
            'movement_speed': self.navigation_state.movement_speed,
            'encounter_rate': self.navigation_state.encounter_rate,
            'last_encounter_step': self.navigation_state.last_encounter_step,
            'steps_since_encounter': self.navigation_state.step_count - self.navigation_state.last_encounter_step
        }
    
    def _get_speed_multiplier(self, movement_type: MovementType) -> float:
        """移動速度倍率取得"""
        speed_map = {
            MovementType.WALK: WALK_SPEED_MULTIPLIER,
            MovementType.RUN: RUN_SPEED_MULTIPLIER,
            MovementType.SNEAK: SNEAK_SPEED_MULTIPLIER,
            MovementType.TELEPORT: TELEPORT_SPEED_MULTIPLIER
        }
        return speed_map.get(movement_type, DEFAULT_MOVEMENT_SPEED) * self.navigation_state.movement_speed
    
    def _determine_movement_failure(self, message: str) -> MovementResult:
        """移動失敗原因判定"""
        if "壁" in message:
            return MovementResult.BLOCKED_BY_WALL
        elif "境界" in message:
            return MovementResult.OUT_OF_BOUNDS
        else:
            return MovementResult.INVALID_TARGET
    
    def _check_trap(self, cell: DungeonCell, movement_type: MovementType) -> Optional[str]:
        """トラップチェック"""
        if not cell.has_trap:
            return None
        
        avoid_chance = self._calculate_trap_avoid_chance(movement_type)
        
        if random.random() < avoid_chance:
            return None  # トラップ回避
        
        # トラップ発動統計更新
        self._update_trap_statistics()
        
        return self._get_trap_message(cell.trap_type)
    
    def _calculate_trap_avoid_chance(self, movement_type: MovementType) -> float:
        """トラップ回避率を計算"""
        avoid_chance = TRAP_AVOID_CHANCE_SNEAK if movement_type == MovementType.SNEAK else TRAP_AVOID_CHANCE_BASE
        
        # パーティの敏捷性も考慮
        if self.current_party:
            living_chars = self.current_party.get_living_characters()
            if living_chars:
                avg_agility = sum(char.base_stats.agility for char in living_chars)
                avg_agility /= len(living_chars)
                avoid_chance += (avg_agility - AGILITY_BASE_VALUE) * AGILITY_BONUS_RATE
        
        return avoid_chance
    
    def _update_trap_statistics(self):
        """トラップ統計を更新"""
        if self.dungeon_manager and self.dungeon_manager.current_dungeon:
            self.dungeon_manager.current_dungeon.traps_triggered += 1
    
    def _get_trap_message(self, trap_type: str) -> str:
        """トラップメッセージを取得"""
        trap_messages = {
            "poison": "毒ガストラップが発動！",
            "paralysis": "麻痺トラップが発動！",
            "damage": "ダメージトラップが発動！",
            "teleport": "テレポートトラップが発動！"
        }
        
        return trap_messages.get(trap_type, "トラップが発動しました！")
    
    def _check_encounter(self, movement_type: MovementType) -> Optional[str]:
        """エンカウンターチェック"""
        if not self.dungeon_manager or not self.dungeon_manager.current_dungeon:
            return None
        
        dungeon_state = self.dungeon_manager.current_dungeon
        current_level = dungeon_state.levels.get(dungeon_state.player_position.level)
        
        if not current_level:
            return None
        
        encounter_rate = self._calculate_encounter_rate(current_level, movement_type)
        
        # エンカウンター判定
        if random.random() < encounter_rate:
            # エンカウンター発生統計更新
            dungeon_state.encounters_faced += 1
            
            return self._determine_encounter_type()
        
        return None
    
    def _calculate_encounter_rate(self, current_level: DungeonLevel, movement_type: MovementType) -> float:
        """エンカウンター率を計算"""
        # 基本エンカウンター率
        encounter_rate = current_level.encounter_rate * self.navigation_state.encounter_rate
        
        # 移動タイプによる調整
        encounter_rate *= self._get_movement_encounter_multiplier(movement_type)
        
        # 歩数による調整
        encounter_rate *= self._get_step_encounter_multiplier()
        
        return encounter_rate
    
    def _get_movement_encounter_multiplier(self, movement_type: MovementType) -> float:
        """移動タイプによるエンカウンター率倍率を取得"""
        if movement_type == MovementType.SNEAK:
            return ENCOUNTER_SNEAK_MULTIPLIER
        elif movement_type == MovementType.RUN:
            return ENCOUNTER_RUN_MULTIPLIER
        else:
            return DEFAULT_MOVEMENT_SPEED
    
    def _get_step_encounter_multiplier(self) -> float:
        """歩数によるエンカウンター率倍率を取得"""
        steps_since_encounter = self.navigation_state.step_count - self.navigation_state.last_encounter_step
        if steps_since_encounter > self.encounter_step_threshold:
            return DEFAULT_MOVEMENT_SPEED + (steps_since_encounter - self.encounter_step_threshold) * ENCOUNTER_STEP_INCREASE_RATE
        return DEFAULT_MOVEMENT_SPEED
    
    def _determine_encounter_type(self) -> str:
        """エンカウンタータイプを決定"""
        encounter_types = ["normal", "ambush", "treasure_guardian"]
        return random.choice(encounter_types)
    
    def _add_to_history(self, event: MovementEvent):
        """履歴に追加"""
        self.movement_history.append(event)
        
        # 履歴サイズ制限
        if len(self.movement_history) > self.max_history_size:
            self.movement_history.pop(0)
    
    def get_visible_area(self, vision_range: int = DEFAULT_VISION_RANGE) -> List[Tuple[int, int, DungeonCell]]:
        """視界エリア取得"""
        if not self.dungeon_manager:
            return []
        
        return self.dungeon_manager.get_visible_cells(vision_range)
    
    def get_auto_map_data(self) -> Dict[str, Any]:
        """オートマップデータ取得"""
        if not self.navigation_state.auto_map_enabled or not self.dungeon_manager:
            return {}
        
        dungeon_state = self.dungeon_manager.current_dungeon
        if not dungeon_state:
            return {}
        
        current_level = dungeon_state.levels.get(dungeon_state.player_position.level)
        if not current_level:
            return {}
        
        # 発見済みセルの情報を収集
        discovered_cells = dungeon_state.discovered_cells.get(dungeon_state.player_position.level, [])
        
        map_data = self._create_map_data_structure(dungeon_state, discovered_cells)
        
        # 発見済みセルの詳細情報を追加
        self._add_cell_details_to_map_data(map_data, discovered_cells, current_level)
        
        return map_data
    
    def _create_map_data_structure(self, dungeon_state: DungeonState, discovered_cells: List[Tuple[int, int]]) -> Dict[str, Any]:
        """マップデータ構造を作成"""
        return {
            'level': dungeon_state.player_position.level,
            'player_position': (dungeon_state.player_position.x, dungeon_state.player_position.y),
            'player_facing': dungeon_state.player_position.facing.value,
            'discovered_cells': discovered_cells,
            'cell_details': {}
        }
    
    def _add_cell_details_to_map_data(self, map_data: Dict[str, Any], discovered_cells: List[Tuple[int, int]], current_level: DungeonLevel):
        """マップデータにセル詳細情報を追加"""
        for x, y in discovered_cells:
            cell = current_level.get_cell(x, y)
            if cell:
                map_data['cell_details'][f"{x},{y}"] = {
                    'type': cell.cell_type.value,
                    'has_treasure': cell.has_treasure,
                    'has_trap': cell.has_trap,
                    'visited': cell.visited
                }


# グローバルインスタンス
navigation_manager = NavigationManager()