"""インベントリUI管理システム（WindowSystem統合版）"""

from typing import Dict, List, Optional, Any, Tuple, Callable
from enum import Enum

from src.ui.window_system import WindowManager
from src.ui.window_system.inventory_window import InventoryWindow
from src.inventory.inventory import Inventory, InventorySlot, InventorySlotType, inventory_manager
from src.items.item import Item, ItemInstance, item_manager
from src.items.item_usage import item_usage_manager, UsageResult
from src.character.party import Party
from src.character.character import Character
from src.core.config_manager import config_manager
from src.utils.logger import logger


class InventoryAction(Enum):
    """インベントリアクション"""
    VIEW = "view"           # 表示
    USE = "use"             # 使用
    TRANSFER = "transfer"   # 移動
    DROP = "drop"           # 破棄
    SORT = "sort"           # 整理


class InventoryUI:
    """インベントリUI管理クラス（WindowSystem統合版）"""
    
    def __init__(self):
        # WindowSystem統合
        self.window_manager = WindowManager.get_instance()
        self.inventory_window: Optional[InventoryWindow] = None
        
        # 状態管理
        self.current_party: Optional[Party] = None
        self.current_inventory: Optional[Inventory] = None
        self.current_character: Optional[Character] = None
        self.selected_slot: Optional[int] = None
        self.transfer_source: Optional[Tuple[Inventory, int]] = None
        
        logger.info(config_manager.get_text("inventory_ui.initialized"))
    
    def _get_inventory_window(self) -> InventoryWindow:
        """InventoryWindowインスタンスを取得または作成"""
        if self.inventory_window is None:
            inventory_config = self._create_inventory_window_config("party")
            
            self.inventory_window = InventoryWindow(
                window_id="inventory_main",
                inventory_config=inventory_config
            )
        return self.inventory_window
    
    def _create_inventory_window_config(self, inventory_type: str) -> Dict[str, Any]:
        """InventoryWindow用設定を作成"""
        return {
            'inventory_type': inventory_type,
            'inventory': self.current_inventory,
            'character': self.current_character,
            'party': self.current_party,
            'show_filters': True,
            'show_categories': True,
            'enable_drag_drop': True,
            'enable_quick_actions': True,
            'auto_sort': False,
            'grid_view': True,
            'show_weight': True,
            'show_value': True
        }
    
    def set_party(self, party: Party):
        """パーティを設定"""
        self.current_party = party
        logger.debug(config_manager.get_text("inventory_ui.party_set").format(party_name=party.name))
    
    def show_party_inventory_menu(self, party: Party):
        """パーティインベントリメニューを表示（WindowSystem版）"""
        try:
            self.set_party(party)
            
            # パーティ共有インベントリをデフォルトで表示
            party_inventory = party.get_party_inventory()
            self.current_inventory = party_inventory
            
            inventory_window = self._get_inventory_window()
            inventory_window.create()
            inventory_window.show_party_inventory()
            
            logger.info(config_manager.get_text("inventory_ui.party_inventory_menu_displayed"))
            return True
        except Exception as e:
            logger.error(f"パーティインベントリメニュー表示エラー: {e}")
            return False
    
    def show_character_inventory(self, character: Character):
        """キャラクターインベントリを表示（WindowSystem版）"""
        try:
            self.current_character = character
            character_inventory = character.get_inventory()
            self.current_inventory = character_inventory
            
            inventory_window = self._get_inventory_window()
            
            # 設定を更新
            inventory_config = self._create_inventory_window_config("character")
            inventory_window.update_config(inventory_config)
            
            inventory_window.show_character_inventory(character)
            
            logger.info(f"キャラクターインベントリを表示: {character.name}")
            return True
        except Exception as e:
            logger.error(f"キャラクターインベントリ表示エラー: {e}")
            return False
    
    def show_party_shared_inventory(self):
        """パーティ共有インベントリを表示（WindowSystem版）"""
        try:
            if not self.current_party:
                logger.warning("パーティが設定されていません")
                return False
            
            party_inventory = self.current_party.get_party_inventory()
            self.current_inventory = party_inventory
            
            inventory_window = self._get_inventory_window()
            
            # 設定を更新
            inventory_config = self._create_inventory_window_config("party")
            inventory_window.update_config(inventory_config)
            
            inventory_window.show_party_inventory()
            
            logger.info("パーティ共有インベントリを表示")
            return True
        except Exception as e:
            logger.error(f"パーティ共有インベントリ表示エラー: {e}")
            return False
    
    def use_item(self, item_instance: ItemInstance, character: Character):
        """アイテムを使用（WindowSystem版）"""
        try:
            if self.inventory_window:
                return self.inventory_window.use_item(item_instance, character)
            
            # フォールバック（直接処理）
            usage_result = item_usage_manager.use_item(item_instance, character)
            
            if usage_result.success:
                logger.info(f"アイテムを使用: {item_instance.item_id} -> {character.name}")
                return True
            else:
                logger.warning(f"アイテム使用失敗: {usage_result.message}")
                return False
                
        except Exception as e:
            logger.error(f"アイテム使用エラー: {e}")
            return False
    
    def transfer_item(self, item_instance: ItemInstance, source_inventory: Inventory, target_inventory: Inventory):
        """アイテム転送（WindowSystem版）"""
        try:
            if self.inventory_window:
                return self.inventory_window.transfer_item(item_instance, source_inventory, target_inventory)
            
            # フォールバック（直接処理）
            # 元のインベントリからアイテムを削除
            source_removed = source_inventory.remove_item(item_instance)
            if not source_removed:
                logger.warning("ソースインベントリからのアイテム削除に失敗")
                return False
            
            # ターゲットインベントリに追加
            target_added = target_inventory.add_item(item_instance)
            if not target_added:
                # 失敗した場合は元に戻す
                source_inventory.add_item(item_instance)
                logger.warning("ターゲットインベントリへのアイテム追加に失敗")
                return False
            
            logger.info(f"アイテム転送完了: {item_instance.item_id}")
            return True
            
        except Exception as e:
            logger.error(f"アイテム転送エラー: {e}")
            return False
    
    def drop_item(self, item_instance: ItemInstance, inventory: Inventory):
        """アイテム破棄（WindowSystem版）"""
        try:
            if self.inventory_window:
                return self.inventory_window.drop_item(item_instance)
            
            # フォールバック（直接処理）
            success = inventory.remove_item(item_instance)
            
            if success:
                logger.info(f"アイテムを破棄: {item_instance.item_id}")
                return True
            else:
                logger.warning("アイテム破棄に失敗")
                return False
                
        except Exception as e:
            logger.error(f"アイテム破棄エラー: {e}")
            return False
    
    def sort_inventory(self, inventory: Inventory):
        """インベントリ整理（WindowSystem版）"""
        try:
            if self.inventory_window:
                return self.inventory_window.sort_inventory()
            
            # フォールバック（基本ソート）
            inventory.sort_items()
            
            logger.info("インベントリを整理しました")
            return True
            
        except Exception as e:
            logger.error(f"インベントリ整理エラー: {e}")
            return False
    
    def show_item_details(self, item_instance: ItemInstance):
        """アイテム詳細を表示（WindowSystem版）"""
        try:
            inventory_window = self._get_inventory_window()
            inventory_window.show_item_details(item_instance)
            
            logger.info(f"アイテム詳細を表示: {item_instance.item_id}")
            return True
        except Exception as e:
            logger.error(f"アイテム詳細表示エラー: {e}")
            return False
    
    def show_inventory_management_menu(self):
        """インベントリ管理メニューを表示（WindowSystem版）"""
        try:
            inventory_window = self._get_inventory_window()
            inventory_window.show_management_menu()
            
            logger.info("インベントリ管理メニューを表示")
            return True
        except Exception as e:
            logger.error(f"インベントリ管理メニュー表示エラー: {e}")
            return False
    
    def show_inventory_stats(self):
        """インベントリ統計を表示（WindowSystem版）"""
        try:
            inventory_window = self._get_inventory_window()
            inventory_window.show_inventory_stats()
            
            logger.info("インベントリ統計を表示")
            return True
        except Exception as e:
            logger.error(f"インベントリ統計表示エラー: {e}")
            return False
    
    def filter_items_by_category(self, category: str):
        """カテゴリでアイテムをフィルタ（WindowSystem版）"""
        try:
            inventory_window = self._get_inventory_window()
            inventory_window.apply_filter(category)
            
            logger.info(f"アイテムフィルタを適用: {category}")
            return True
        except Exception as e:
            logger.error(f"アイテムフィルタエラー: {e}")
            return False
    
    def close_inventory_ui(self):
        """インベントリUIを閉じる（WindowSystem版）"""
        try:
            if self.inventory_window:
                self.inventory_window.close()
            
            # 状態リセット
            self.selected_slot = None
            self.transfer_source = None
            
            logger.info("インベントリUIを閉じました")
        except Exception as e:
            logger.error(f"インベントリUI終了エラー: {e}")
    
    def cleanup(self):
        """リソースクリーンアップ"""
        try:
            if self.inventory_window:
                if hasattr(self.inventory_window, 'cleanup'):
                    self.inventory_window.cleanup()
                self.inventory_window = None
            
            # 状態クリア
            self.current_party = None
            self.current_inventory = None
            self.current_character = None
            self.selected_slot = None
            self.transfer_source = None
            
            logger.info("InventoryUI（WindowSystem版）リソースをクリーンアップしました")
        except Exception as e:
            logger.error(f"クリーンアップエラー: {e}")
    
    # 内部ヘルパーメソッド（レガシー互換性のため）
    def _show_inventory_contents(self, inventory: Inventory, title: str, inventory_type: str):
        """インベントリ内容を表示（レガシー互換性）"""
        try:
            self.current_inventory = inventory
            
            inventory_config = self._create_inventory_window_config(inventory_type)
            
            inventory_window = self._get_inventory_window()
            inventory_window.update_config(inventory_config)
            inventory_window.show_inventory_contents(title)
            
            logger.info(f"インベントリ内容を表示: {title}")
        except Exception as e:
            logger.error(f"インベントリ内容表示エラー: {e}")


# グローバルインスタンス（互換性のため）
inventory_ui = InventoryUI()

def create_inventory_ui() -> InventoryUI:
    """インベントリUI作成"""
    return InventoryUI()