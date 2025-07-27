"""リファクタリング後のダンジョン管理システム"""

from typing import Dict, Optional, Tuple, List, Any

from .managers.dungeon_state_manager import DungeonStateManager, DungeonState, PlayerPosition, DungeonStatus
from .managers.dungeon_navigation_manager import DungeonNavigationManager
from .managers.dungeon_interaction_manager import DungeonInteractionManager
from .dungeon_generator import DungeonCell, Direction
from src.character.party import Party
from src.character.character import Character
from src.utils.logger import logger


class DungeonManager:
    """リファクタリング後のダンジョン管理システム（ファサードパターン）"""
    
    def __init__(self, save_directory: str = "saves/dungeons"):
        # 各管理コンポーネントを初期化
        self.state_manager = DungeonStateManager(save_directory)
        self.navigation_manager = DungeonNavigationManager(self.state_manager)
        self.interaction_manager = DungeonInteractionManager(self.state_manager, self.navigation_manager)
        
        logger.info("DungeonManager（リファクタリング版）初期化完了")
    
    # === ファサードメソッド：各管理コンポーネントの機能を統合 ===
    
    # 状態管理系メソッド
    def create_dungeon(self, dungeon_id: str, seed: str = "default") -> DungeonState:
        """新しいダンジョンを作成"""
        return self.state_manager.create_dungeon(dungeon_id, seed)
    
    def enter_dungeon(self, dungeon_id: str, party: Party) -> bool:
        """ダンジョンに入る"""
        return self.state_manager.enter_dungeon(dungeon_id, party)
    
    def exit_dungeon(self) -> bool:
        """ダンジョンから出る"""
        return self.state_manager.exit_dungeon()
    
    def save_dungeon(self, dungeon_id: str) -> bool:
        """ダンジョン状態を保存"""
        return self.state_manager.save_dungeon(dungeon_id)
    
    def load_dungeon(self, dungeon_id: str) -> Optional[DungeonState]:
        """ダンジョン状態を読み込み"""
        return self.state_manager.load_dungeon(dungeon_id)
    
    def get_dungeon_info(self, dungeon_id: str) -> Optional[dict]:
        """ダンジョン情報を取得"""
        return self.state_manager.get_dungeon_info(dungeon_id)
    
    # ナビゲーション系メソッド
    def set_return_to_overworld_callback(self, callback):
        """地上部帰還コールバックを設定"""
        self.navigation_manager.set_return_to_overworld_callback(callback)
    
    def return_to_overworld(self) -> bool:
        """地上部に帰還"""
        return self.navigation_manager.return_to_overworld()
    
    def use_stairs(self) -> Tuple[bool, str, Optional[str]]:
        """階段または出口を使用"""
        return self.navigation_manager.use_stairs()
    
    def move_player(self, direction: Direction) -> Tuple[bool, str]:
        """プレイヤーを移動"""
        return self.navigation_manager.move_player(direction)
    
    def turn_player(self, direction: Direction) -> bool:
        """プレイヤーの向きを変更"""
        return self.navigation_manager.turn_player(direction)
    
    def turn_player_left(self) -> bool:
        """プレイヤーを左に回転"""
        return self.navigation_manager.turn_player_left()
    
    def turn_player_right(self) -> bool:
        """プレイヤーを右に回転"""
        return self.navigation_manager.turn_player_right()
    
    def change_level(self, target_level: int) -> Tuple[bool, str]:
        """レベルを変更（階段使用）"""
        return self.navigation_manager.change_level(target_level)
    
    def get_current_cell(self) -> Optional[DungeonCell]:
        """現在位置のセルを取得"""
        return self.navigation_manager.get_current_cell()
    
    def get_visible_cells(self, vision_range: int = 1) -> List[Tuple[int, int, DungeonCell]]:
        """視界内のセルを取得"""
        return self.navigation_manager.get_visible_cells(vision_range)
    
    # インタラクション系メソッド
    def set_force_retreat_callback(self, callback):
        """強制撤退コールバックを設定"""
        self.interaction_manager.set_force_retreat_callback(callback)
    
    def interact_with_current_cell(self, party: Party, character = None) -> Dict[str, Any]:
        """現在位置のセルとのインタラクション"""
        return self.interaction_manager.interact_with_current_cell(party, character)
    
    def check_for_secret_interactions(self, party: Party) -> Dict[str, Any]:
        """隠された要素との相互作用をチェック"""
        return self.interaction_manager.check_for_secret_interactions(party)
    
    def complete_boss_encounter(self, encounter_id: str, victory: bool, party: Party) -> Dict[str, Any]:
        """ボス戦完了処理"""
        return self.interaction_manager.complete_boss_encounter(encounter_id, victory, party)
    
    def check_party_status(self, party) -> Dict[str, Any]:
        """パーティ状態をチェック"""
        return self.interaction_manager.check_party_status(party)
    
    def should_force_retreat(self, party) -> Tuple[bool, str]:
        """強制的な撤退が必要かチェック"""
        return self.interaction_manager.should_force_retreat(party)
    
    def handle_member_death(self, party, dead_character_name: str):
        """メンバー死亡時の処理"""
        self.interaction_manager.handle_member_death(party, dead_character_name)
    
    # === 便利プロパティ ===
    
    @property
    def current_dungeon(self) -> Optional[DungeonState]:
        """現在のダンジョン状態を取得"""
        return self.state_manager.get_current_dungeon()
    
    # === クリーンアップ ===
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        try:
            self.state_manager.cleanup()
            logger.info("DungeonManager（リファクタリング版） リソースをクリーンアップしました")
        except Exception as e:
            logger.error(f"DungeonManager クリーンアップ中にエラー: {e}")


# 既存コードとの互換性のためのグローバルインスタンス
dungeon_manager = DungeonManager()