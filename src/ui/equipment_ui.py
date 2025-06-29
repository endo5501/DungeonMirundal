"""装備UI管理システム（WindowSystem統合版）"""

from typing import Dict, List, Optional, Any, Tuple, Callable
from enum import Enum

from src.ui.window_system import WindowManager
from src.ui.window_system.equipment_window import EquipmentWindow
from src.equipment.equipment import Equipment, EquipmentSlot, EquipmentBonus, equipment_manager
from src.items.item import Item, ItemInstance, item_manager
from src.character.party import Party
from src.character.character import Character
from src.core.config_manager import config_manager
from src.utils.logger import logger


class EquipmentUIMode(Enum):
    """装備UI表示モード"""
    OVERVIEW = "overview"           # 装備概要
    SLOT_DETAIL = "slot_detail"     # スロット詳細
    ITEM_SELECTION = "item_selection"  # アイテム選択
    COMPARISON = "comparison"       # 装備比較


class EquipmentUI:
    """装備UI管理クラス（WindowSystem統合版）"""
    
    def __init__(self):
        # WindowSystem統合
        self.window_manager = WindowManager.get_instance()
        self.equipment_window: Optional[EquipmentWindow] = None
        
        # 状態管理
        self.current_party: Optional[Party] = None
        self.current_character: Optional[Character] = None
        self.current_equipment: Optional[Equipment] = None
        self.current_mode = EquipmentUIMode.OVERVIEW
        self.selected_slot: Optional[EquipmentSlot] = None
        self.comparison_item: Optional[ItemInstance] = None
        
        # UI状態
        self.is_open = False
        self.callback_on_close: Optional[Callable] = None
        
        logger.info(config_manager.get_text("equipment_ui.initialized"))
    
    def _get_equipment_window(self) -> EquipmentWindow:
        """EquipmentWindowインスタンスを取得または作成"""
        if self.equipment_window is None:
            equipment_config = self._create_equipment_window_config()
            
            self.equipment_window = EquipmentWindow(
                window_id="equipment_main",
                equipment_config=equipment_config
            )
        return self.equipment_window
    
    def _create_equipment_window_config(self) -> Dict[str, Any]:
        """EquipmentWindow用設定を作成"""
        return {
            'character': self.current_character,
            'equipment_slots': self._get_available_equipment_slots(),
            'inventory': self.current_character.get_inventory() if self.current_character else None,
            'show_comparison': True,
            'show_stats': True,
            'enable_drag_drop': True,
            'enable_quick_actions': True,
            'auto_save': True
        }
    
    def _get_available_equipment_slots(self) -> List[EquipmentSlot]:
        """利用可能な装備スロットを取得"""
        return list(EquipmentSlot)
    
    def set_party(self, party: Party):
        """パーティを設定"""
        self.current_party = party
        logger.debug(config_manager.get_text("equipment_ui.party_set").format(party_name=party.name))
    
    def show_party_equipment_menu(self, party: Party):
        """パーティ装備メニューを表示（WindowSystem版）"""
        try:
            self.set_party(party)
            self.current_mode = EquipmentUIMode.OVERVIEW
            
            # 最初のキャラクターを自動選択（UX向上）
            characters = party.get_all_characters()
            if characters:
                self.current_character = characters[0]
            
            equipment_window = self._get_equipment_window()
            equipment_window.create()
            equipment_window.show_party_overview()
            
            self.is_open = True
            logger.info(config_manager.get_text("equipment_ui.party_equipment_menu_displayed"))
            return True
        except Exception as e:
            logger.error(f"パーティ装備メニュー表示エラー: {e}")
            return False
    
    def show_character_equipment(self, character: Character):
        """キャラクター装備画面を表示（WindowSystem版）"""
        try:
            self.current_character = character
            self.current_equipment = character.get_equipment()
            
            equipment_window = self._get_equipment_window()
            
            # 設定を更新
            equipment_config = self._create_equipment_window_config()
            equipment_window.update_config(equipment_config)
            
            equipment_window.show_character_equipment(character)
            
            logger.info(f"キャラクター装備を表示: {character.name}")
            return True
        except Exception as e:
            logger.error(f"キャラクター装備表示エラー: {e}")
            return False
    
    def select_equipment_slot(self, slot: EquipmentSlot):
        """装備スロット選択（EquipmentWindowに委譲）"""
        if self.equipment_window:
            try:
                return self.equipment_window.select_equipment_slot(slot)
            except Exception as e:
                logger.error(f"装備スロット選択エラー: {e}")
                return False
        return False
    
    def show_equipment_comparison(self, current_item: ItemInstance, new_item: ItemInstance):
        """装備比較を表示（WindowSystem版）"""
        try:
            self.comparison_item = new_item
            self.current_mode = EquipmentUIMode.COMPARISON
            
            equipment_window = self._get_equipment_window()
            equipment_window.show_equipment_comparison(current_item, new_item)
            
            logger.info("装備比較を表示")
            return True
        except Exception as e:
            logger.error(f"装備比較表示エラー: {e}")
            return False
    
    def equip_item(self, item_instance: ItemInstance, slot: EquipmentSlot):
        """アイテムを装備（WindowSystem版）"""
        try:
            if not self.current_character or not self.current_equipment:
                logger.warning("キャラクターまたは装備が設定されていません")
                return False
            
            # バリデーション
            can_equip, reason = self.validate_equipment(item_instance, slot)
            if not can_equip:
                logger.warning(f"装備不可: {reason}")
                return False
            
            # 装備実行
            success = self.current_equipment.equip_item(item_instance, slot)
            
            if success:
                # EquipmentWindowに変更通知
                if self.equipment_window:
                    self.equipment_window.refresh_equipment_display()
                
                logger.info(f"アイテムを装備: {item_instance.item_id} -> {slot.value}")
                return True
            else:
                logger.warning("装備処理に失敗しました")
                return False
                
        except Exception as e:
            logger.error(f"アイテム装備エラー: {e}")
            return False
    
    def unequip_item(self, slot: EquipmentSlot):
        """アイテムを外す（WindowSystem版）"""
        try:
            if not self.current_character or not self.current_equipment:
                logger.warning("キャラクターまたは装備が設定されていません")
                return False
            
            # 装備解除実行
            success = self.current_equipment.unequip_item(slot)
            
            if success:
                # EquipmentWindowに変更通知
                if self.equipment_window:
                    self.equipment_window.refresh_equipment_display()
                
                logger.info(f"アイテムを外しました: {slot.value}")
                return True
            else:
                logger.warning("装備解除処理に失敗しました")
                return False
                
        except Exception as e:
            logger.error(f"アイテム装備解除エラー: {e}")
            return False
    
    def validate_equipment(self, item_instance: ItemInstance, slot: EquipmentSlot):
        """装備バリデーション（EquipmentWindowに委譲）"""
        if self.equipment_window:
            try:
                return self.equipment_window.validate_equipment(item_instance, slot)
            except Exception as e:
                logger.error(f"装備バリデーションエラー: {e}")
                return False, str(e)
        
        # フォールバック（基本バリデーション）
        if not self.current_character or not self.current_equipment:
            return False, "キャラクターまたは装備が設定されていません"
        
        try:
            can_equip, reason = self.current_equipment.can_equip_item(
                item_instance, slot, self.current_character.character_class.value
            )
            return can_equip, reason
        except Exception as e:
            return False, str(e)
    
    def show_equipment_effects(self):
        """装備効果確認を表示（WindowSystem版）"""
        try:
            equipment_window = self._get_equipment_window()
            equipment_window.show_equipment_effects()
            
            logger.info("装備効果確認を表示")
            return True
        except Exception as e:
            logger.error(f"装備効果確認表示エラー: {e}")
            return False
    
    def show_equipment_bonus(self):
        """装備ボーナス詳細を表示（WindowSystem版）"""
        try:
            equipment_window = self._get_equipment_window()
            equipment_window.show_equipment_bonus()
            
            logger.info("装備ボーナス詳細を表示")
            return True
        except Exception as e:
            logger.error(f"装備ボーナス詳細表示エラー: {e}")
            return False
    
    def close_equipment_ui(self):
        """装備UIを閉じる（WindowSystem版）"""
        try:
            if self.equipment_window:
                self.equipment_window.close()
            
            self.is_open = False
            self.current_mode = EquipmentUIMode.OVERVIEW
            
            if self.callback_on_close:
                self.callback_on_close()
            
            logger.info("装備UIを閉じました")
        except Exception as e:
            logger.error(f"装備UI終了エラー: {e}")
    
    def set_callback_on_close(self, callback: Callable):
        """クローズ時コールバックを設定"""
        self.callback_on_close = callback
    
    def cleanup(self):
        """リソースクリーンアップ"""
        try:
            if self.equipment_window:
                if hasattr(self.equipment_window, 'cleanup'):
                    self.equipment_window.cleanup()
                self.equipment_window = None
            
            self.is_open = False
            self.current_party = None
            self.current_character = None
            self.current_equipment = None
            
            logger.info("EquipmentUI（WindowSystem版）リソースをクリーンアップしました")
        except Exception as e:
            logger.error(f"クリーンアップエラー: {e}")
    
    # 内部ヘルパーメソッド（レガシー互換性のため）
    def _get_slot_name(self, slot: EquipmentSlot) -> str:
        """スロット名を取得（レガシー互換性）"""
        slot_names = {
            EquipmentSlot.WEAPON: "武器",
            EquipmentSlot.SHIELD: "盾",
            EquipmentSlot.ARMOR: "鎧",
            EquipmentSlot.HELMET: "兜",
            EquipmentSlot.GLOVES: "手袋",
            EquipmentSlot.BOOTS: "靴",
            EquipmentSlot.ACCESSORY1: "アクセサリ1",
            EquipmentSlot.ACCESSORY2: "アクセサリ2"
        }
        return slot_names.get(slot, "不明なスロット")
    
    def _can_equip_in_slot(self, item: Item, slot: EquipmentSlot) -> bool:
        """スロットに装備可能かチェック（レガシー互換性）"""
        # 基本的なタイプチェック（実際の実装では詳細な条件）
        return True  # 簡略化


# グローバルインスタンス（互換性のため）
equipment_ui = EquipmentUI()

def create_equipment_ui() -> EquipmentUI:
    """装備UI作成"""
    return EquipmentUI()