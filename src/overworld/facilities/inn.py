"""宿屋（リファクタリング版）"""

import pygame
from typing import Dict, List, Optional, Any
from src.overworld.base_facility import BaseFacility, FacilityType
from src.character.party import Party
from src.ui.base_ui_pygame import UIMenu, UIDialog, UIInputDialog, ui_manager
from src.ui.selection_list_ui import ItemSelectionList, CustomSelectionList, SelectionListData
from src.core.config_manager import config_manager
from src.utils.logger import logger
from src.inventory.inventory import Inventory, InventoryManager
from src.equipment.equipment import Equipment, EquipmentManager
from src.magic.spells import SpellManager
from src.items.item import item_manager


class Inn(BaseFacility):
    """宿屋（リファクタリング版）
    
    新メニューシステムのみをサポートし、機能を分離・整理
    """
    
    def __init__(self):
        super().__init__(
            facility_id="inn",
            facility_type=FacilityType.INN,
            name_key="facility.inn"
        )
        
        # UI要素
        self.storage_view_list: Optional[ItemSelectionList] = None
    
    def _setup_menu_items(self, menu: UIMenu):
        """宿屋固有のメニュー項目を設定"""
        menu.add_menu_item("冒険の準備", self._show_adventure_preparation)
        menu.add_menu_item("アイテム預かり", self._show_item_organization)
        menu.add_menu_item("宿屋の主人と話す", self._talk_to_innkeeper)
        menu.add_menu_item("旅の情報を聞く", self._show_travel_info)
        menu.add_menu_item("酒場の噂話", self._show_tavern_rumors)
        menu.add_menu_item("パーティ名を変更", self._change_party_name)
    
    def _on_enter(self):
        """宿屋入場時の処理"""
        logger.info("宿屋に入りました")
    
    def _on_exit(self):
        """宿屋退場時の処理"""
        self._cleanup_all_ui()
        logger.info("宿屋から出ました")
    
    def _cleanup_all_ui(self):
        """全てのUI要素をクリーンアップ"""
        self._hide_storage_view_list()
    
    def _get_additional_menu_ids(self) -> List[str]:
        """旧システム用：宿屋で使用される追加のメニューIDリストを返す"""
        return [
            "adventure_prep_menu",
            "new_item_mgmt_menu", 
            "character_item_menu",
            "spell_mgmt_menu",
            "prayer_mgmt_menu",
            "character_spell_menu",
            "character_prayer_menu",
            "party_equipment_menu"
        ]
    
    def _handle_ui_selection_events(self, event: pygame.event.Event) -> bool:
        """UISelectionListのイベント処理をオーバーライド"""
        if self.storage_view_list and self.storage_view_list.handle_event(event):
            return True
        return False
    
    # === 情報表示メソッド ===
    
    def _talk_to_innkeeper(self):
        """宿屋の主人との会話"""
        messages = [
            (config_manager.get_text("inn.innkeeper.conversation.adventure_title"),
             config_manager.get_text("inn.innkeeper.conversation.adventure_message")),
            (config_manager.get_text("inn.innkeeper.conversation.town_title"),
             config_manager.get_text("inn.innkeeper.conversation.town_message")),
            (config_manager.get_text("inn.innkeeper.conversation.history_title"),
             config_manager.get_text("inn.innkeeper.conversation.history_message"))
        ]
        
        import random
        title, message = random.choice(messages)
        
        self.show_information_dialog(
            f"{config_manager.get_text('inn.innkeeper.title')} - {title}",
            message
        )
    
    def _show_travel_info(self):
        """旅の情報を表示"""
        travel_info = config_manager.get_text("inn.travel_info.content")
        self.show_information_dialog(
            config_manager.get_text("inn.travel_info.title"),
            travel_info
        )
    
    def _show_tavern_rumors(self):
        """酒場の噂話を表示"""
        rumors = [
            (config_manager.get_text("inn.rumors.dungeon_title"),
             config_manager.get_text("inn.rumors.dungeon_message")),
            (config_manager.get_text("inn.rumors.monster_title"),
             config_manager.get_text("inn.rumors.monster_message")),
            (config_manager.get_text("inn.rumors.legendary_title"),
             config_manager.get_text("inn.rumors.legendary_message")),
            (config_manager.get_text("inn.rumors.adventurer_title"),
             config_manager.get_text("inn.rumors.adventurer_message")),
            (config_manager.get_text("inn.rumors.merchant_title"),
             config_manager.get_text("inn.rumors.merchant_message"))
        ]
        
        import random
        title, rumor = random.choice(rumors)
        
        self.show_information_dialog(
            f"{config_manager.get_text('inn.rumors.title')} - {title}",
            rumor
        )
    
    # === パーティ管理 ===
    
    def _change_party_name(self):
        """パーティ名変更機能"""
        if not self.current_party:
            self.show_error_dialog("エラー", "パーティが設定されていません")
            return
        
        current_name = self.current_party.name if self.current_party.name else "無名のパーティ"
        
        name_input_dialog = UIInputDialog(
            "party_name_input_dialog",
            config_manager.get_text("inn.party_name.title"),
            f"現在の名前: {current_name}\n\n新しいパーティ名を入力してください:",
            initial_text=current_name,
            placeholder=config_manager.get_text("inn.party_name.placeholder"),
            on_confirm=self._on_party_name_confirmed,
            on_cancel=self._on_party_name_cancelled
        )
        
        ui_manager.add_dialog(name_input_dialog)
        ui_manager.show_dialog(name_input_dialog.dialog_id)
    
    def _on_party_name_confirmed(self, new_name: str):
        """パーティ名変更確認時の処理"""
        validated_name = self._validate_party_name(new_name)
        
        if not validated_name:
            self.show_error_dialog("無効な名前", "入力された名前は無効です")
            return
        
        old_name = self.current_party.name
        self.current_party.name = validated_name
        
        ui_manager.hide_menu("party_name_input_dialog")
        
        success_message = f"パーティ名を「{old_name}」から「{validated_name}」に変更しました。"
        self.show_success_dialog("名前変更完了", success_message)
        
        logger.info(f"パーティ名を変更: {old_name} → {validated_name}")
    
    def _on_party_name_cancelled(self):
        """パーティ名変更キャンセル時の処理"""
        ui_manager.hide_menu("party_name_input_dialog")
        logger.info("パーティ名変更がキャンセルされました")
    
    def _validate_party_name(self, name: str) -> str:
        """パーティ名のバリデーションと正規化"""
        if not name or not name.strip():
            return config_manager.get_text("inn.party_name.default_name")
        
        name = name.strip()
        
        if len(name) > 30:
            name = name[:30]
        
        # より厳密なサニタイズ：HTMLタグとスクリプト要素を完全に除去
        import re
        # HTMLタグを除去
        name = re.sub(r'<[^>]*>', '', name)
        # JavaScriptの危険なキーワードを除去
        dangerous_patterns = [
            r'script', r'alert', r'document', r'window', r'eval',
            r'function', r'javascript:', r'onclick', r'onload'
        ]
        for pattern in dangerous_patterns:
            name = re.sub(pattern, '', name, flags=re.IGNORECASE)
        
        # 制御文字を除去
        dangerous_chars = ['\n', '\r', '\t', '\0']
        for char in dangerous_chars:
            name = name.replace(char, '')
        
        name = name.strip()
        if not name:
            return config_manager.get_text("inn.party_name.default_name")
        
        return name
    
    # === 冒険準備メニュー ===
    
    def _show_adventure_preparation(self):
        """冒険の準備メニューを表示"""
        if not self.current_party:
            self.show_error_dialog("エラー", "パーティが設定されていません")
            return
        
        prep_menu = UIMenu("adventure_prep_menu", "冒険の準備")
        
        prep_menu.add_menu_item("アイテム整理", self._show_item_organization)
        prep_menu.add_menu_item("魔術スロット設定", self._show_spell_slot_management)
        prep_menu.add_menu_item("祈祷スロット設定", self._show_prayer_slot_management)
        prep_menu.add_menu_item("パーティ装備確認", self._show_party_equipment_status)
        prep_menu.add_menu_item(config_manager.get_text("menu.back"), self.back_to_previous_menu)
        
        self.show_submenu(prep_menu, {'menu_type': 'adventure_prep'})
    
    # === アイテム管理 ===
    
    def _show_item_organization(self):
        """アイテム整理画面を表示"""
        if not self.current_party:
            return
        
        try:
            from src.overworld.inn_storage import inn_storage_manager
            
            # パーティインベントリから宿屋倉庫への移行（初回のみ）
            party_inventory = self.current_party.get_party_inventory()
            if party_inventory:
                party_items_count = sum(1 for slot in party_inventory.slots if not slot.is_empty())
                if party_items_count > 0:
                    transferred = inn_storage_manager.transfer_from_party_inventory(self.current_party)
                    if transferred > 0:
                        self.show_information_dialog(
                            "アイテム移行完了",
                            f"パーティインベントリから宿屋倉庫に{transferred}個のアイテムを移動しました。\n\n"
                            "今後、購入したアイテムは直接宿屋倉庫に搬入されます。"
                        )
            
            self._show_new_item_organization_menu()
            
        except Exception as e:
            logger.error(f"アイテム整理画面表示エラー: {e}")
            self.show_error_dialog("エラー", "アイテム整理画面の表示に失敗しました")
    
    def _show_new_item_organization_menu(self):
        """新しいアイテム整理メニューを表示"""
        item_mgmt_menu = UIMenu("new_item_mgmt_menu", "アイテム整理")
        
        # キャラクター一覧を追加
        for character in self.current_party.get_all_characters():
            item_mgmt_menu.add_menu_item(
                f"{character.name}のアイテム",
                self._show_character_item_management,
                [character]
            )
        
        item_mgmt_menu.add_menu_item("宿屋倉庫の状況", self._show_inn_storage_status)
        item_mgmt_menu.add_menu_item(config_manager.get_text("menu.back"), self.back_to_previous_menu)
        
        self.show_submenu(item_mgmt_menu)
    
    def _show_inn_storage_status(self):
        """宿屋倉庫の状況を表示"""
        try:
            from src.overworld.inn_storage import inn_storage_manager
            
            storage = inn_storage_manager.get_storage()
            summary = inn_storage_manager.get_storage_summary()
            
            status_text = f"宿屋倉庫の状況\n\n"
            status_text += f"使用中: {summary['used_slots']}/{summary['capacity']} スロット\n"
            status_text += f"空きスロット: {summary['free_slots']}\n"
            status_text += f"使用率: {summary['usage_percentage']:.1f}%\n\n"
            
            if summary['used_slots'] > 0:
                status_text += "保管中のアイテム:\n"
                items = storage.get_all_items()
                for i, (slot_index, item_instance) in enumerate(items[:10]):  # 最初の10個まで表示
                    item = item_manager.get_item(item_instance.item_id)
                    if item:
                        quantity_text = f" x{item_instance.quantity}" if item_instance.quantity > 1 else ""
                        status_text += f"• {item.get_name()}{quantity_text}\n"
                
                if len(items) > 10:
                    status_text += f"... 他{len(items) - 10}個\n"
            else:
                status_text += "倉庫は空です。"
            
            self.show_information_dialog("宿屋倉庫の状況", status_text, buttons=[{"text": "戻る", "callback": None}])
            
        except Exception as e:
            logger.error(f"倉庫状況表示エラー: {e}")
            self.show_error_dialog("エラー", "倉庫状況の表示に失敗しました")
    
    def _show_character_item_management(self, character):
        """キャラクターアイテム管理メニューを表示"""
        char_menu = UIMenu("character_item_menu", f"{character.name} - アイテム管理")
        
        char_menu.add_menu_item("倉庫→キャラクター", self._show_storage_to_character_transfer, [character])
        char_menu.add_menu_item("キャラクター→倉庫", self._show_character_to_storage_transfer, [character])
        char_menu.add_menu_item("アイテム使用", self._show_character_item_usage, [character])
        char_menu.add_menu_item("詳細表示", self._show_character_item_detail, [character])
        char_menu.add_menu_item(config_manager.get_text("menu.back"), self.back_to_previous_menu)
        
        self.show_submenu(char_menu, {'character': character})
    
    # === 魔法管理 ===
    
    def _show_spell_slot_management(self):
        """魔術スロット設定メニューを表示"""
        if not self.current_party:
            return
        
        spell_menu = UIMenu("spell_mgmt_menu", "魔術スロット設定")
        
        for character in self.current_party.get_all_characters():
            spell_menu.add_menu_item(
                f"{character.name}の魔術",
                self._show_character_spell_management,
                [character]
            )
        
        spell_menu.add_menu_item(config_manager.get_text("menu.back"), self.back_to_previous_menu)
        self.show_submenu(spell_menu)
    
    def _show_prayer_slot_management(self):
        """祈祷スロット設定メニューを表示"""
        if not self.current_party:
            return
        
        prayer_menu = UIMenu("prayer_mgmt_menu", "祈祷スロット設定")
        
        for character in self.current_party.get_all_characters():
            prayer_menu.add_menu_item(
                f"{character.name}の祈祷",
                self._show_character_prayer_management,
                [character]
            )
        
        prayer_menu.add_menu_item(config_manager.get_text("menu.back"), self.back_to_previous_menu)
        self.show_submenu(prayer_menu)
    
    def _show_character_spell_management(self, character):
        """キャラクター魔術管理メニューを表示"""
        spell_menu = UIMenu("character_spell_menu", f"{character.name} - 魔術管理")
        
        spell_menu.add_menu_item("魔術装備", self._show_spell_equip_menu, [character])
        spell_menu.add_menu_item("現在の状況", self._show_spell_status, [character])
        spell_menu.add_menu_item(config_manager.get_text("menu.back"), self.back_to_previous_menu)
        
        self.show_submenu(spell_menu, {'character': character})
    
    def _show_character_prayer_management(self, character):
        """キャラクター祈祷管理メニューを表示"""
        prayer_menu = UIMenu("character_prayer_menu", f"{character.name} - 祈祷管理")
        
        prayer_menu.add_menu_item("祈祷装備", self._show_prayer_equip_menu, [character])
        prayer_menu.add_menu_item("現在の状況", self._show_prayer_status, [character])
        prayer_menu.add_menu_item(config_manager.get_text("menu.back"), self.back_to_previous_menu)
        
        self.show_submenu(prayer_menu, {'character': character})
    
    # === 装備管理 ===
    
    def _show_party_equipment_status(self):
        """パーティ装備確認を表示"""
        if not self.current_party:
            return
        
        equipment_menu = UIMenu("party_equipment_menu", "パーティ装備確認")
        
        for character in self.current_party.get_all_characters():
            equipment_menu.add_menu_item(
                f"{character.name}の装備",
                self._show_character_equipment_status,
                [character]
            )
        
        equipment_menu.add_menu_item(config_manager.get_text("menu.back"), self.back_to_previous_menu)
        self.show_submenu(equipment_menu)
    
    def _show_character_equipment_status(self, character):
        """キャラクター装備状況を表示"""
        equipment = character.get_equipment()
        status_text = f"{character.name}の装備状況\n\n"
        
        # 装備品の詳細表示
        weapon = equipment.get_equipped_weapon()
        armor = equipment.get_equipped_armor()
        
        status_text += f"武器: {weapon.get_name() if weapon else '装備なし'}\n"
        status_text += f"防具: {armor.get_name() if armor else '装備なし'}\n"
        
        self.show_information_dialog(f"{character.name}の装備", status_text)
    
    # === UIヘルパー ===
    
    def _hide_storage_view_list(self):
        """倉庫表示リストを非表示"""
        if self.storage_view_list:
            self.storage_view_list.hide()
            self.storage_view_list = None
    
    # === スタブメソッド（実装予定機能） ===
    
    def _show_storage_to_character_transfer(self, character):
        """倉庫からキャラクターへの転送（実装予定）"""
        self.show_information_dialog("実装予定", "この機能は実装予定です")
    
    def _show_character_to_storage_transfer(self, character):
        """キャラクターから倉庫への転送（実装予定）"""
        self.show_information_dialog("実装予定", "この機能は実装予定です")
    
    def _show_character_item_usage(self, character):
        """キャラクターアイテム使用（実装予定）"""
        self.show_information_dialog("実装予定", "この機能は実装予定です")
    
    def _show_character_item_detail(self, character):
        """キャラクターアイテム詳細（実装予定）"""
        self.show_information_dialog("実装予定", "この機能は実装予定です")
    
    def _show_spell_equip_menu(self, character):
        """魔術装備メニュー（実装予定）"""
        self.show_information_dialog("実装予定", "この機能は実装予定です")
    
    def _show_spell_status(self, character):
        """魔術状況表示（実装予定）"""
        self.show_information_dialog("実装予定", "この機能は実装予定です")
    
    def _show_prayer_equip_menu(self, character):
        """祈祷装備メニュー（実装予定）"""
        self.show_information_dialog("実装予定", "この機能は実装予定です")
    
    def _show_prayer_status(self, character):
        """祈祷状況表示（実装予定）"""
        self.show_information_dialog("実装予定", "この機能は実装予定です")