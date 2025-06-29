"""宿屋（リファクタリング版）"""

import pygame
from typing import Dict, List, Optional, Any
from src.overworld.base_facility import BaseFacility, FacilityType
from src.character.party import Party
from src.ui.window_system import WindowManager
from src.ui.window_system.facility_menu_window import FacilityMenuWindow
from src.ui.window_system.inn_service_window import InnServiceWindow
from src.ui.selection_list_ui import ItemSelectionList, CustomSelectionList, SelectionListData
from src.ui.base_ui_pygame import ui_manager
from src.core.config_manager import config_manager
from src.utils.logger import logger
from src.inventory.inventory import Inventory, InventoryManager
from src.equipment.equipment import Equipment, EquipmentManager
from src.magic.spells import SpellManager
from src.items.item import item_manager
from src.magic.spells import SpellBook, spell_manager


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
    
    def _create_inn_menu_config(self):
        """Inn用のFacilityMenuWindow設定を作成"""
        menu_items = [
            {
                'id': 'adventure_preparation',
                'label': config_manager.get_text("inn_menu.adventure_preparation"),
                'type': 'action',
                'enabled': True
            },
            {
                'id': 'item_storage',
                'label': config_manager.get_text("inn_menu.item_storage"),
                'type': 'action',
                'enabled': True
            },
            {
                'id': 'talk_innkeeper',
                'label': config_manager.get_text("inn_menu.talk_innkeeper"),
                'type': 'action',
                'enabled': True
            },
            {
                'id': 'travel_info',
                'label': config_manager.get_text("inn_menu.travel_info"),
                'type': 'action',
                'enabled': True
            },
            {
                'id': 'tavern_rumors',
                'label': config_manager.get_text("inn_menu.tavern_rumors"),
                'type': 'action',
                'enabled': True
            },
            {
                'id': 'change_party_name',
                'label': config_manager.get_text("inn_menu.change_party_name"),
                'type': 'action',
                'enabled': self.current_party is not None
            },
            {
                'id': 'exit',
                'label': config_manager.get_text("menu.exit"),
                'type': 'exit',
                'enabled': True
            }
        ]
        
        return {
            'facility_type': FacilityType.INN.value,
            'facility_name': config_manager.get_text("facility.inn"),
            'menu_items': menu_items,
            'party': self.current_party,
            'show_party_info': True,
            'show_gold': True
        }
    
    def show_menu(self):
        """Innメインメニューを表示（FacilityMenuWindow使用）"""
        window_manager = WindowManager.get_instance()
        
        # メニュー設定を作成
        menu_config = self._create_inn_menu_config()
        
        # FacilityMenuWindowを作成
        inn_window = FacilityMenuWindow('inn_main_menu', menu_config)
        
        # メッセージハンドラーを設定
        inn_window.message_handler = self.handle_facility_message
        
        # ウィンドウを表示
        window_manager.show_window(inn_window, push_to_stack=True)
        
        logger.info(config_manager.get_text("app_log.entered_inn"))
    
    def handle_facility_message(self, message_type: str, data: dict) -> bool:
        """FacilityMenuWindowからのメッセージを処理"""
        if message_type == 'menu_item_selected':
            item_id = data.get('id')
            
            if item_id == 'adventure_preparation':
                return self._show_adventure_service()
            elif item_id == 'item_storage':
                return self._show_item_service()
            elif item_id == 'talk_innkeeper':
                return self._talk_to_innkeeper()
            elif item_id == 'travel_info':
                return self._show_travel_info()
            elif item_id == 'tavern_rumors':
                return self._show_tavern_rumors()
            elif item_id == 'change_party_name':
                return self._change_party_name()
                
        elif message_type == 'facility_exit_requested':
            return self._handle_exit()
            
        return False
    
    def _handle_exit(self) -> bool:
        """施設退場処理"""
        self._cleanup_all_ui()
        logger.info(config_manager.get_text("app_log.left_inn"))
        
        # WindowManagerでウィンドウを閉じる
        window_manager = WindowManager.get_instance()
        if window_manager.get_active_window():
            window_manager.go_back()
            
        return True
    
    def _on_enter(self):
        """宿屋入場時の処理"""
        logger.info(config_manager.get_text("app_log.entered_inn"))
    
    def _on_exit(self):
        """宿屋退場時の処理"""
        self._cleanup_all_ui()
        logger.info(config_manager.get_text("app_log.left_inn"))
    
    
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
            message,
            buttons=[{"text": "戻る", "callback": None}]
        )
    
    def _show_travel_info(self):
        """旅の情報を表示"""
        travel_info = config_manager.get_text("inn.travel_info.content")
        self.show_information_dialog(
            config_manager.get_text("inn.travel_info.title"),
            travel_info,
            buttons=[{"text": "戻る", "callback": None}]
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
            rumor,
            buttons=[{"text": "戻る", "callback": None}]
        )
    
    # === パーティ管理 ===
    
    def _change_party_name(self):
        """パーティ名変更機能"""
        if not self.current_party:
            self.show_error_dialog(config_manager.get_text("app_log.no_party_error_title"), config_manager.get_text("app_log.no_party_error_message"))
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
            self.show_error_dialog(config_manager.get_text("app_log.invalid_name_error_title"), config_manager.get_text("app_log.invalid_name_error_message"))
            return
        
        old_name = self.current_party.name
        self.current_party.name = validated_name
        
        ui_manager.hide_menu("party_name_input_dialog")
        
        success_message = config_manager.get_text("app_log.name_change_complete_message").format(old_name=old_name, new_name=validated_name)
        self.show_success_dialog(config_manager.get_text("app_log.name_change_complete_title"), success_message)
        
        logger.info(config_manager.get_text("app_log.party_name_changed").format(old_name=old_name, new_name=validated_name))
    
    def _on_party_name_cancelled(self):
        """パーティ名変更キャンセル時の処理"""
        ui_manager.hide_menu("party_name_input_dialog")
        logger.info(config_manager.get_text("app_log.party_name_change_cancelled"))
    
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
    
    def _show_adventure_service(self):
        """冒険サービス統合ウィンドウを表示（InnServiceWindow使用）"""
        if not self.current_party:
            self.show_error_dialog(config_manager.get_text("app_log.no_party_error_title"), config_manager.get_text("app_log.no_party_error_message"))
            return
        
        # InnServiceWindow設定を作成
        inn_config = {
            'parent_facility': self,
            'current_party': self.current_party,
            'service_types': ['adventure_prep', 'item_management', 'magic_management', 'equipment_management'],
            'title': '冒険の準備'
        }
        
        # InnServiceWindowを作成
        adventure_window = InnServiceWindow('inn_adventure_prep', inn_config)
        
        # WindowManagerで表示
        window_manager = WindowManager.get_instance()
        window_manager.show_window(adventure_window, push_to_stack=True)
        
        logger.info("冒険準備サービスウィンドウを表示しました")
    
    def _show_item_service(self):
        """アイテム管理サービスウィンドウを表示（InnServiceWindow使用）"""
        if not self.current_party:
            self.show_error_dialog(config_manager.get_text("app_log.no_party_error_title"), config_manager.get_text("app_log.no_party_error_message"))
            return
        
        # InnServiceWindow設定を作成
        inn_config = {
            'parent_facility': self,
            'current_party': self.current_party,
            'service_types': ['item_management'],
            'title': 'アイテム整理'
        }
        
        # InnServiceWindowを作成
        item_window = InnServiceWindow('inn_item_management', inn_config)
        
        # WindowManagerで表示
        window_manager = WindowManager.get_instance()
        window_manager.show_window(item_window, push_to_stack=True)
        
        logger.info("アイテム管理サービスウィンドウを表示しました")
    
    def _show_adventure_preparation(self):
        """冒険の準備メニューを表示（レガシー - 移行済み）"""
        # UIMenu削除済み: _show_adventure_preparation()は_show_adventure_service()に移行されました
        return self._show_adventure_service()
    
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
            logger.error(config_manager.get_text("app_log.item_organization_error").format(error=e))
            self.show_error_dialog(config_manager.get_text("common.error"), config_manager.get_text("app_log.item_organization_display_failed"))
    
    def _show_new_item_organization_menu(self):
        """新しいアイテム整理メニューを表示（InnServiceWindow使用）"""
        # InnServiceWindow設定を作成
        inn_config = {
            'parent_facility': self,
            'current_party': self.current_party,
            'service_types': ['item_management'],
            'title': 'アイテム整理'
        }
        
        # InnServiceWindowを作成
        item_mgmt_window = InnServiceWindow('inn_item_organization', inn_config)
        
        # WindowManagerで表示
        window_manager = WindowManager.get_instance()
        window_manager.show_window(item_mgmt_window, push_to_stack=True)
        
        logger.info("アイテム整理サービスウィンドウを表示しました")
    
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
            logger.error(config_manager.get_text("app_log.storage_status_display_error").format(error=e))
            self.show_error_dialog(config_manager.get_text("common.error"), config_manager.get_text("app_log.storage_status_display_failed"))
    
    def _show_character_item_management(self, character):
        """キャラクターアイテム管理メニューを表示（InnServiceWindow使用）"""
        # InnServiceWindow設定を作成
        inn_config = {
            'parent_facility': self,
            'current_party': self.current_party,
            'service_types': ['item_management'],
            'selected_character': character,
            'title': f'{character.name} - アイテム管理'
        }
        
        # InnServiceWindowを作成
        char_item_window = InnServiceWindow('inn_character_item_mgmt', inn_config)
        
        # WindowManagerで表示
        window_manager = WindowManager.get_instance()
        window_manager.show_window(char_item_window, push_to_stack=True)
        
        logger.info(f"{character.name}のアイテム管理ウィンドウを表示しました")
    
    # === 魔法管理 ===
    
    def _show_spell_slot_management(self):
        """魔術スロット設定メニューを表示（InnServiceWindow使用）"""
        if not self.current_party:
            return
        
        # InnServiceWindow設定を作成
        inn_config = {
            'parent_facility': self,
            'current_party': self.current_party,
            'service_types': ['magic_management', 'spell_slot_management'],
            'title': '魔術スロット設定'
        }
        
        # InnServiceWindowを作成
        spell_mgmt_window = InnServiceWindow('inn_spell_management', inn_config)
        
        # WindowManagerで表示
        window_manager = WindowManager.get_instance()
        window_manager.show_window(spell_mgmt_window, push_to_stack=True)
        
        logger.info("魔術スロット設定ウィンドウを表示しました")
    
    def _show_prayer_slot_management(self):
        """祈祷スロット設定メニューを表示（InnServiceWindow使用）"""
        if not self.current_party:
            return
        
        # InnServiceWindow設定を作成
        inn_config = {
            'parent_facility': self,
            'current_party': self.current_party,
            'service_types': ['magic_management'],  # 祈祷も魔術管理の一部として統合
            'title': '祈祷スロット設定'
        }
        
        # InnServiceWindowを作成
        prayer_mgmt_window = InnServiceWindow('inn_prayer_management', inn_config)
        
        # WindowManagerで表示
        window_manager = WindowManager.get_instance()
        window_manager.show_window(prayer_mgmt_window, push_to_stack=True)
        
        logger.info("祈祷スロット設定ウィンドウを表示しました")
    
    def _show_character_spell_management(self, character):
        """キャラクター魔術管理メニューを表示（InnServiceWindow使用）"""
        # InnServiceWindow設定を作成
        inn_config = {
            'parent_facility': self,
            'current_party': self.current_party,
            'service_types': ['magic_management', 'spell_slot_management'],
            'selected_character': character,
            'title': f'{character.name} - 魔術管理'
        }
        
        # InnServiceWindowを作成
        char_spell_window = InnServiceWindow('inn_character_spell_mgmt', inn_config)
        
        # WindowManagerで表示
        window_manager = WindowManager.get_instance()
        window_manager.show_window(char_spell_window, push_to_stack=True)
        
        logger.info(f"{character.name}の魔術管理ウィンドウを表示しました")
    
    def _show_character_prayer_management(self, character):
        """キャラクター祈祷管理メニューを表示（InnServiceWindow使用）"""
        # InnServiceWindow設定を作成
        inn_config = {
            'parent_facility': self,
            'current_party': self.current_party,
            'service_types': ['magic_management'],  # 祈祷も魔術管理の一部として統合
            'selected_character': character,
            'title': f'{character.name} - 祈祷管理'
        }
        
        # InnServiceWindowを作成
        char_prayer_window = InnServiceWindow('inn_character_prayer_mgmt', inn_config)
        
        # WindowManagerで表示
        window_manager = WindowManager.get_instance()
        window_manager.show_window(char_prayer_window, push_to_stack=True)
        
        logger.info(f"{character.name}の祈祷管理ウィンドウを表示しました")
    
    # === 装備管理 ===
    
    def _show_party_equipment_status(self):
        """パーティ装備確認を表示（InnServiceWindow使用）"""
        if not self.current_party:
            return
        
        # InnServiceWindow設定を作成
        inn_config = {
            'parent_facility': self,
            'current_party': self.current_party,
            'service_types': ['equipment_management'],
            'title': 'パーティ装備確認'
        }
        
        # InnServiceWindowを作成
        equipment_status_window = InnServiceWindow('inn_party_equipment_status', inn_config)
        
        # WindowManagerで表示
        window_manager = WindowManager.get_instance()
        window_manager.show_window(equipment_status_window, push_to_stack=True)
        
        logger.info("パーティ装備確認ウィンドウを表示しました")
    
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
        """魔術装備メニュー（InnServiceWindow使用）"""
        try:
            spellbook = self._get_or_create_spellbook(character)
            
            # 習得済み魔法があるかチェック
            if not spellbook.learned_spells:
                self.show_information_dialog("情報", f"{character.name}は魔法を習得していません")
                return
            
            # InnServiceWindow設定を作成
            inn_config = {
                'parent_facility': self,
                'current_party': self.current_party,
                'service_types': ['spell_slot_management'],
                'selected_character': character,
                'title': f'{character.name} - 魔術装備'
            }
            
            # InnServiceWindowを作成
            spell_equip_window = InnServiceWindow('inn_spell_equip', inn_config)
            
            # WindowManagerで表示
            window_manager = WindowManager.get_instance()
            window_manager.show_window(spell_equip_window, push_to_stack=True)
            
            logger.info(f"{character.name}の魔術装備ウィンドウを表示しました")
            
        except Exception as e:
            logger.error(config_manager.get_text("app_log.spell_equipment_error").format(error=e))
            self.show_error_dialog(config_manager.get_text("common.error"), config_manager.get_text("app_log.spell_equipment_display_failed"))
    
    def _show_spell_status(self, character):
        """魔術状況表示（実装予定）"""
        self.show_information_dialog("実装予定", "この機能は実装予定です")
    
    # === 魔法スロット管理の実装メソッド ===
    
    def _get_or_create_spellbook(self, character) -> SpellBook:
        """キャラクターのスペルブックを取得または作成"""
        # キャラクターIDを使用してスペルブックを取得/作成
        if not hasattr(character, 'spellbook') or character.spellbook is None:
            character.spellbook = SpellBook(character.character_id)
        return character.spellbook
    
    def _equip_spell_to_slot(self, character, spell_id: str, level: int, slot_index: int):
        """魔法をスロットに装備"""
        try:
            spellbook = self._get_or_create_spellbook(character)
            success = spellbook.equip_spell_to_slot(spell_id, level, slot_index)
            
            if success:
                # 成功メッセージを表示
                spell = spell_manager.get_spell(spell_id)
                spell_name = spell.get_name() if spell else spell_id
                message = f"{spell_name}をレベル{level}スロット{slot_index + 1}に装備しました。"
                
                self.show_information_dialog(
                    "装備成功",
                    message,
                    buttons=[{
                        "text": "OK",
                        "callback": lambda: self._show_character_spell_slot_detail(character)
                    }]
                )
            else:
                # 失敗メッセージを表示
                message = "魔法の装備に失敗しました。\n\n原因：\n・魔法レベルがスロットレベルより高い\n・魔法を習得していない\n・無効なスロット"
                
                self.show_information_dialog(
                    "装備失敗",
                    message,
                    buttons=[{
                        "text": "OK",
                        "callback": lambda: self._show_character_spell_slot_detail(character)
                    }]
                )
                    
        except Exception as e:
            logger.error(f"魔法装備エラー: {e}")
            self.show_error_dialog("エラー", "魔法装備中にエラーが発生しました")
    
    def _show_character_spell_slot_detail(self, character):
        """キャラクター魔法スロット詳細メニューを表示（InnServiceWindow使用）"""
        # InnServiceWindow設定を作成
        inn_config = {
            'parent_facility': self,
            'current_party': self.current_party,
            'service_types': ['spell_slot_management'],
            'selected_character': character,
            'title': f'{character.name} - 魔法スロット詳細'
        }
        
        # InnServiceWindowを作成
        slot_detail_window = InnServiceWindow('inn_spell_slot_detail', inn_config)
        
        # WindowManagerで表示
        window_manager = WindowManager.get_instance()
        window_manager.show_window(slot_detail_window, push_to_stack=True)
        
        logger.info(f"{character.name}の魔法スロット詳細ウィンドウを表示しました")
    
    def _show_spell_slot_status(self, character):
        """魔法スロット状況を表示"""
        try:
            spellbook = self._get_or_create_spellbook(character)
            
            status_text = f"{character.name}の魔法スロット状況\n\n"
            
            for level in sorted(spellbook.spell_slots.keys()):
                level_slots = spellbook.spell_slots[level]
                status_text += f"Lv.{level} スロット:\n"
                
                for i, slot in enumerate(level_slots):
                    if slot.is_empty():
                        status_text += f"  [{i + 1}] (空)\n"
                    else:
                        spell = spell_manager.get_spell(slot.spell_id)
                        spell_name = spell.get_name() if spell else slot.spell_id
                        uses_text = f"{slot.current_uses}/{slot.max_uses}"
                        status_text += f"  [{i + 1}] {spell_name} ({uses_text})\n"
                
                status_text += "\n"
            
            self.show_information_dialog(
                "魔法スロット状況",
                status_text,
                buttons=[{"text": "戻る", "callback": None}]
            )
                
        except Exception as e:
            logger.error(f"スロット状況表示エラー: {e}")
            self.show_error_dialog("エラー", "スロット状況の表示に失敗しました")
    
    def _show_new_spell_user_selection(self, spell_users: List):
        """魔法使用者選択メニューを表示（InnServiceWindow使用）"""
        if not spell_users:
            self.show_information_dialog("情報", "魔法を使用できるキャラクターがいません")
            return
        
        # InnServiceWindow設定を作成
        inn_config = {
            'parent_facility': self,
            'current_party': self.current_party,
            'service_types': ['magic_management'],
            'title': '魔法使用者選択'
        }
        
        # InnServiceWindowを作成
        user_select_window = InnServiceWindow('inn_spell_user_selection', inn_config)
        
        # WindowManagerで表示
        window_manager = WindowManager.get_instance()
        window_manager.show_window(user_select_window, push_to_stack=True)
        
        logger.info("魔法使用者選択ウィンドウを表示しました")
    
    def _show_spell_slot_selection(self, character, spell_id: str):
        """魔法装備用のスロット選択メニューを表示（InnServiceWindow使用）"""
        try:
            spellbook = self._get_or_create_spellbook(character)
            spell = spell_manager.get_spell(spell_id)
            
            if not spell:
                self.show_error_dialog("エラー", "魔法データが見つかりません")
                return
            
            # InnServiceWindow設定を作成
            inn_config = {
                'parent_facility': self,
                'current_party': self.current_party,
                'service_types': ['spell_slot_management'],
                'selected_character': character,
                'context': {'target_spell_id': spell_id},
                'title': f'{spell.get_name()} - スロット選択'
            }
            
            # InnServiceWindowを作成
            slot_select_window = InnServiceWindow('inn_spell_slot_selection', inn_config)
            
            # WindowManagerで表示
            window_manager = WindowManager.get_instance()
            window_manager.show_window(slot_select_window, push_to_stack=True)
            
            logger.info(f"{spell.get_name()}のスロット選択ウィンドウを表示しました")
            
        except Exception as e:
            logger.error(f"スロット選択メニュー表示エラー: {e}")
            self.show_error_dialog("エラー", "スロット選択メニューの表示に失敗しました")
    
    def _show_prayer_equip_menu(self, character):
        """祈祷装備メニュー（実装予定）"""
        self.show_information_dialog("実装予定", "この機能は実装予定です")
    
    def _show_prayer_status(self, character):
        """祈祷状況表示（実装予定）"""
        self.show_information_dialog("実装予定", "この機能は実装予定です")