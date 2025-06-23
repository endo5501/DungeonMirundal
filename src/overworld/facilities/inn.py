"""宿屋"""

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
    """宿屋
    
    注意: このゲームでは地上部帰還時に自動回復するため、
    従来の宿屋での休息機能は提供しません。
    代わりに情報提供や雰囲気作りの場として機能します。
    """
    
    def __init__(self):
        super().__init__(
            facility_id="inn",
            facility_type=FacilityType.INN,
            name_key="facility.inn"
        )
        
        # 宿屋のアイテム預かりシステム（永続的）
        self.storage_inventory: Optional[Inventory] = None
        self._storage_initialized = False
        
        # UI要素
        self.storage_view_list: Optional[ItemSelectionList] = None
    
    def _setup_menu_items(self, menu: UIMenu):
        """宿屋固有のメニュー項目を設定"""
        menu.add_menu_item(
            "冒険の準備",
            self._show_adventure_preparation
        )
        
        menu.add_menu_item(
            "アイテム預かり",
            self._show_item_organization
        )
        
        menu.add_menu_item(
            "宿屋の主人と話す",
            self._talk_to_innkeeper
        )
        
        menu.add_menu_item(
            "旅の情報を聞く",
            self._show_travel_info
        )
        
        menu.add_menu_item(
            "酒場の噂話",
            self._show_tavern_rumors
        )
        
        menu.add_menu_item(
            "パーティ名を変更",
            self._change_party_name
        )
    
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
    
    def _handle_ui_selection_events(self, event: pygame.event.Event) -> bool:
        """UISelectionListのイベント処理をオーバーライド"""
        # 宿屋倉庫表示リスト
        if self.storage_view_list and self.storage_view_list.handle_event(event):
            return True
        
        return False
    
    def _talk_to_innkeeper(self):
        """宿屋の主人との会話"""
        messages = [
            (
                config_manager.get_text("inn.innkeeper.conversation.adventure_title"),
                config_manager.get_text("inn.innkeeper.conversation.adventure_message")
            ),
            (
                config_manager.get_text("inn.innkeeper.conversation.town_title"),
                config_manager.get_text("inn.innkeeper.conversation.town_message")
            ),
            (
                config_manager.get_text("inn.innkeeper.conversation.history_title"),
                config_manager.get_text("inn.innkeeper.conversation.history_message")
            )
        ]
        
        # ランダムにメッセージを選択
        import random
        title, message = random.choice(messages)
        
        # 新システムを使用（戻るボタン付き）
        if self.use_new_menu_system:
            def on_innkeeper_close():
                """宿屋の主人会話ダイアログ終了時の処理"""
                # 新システムでは自動的にメニューが管理される
                pass
            
            self.show_information_dialog(
                f"{config_manager.get_text('inn.innkeeper.title')} - {title}",
                message,
                on_innkeeper_close
            )
        else:
            # 旧システム（戻るボタンを追加）
            def on_innkeeper_back():
                """宿屋の主人会話ダイアログの戻るボタン処理"""
                self._close_dialog()
                # 明示的にメインメニューを再表示（問題の修正）
                if self.main_menu and ui_manager:
                    ui_manager.show_menu(self.main_menu.menu_id, modal=True)
            
            self._show_dialog(
                "innkeeper_dialog",
                f"{config_manager.get_text('inn.innkeeper.title')} - {title}",
                message,
                buttons=[
                    {
                        'text': config_manager.get_text("common.back"),
                        'command': on_innkeeper_back
                    }
                ]
            )
    
    def _show_travel_info(self):
        """旅の情報を表示"""
        travel_info = config_manager.get_text("inn.travel_info.content")
        
        # 新システムを使用（戻るボタン付き）
        if self.use_new_menu_system:
            def on_travel_info_close():
                """旅の情報ダイアログ終了時の処理"""
                # 新システムでは自動的にメニューが管理される
                pass
            
            self.show_information_dialog(
                config_manager.get_text("inn.travel_info.title"),
                travel_info,
                on_travel_info_close
            )
        else:
            # 旧システム（戻るボタンを追加）
            def on_travel_info_back():
                """旅の情報ダイアログの戻るボタン処理"""
                self._close_dialog()
                # 明示的にメインメニューを再表示（問題の修正）
                if self.main_menu and ui_manager:
                    ui_manager.show_menu(self.main_menu.menu_id, modal=True)
            
            self._show_dialog(
                "travel_info_dialog",
                config_manager.get_text("inn.travel_info.title"),
                travel_info,
                buttons=[
                    {
                        'text': config_manager.get_text("common.back"),
                        'command': on_travel_info_back
                    }
                ]
            )
    
    def _show_tavern_rumors(self):
        """酒場の噂話を表示"""
        rumors = [
            (
                config_manager.get_text("inn.rumors.dungeon_title"),
                config_manager.get_text("inn.rumors.dungeon_message")
            ),
            (
                config_manager.get_text("inn.rumors.monster_title"),
                config_manager.get_text("inn.rumors.monster_message")
            ),
            (
                config_manager.get_text("inn.rumors.legendary_title"),
                config_manager.get_text("inn.rumors.legendary_message")
            ),
            (
                config_manager.get_text("inn.rumors.adventurer_title"),
                config_manager.get_text("inn.rumors.adventurer_message")
            ),
            (
                config_manager.get_text("inn.rumors.merchant_title"),
                config_manager.get_text("inn.rumors.merchant_message")
            )
        ]
        
        # ランダムに噂を選択
        import random
        title, rumor = random.choice(rumors)
        
        # 新システムを使用（戻るボタン付き）
        if self.use_new_menu_system:
            # コールバック関数を定義（メニューが正しく復元されるように）
            def on_rumor_close():
                """噂話ダイアログ終了時の処理"""
                # 新システムでは自動的にメニューが管理される
                pass
            
            self.show_information_dialog(
                f"{config_manager.get_text('inn.rumors.title')} - {title}",
                rumor,
                on_rumor_close
            )
        else:
            # 旧システム（戻るボタンを追加）
            def on_rumor_back():
                """噂話ダイアログの戻るボタン処理"""
                self._close_dialog()
                # 明示的にメインメニューを再表示（問題の修正）
                if self.main_menu and ui_manager:
                    ui_manager.show_menu(self.main_menu.menu_id, modal=True)
            
            self._show_dialog(
                "rumor_dialog",
                f"{config_manager.get_text('inn.rumors.title')} - {title}",
                rumor,
                buttons=[
                    {
                        'text': config_manager.get_text("common.back"),
                        'command': on_rumor_back
                    }
                ]
            )
    
    def _change_party_name(self):
        """パーティ名変更機能"""
        if not self.current_party:
            self._show_dialog(
                "no_party_error_dialog",
                config_manager.get_text("inn.party_name.no_party_error_title"),
                config_manager.get_text("inn.party_name.no_party_error_message")
            )
            return
        
        # 現在のパーティ名を取得
        current_name = self.current_party.name if self.current_party.name else config_manager.get_text("inn.party_name.anonymous_party")
        
        # パーティ名変更ダイアログを表示
        name_input_dialog = UIInputDialog(
            "party_name_input_dialog",
            config_manager.get_text("inn.party_name.title"),
            f"{config_manager.get_text('inn.party_name.current_name_label').format(name=current_name)}\n\n"
            f"{config_manager.get_text('inn.party_name.input_prompt')}",
            initial_text=current_name,
            placeholder=config_manager.get_text("inn.party_name.placeholder"),
            on_confirm=self._on_party_name_confirmed,
            on_cancel=self._on_party_name_cancelled
        )
        
        ui_manager.add_dialog(name_input_dialog)
        ui_manager.show_dialog(name_input_dialog.dialog_id)
    
    def _on_party_name_confirmed(self, new_name: str):
        """パーティ名変更確認時の処理"""
        # 名前の検証と正規化
        validated_name = self._validate_party_name(new_name)
        
        if not validated_name:
            self._show_dialog(
                "invalid_name_dialog",
                config_manager.get_text("inn.party_name.invalid_name_title"),
                config_manager.get_text("inn.party_name.invalid_name_message")
            )
            return
        
        # パーティ名を更新
        old_name = self.current_party.name
        self.current_party.name = validated_name
        
        # 入力ダイアログを閉じる
        ui_manager.hide_menu("party_name_input_dialog")
        
        
        # 成功メッセージを表示
        success_message = config_manager.get_text("inn.party_name.success_message").format(
            old_name=old_name,
            new_name=validated_name
        )
        
        self._show_dialog(
            "name_change_success_dialog",
            config_manager.get_text("inn.party_name.success_title"),
            success_message
        )
        
        logger.info(f"パーティ名を変更: {old_name} → {validated_name}")
    
    def _on_party_name_cancelled(self):
        """パーティ名変更キャンセル時の処理"""
        # 入力ダイアログを閉じる
        ui_manager.hide_menu("party_name_input_dialog")
        
        
        logger.info("パーティ名変更がキャンセルされました")
    
    def _validate_party_name(self, name: str) -> str:
        """パーティ名のバリデーションと正規化"""
        if not name or not name.strip():
            return config_manager.get_text("inn.party_name.default_name")  # デフォルト名
        
        # 前後の空白を除去
        name = name.strip()
        
        # 長さ制限（30文字）
        if len(name) > 30:
            name = name[:30]
        
        # 危険な文字の除去（基本的なサニタイズ）
        dangerous_chars = ['<', '>', '&', '"', "'", '\n', '\r', '\t']
        for char in dangerous_chars:
            name = name.replace(char, '')
        
        # 空になった場合はデフォルト名
        if not name:
            return config_manager.get_text("inn.party_name.default_name")
        
        return name
    
    def _show_adventure_preparation(self):
        """冒険の準備メニューを表示"""
        if not self.current_party:
            if self.use_new_menu_system:
                self.show_error_dialog("エラー", "パーティが設定されていません")
            else:
                self._show_error_message("パーティが設定されていません")
            return
        
        prep_menu = UIMenu("adventure_prep_menu", "冒険の準備")
        
        prep_menu.add_menu_item(
            "アイテム整理",
            self._show_item_organization
        )
        
        prep_menu.add_menu_item(
            "魔術スロット設定",
            self._show_spell_slot_management
        )
        
        prep_menu.add_menu_item(
            "祈祷スロット設定",
            self._show_prayer_slot_management
        )
        
        prep_menu.add_menu_item(
            "パーティ装備確認",
            self._show_party_equipment_status
        )
        
        # 新システムでは戻るボタンは自動的に管理される
        if not self.use_new_menu_system:
            prep_menu.add_menu_item(
                config_manager.get_text("menu.back"),
                self._back_to_main_menu_from_submenu,
                [prep_menu]
            )
        else:
            prep_menu.add_menu_item(
                config_manager.get_text("menu.back"),
                self.back_to_previous_menu
            )
        
        # 新システムまたは旧システムでサブメニューを表示
        if self.use_new_menu_system:
            self.show_submenu(prep_menu, {'menu_type': 'adventure_prep'})
        else:
            self._show_submenu(prep_menu)
    
    def _show_item_organization(self):
        """アイテム整理画面を表示（新しい宿屋倉庫システム）"""
        if not self.current_party:
            return
        
        try:
            # 宿屋倉庫システムを使用
            from src.overworld.inn_storage import inn_storage_manager
            
            # パーティインベントリから宿屋倉庫への移行（初回のみ）
            party_inventory = self.current_party.get_party_inventory()
            if party_inventory:
                # パーティインベントリにアイテムがある場合は移行
                party_items_count = sum(1 for slot in party_inventory.slots if not slot.is_empty())
                if party_items_count > 0:
                    transferred = inn_storage_manager.transfer_from_party_inventory(self.current_party)
                    if transferred > 0:
                        self._show_dialog(
                            "migration_info_dialog",
                            "アイテム移行完了",
                            f"パーティインベントリから宿屋倉庫に\\n{transferred}個のアイテムを移動しました。\\n\\n"
                            "今後、購入したアイテムは直接\\n宿屋倉庫に搬入されます。"
                        )
            
            # 新しいアイテム整理メニューを表示
            self._show_new_item_organization_menu()
            
        except Exception as e:
            logger.error(f"アイテム整理画面表示エラー: {e}")
            self._show_error_message(f"アイテム整理画面の表示に失敗しました: {str(e)}")
    
    def _show_new_item_organization_menu(self):
        """新しいアイテム整理メニューを表示"""
        item_menu = UIMenu("item_organization_menu", "アイテム整理")
        
        item_menu.add_menu_item(
            "宿屋倉庫の確認",
            self._show_inn_storage_status
        )
        
        item_menu.add_menu_item(
            "キャラクター別アイテム管理",
            self._show_character_item_management
        )
        
        item_menu.add_menu_item(
            "魔術・祈祷書の使用",
            self._show_spell_item_usage
        )
        
        item_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._back_to_main_menu_from_submenu,
            [item_menu]
        )
        
        self._show_submenu(item_menu)
    
    def _show_inn_storage_status(self):
        """宿屋倉庫の状況をUISelectionListで表示"""
        from src.overworld.inn_storage import inn_storage_manager
        from src.items.item import item_manager
        
        storage = inn_storage_manager.get_storage()
        summary = inn_storage_manager.get_storage_summary()
        
        if summary['used_slots'] == 0:
            # 倉庫が空の場合はダイアログで表示
            storage_info = "【宿屋倉庫の状況】\\n\\n"
            storage_info += f"使用状況: {summary['used_slots']}/{summary['capacity']} スロット\\n"
            storage_info += f"使用率: {summary['usage_percentage']:.1f}%\\n\\n"
            storage_info += "倉庫は空です。\\n"
            
            self._show_dialog(
                "inn_storage_status_dialog",
                "宿屋倉庫の状況",
                storage_info,
                buttons=[
                    {
                        'text': "戻る",
                        'command': self._close_dialog
                    }
                ]
            )
            return
        
        # UISelectionListを使用して倉庫アイテムを表示
        import pygame
        list_rect = pygame.Rect(100, 100, 600, 500)
        
        self.storage_view_list = ItemSelectionList(
            relative_rect=list_rect,
            manager=ui_manager.pygame_gui_manager,
            title=f"宿屋倉庫 ({summary['used_slots']}/{summary['capacity']} スロット使用中)"
        )
        
        # アイテムをリストに追加
        items = storage.get_all_items()
        for slot_index, item_instance in items:
            item = item_manager.get_item(item_instance.item_id)
            if item:
                quantity_text = f" x{item_instance.quantity}" if item_instance.quantity > 1 else ""
                display_name = f"{item.get_name()}{quantity_text}"
                self.storage_view_list.add_item_data(
                    (slot_index, item_instance, item), 
                    display_name
                )
        
        # コールバック設定
        self.storage_view_list.on_item_details = self._show_storage_item_details
        
        # 表示
        self.storage_view_list.show()
    
    def _show_storage_item_details(self, item_data):
        """倉庫アイテムの詳細を表示"""
        slot_index, item_instance, item = item_data
        
        details = f"【{item.get_name()}】\\n\\n"
        details += f"説明: {item.get_description()}\\n"
        details += f"重量: {item.weight}\\n"
        details += f"希少度: {item.rarity.value}\\n"
        
        if item.is_weapon():
            details += f"攻撃力: {item.get_attack_power()}\\n"
            details += f"属性: {item.get_attribute()}\\n"
        elif item.is_armor():
            details += f"防御力: {item.get_defense()}\\n"
        elif item.is_consumable():
            details += f"効果: {item.get_effect_type()}\\n"
            if item.get_effect_value() > 0:
                details += f"効果値: {item.get_effect_value()}\\n"
        
        if item_instance.quantity > 1:
            details += f"\\n数量: {item_instance.quantity}\\n"
        
        if item_instance.identified:
            details += "\\n鑑定済み"
        else:
            details += "\\n未鑑定"
        
        details += f"\\nスロット位置: {slot_index}"
        
        self._show_dialog(
            "storage_item_detail_dialog",
            f"{item.get_name()} の詳細",
            details,
            buttons=[
                {
                    'text': "戻る",
                    'command': self._close_dialog
                }
            ]
        )
    
    def _hide_storage_view_list(self):
        """倉庫表示リストを非表示"""
        if hasattr(self, 'storage_view_list') and self.storage_view_list:
            self.storage_view_list.hide()
            self.storage_view_list.kill()
            self.storage_view_list = None
    
    def _show_character_item_management(self):
        """キャラクター別アイテム管理を表示"""
        if not self.current_party:
            return
        
        char_menu = UIMenu("character_item_menu", "キャラクター選択")
        
        for character in self.current_party.get_all_characters():
            char_info = f"{character.name} ({character.character_class})\\n"
            # キャラクターインベントリの状況
            char_inventory = character.get_inventory()
            used_slots = sum(1 for slot in char_inventory.slots if not slot.is_empty())
            char_info += f"所持: {used_slots}/{len(char_inventory.slots)} スロット"
            
            char_menu.add_menu_item(
                char_info,
                self._show_character_item_detail,
                [character]
            )
        
        char_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            lambda: self.back_to_previous_menu() if self.use_new_menu_system else self._show_new_item_organization_menu()
        )
        
        # 新システムが利用可能な場合は新システムを使用
        if self.use_new_menu_system:
            self.show_submenu(char_menu)
        else:
            self._show_submenu(char_menu)
    
    def _show_character_item_detail(self, character):
        """キャラクターのアイテム詳細管理"""
        item_mgmt_menu = UIMenu("character_item_mgmt_menu", f"{character.name} のアイテム管理")
        
        item_mgmt_menu.add_menu_item(
            "倉庫→キャラクター",
            self._show_storage_to_character_transfer,
            [character]
        )
        
        item_mgmt_menu.add_menu_item(
            "キャラクター→倉庫",
            self._show_character_to_storage_transfer,
            [character]
        )
        
        item_mgmt_menu.add_menu_item(
            "アイテム使用",
            self._show_character_item_usage,
            [character]
        )
        
        item_mgmt_menu.add_menu_item(
            "所持状況確認",
            self._show_character_inventory_status,
            [character]
        )
        
        item_mgmt_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            lambda: self.back_to_previous_menu() if self.use_new_menu_system else self._show_character_item_management()
        )
        
        # 新システムが利用可能な場合は新システムを使用
        if self.use_new_menu_system:
            self.show_submenu(item_mgmt_menu, {'character': character})
        else:
            self._show_submenu(item_mgmt_menu)
    
    def _show_storage_to_character_transfer(self, character):
        """倉庫からキャラクターへのアイテム転送UI"""
        from src.overworld.inn_storage import inn_storage_manager
        
        storage = inn_storage_manager.get_storage()
        storage_items = storage.get_all_items()
        
        if not storage_items:
            self._show_dialog(
                "no_storage_items_dialog",
                "倉庫→キャラクター",
                "宿屋倉庫にアイテムがありません。",
                buttons=["戻る"]
            )
            return
        
        self._show_storage_item_list(character, storage_items, "transfer_to_character")
    
    def _show_character_to_storage_transfer(self, character):
        """キャラクターから倉庫への転送UI"""
        char_inventory = character.get_inventory()
        char_items = []
        
        for i, slot in enumerate(char_inventory.slots):
            if not slot.is_empty():
                char_items.append((i, slot.item_instance))
        
        if not char_items:
            self._show_dialog(
                "no_char_items_dialog",
                "キャラクター→倉庫",
                f"{character.name}はアイテムを所持していません。",
                buttons=["戻る"]
            )
            return
        
        self._show_character_item_list(character, char_items, "transfer_to_storage")
    
    def _show_storage_item_list(self, character, items, action_type):
        """倉庫アイテム一覧をpygame UIメニューで表示"""
        title_text = f"宿屋倉庫 → {character.name}"
        storage_menu = UIMenu("storage_item_list", title_text)
        
        # アイテムリストを追加
        for slot_index, item_instance in items:
            item = item_manager.get_item(item_instance.item_id)
            if item:
                display_name = self._format_transfer_item_display(item_instance, item)
                storage_menu.add_menu_item(
                    display_name,
                    self._confirm_storage_to_character_transfer,
                    [character, slot_index, item_instance, item]
                )
        
        # 戻るボタン
        storage_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._back_to_character_detail,
            [character]
        )
        
        self._show_submenu(storage_menu)
    
    def _show_character_item_list(self, character, items, action_type):
        """キャラクターアイテム一覧をpygame UIメニューで表示"""
        title_text = f"{character.name} → 宿屋倉庫"
        character_menu = UIMenu("character_item_list", title_text)
        
        # アイテムリストを追加
        for slot_index, item_instance in items:
            item = item_manager.get_item(item_instance.item_id)
            if item:
                display_name = self._format_transfer_item_display(item_instance, item)
                character_menu.add_menu_item(
                    display_name,
                    self._confirm_character_to_storage_transfer,
                    [character, slot_index, item_instance, item]
                )
        
        # 戻るボタン
        character_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._back_to_character_detail,
            [character]
        )
        
        self._show_submenu(character_menu)
    
    def _format_transfer_item_display(self, item_instance, item) -> str:
        """転送用アイテム表示名をフォーマット"""
        quantity_text = f" x{item_instance.quantity}" if item_instance.quantity > 1 else ""
        return f"📦 {item.get_name()}{quantity_text}"
    
    def _confirm_storage_to_character_transfer(self, character, slot_index, item_instance, item):
        """倉庫→キャラクター転送確認"""
        self._cleanup_inn_item_ui()
        
        if item_instance.quantity > 1:
            # 数量選択ダイアログ
            self._show_quantity_selection_dialog(
                character, slot_index, item_instance, item, "storage_to_character"
            )
        else:
            # 直接転送
            self._execute_storage_to_character_transfer(character, slot_index, 1)
    
    def _confirm_character_to_storage_transfer(self, character, slot_index, item_instance, item):
        """キャラクター→倉庫転送確認"""
        self._cleanup_inn_item_ui()
        
        if item_instance.quantity > 1:
            # 数量選択ダイアログ
            self._show_quantity_selection_dialog(
                character, slot_index, item_instance, item, "character_to_storage"
            )
        else:
            # 直接転送
            self._execute_character_to_storage_transfer(character, slot_index, 1)
    
    def _show_quantity_selection_dialog(self, character, slot_index, item_instance, item, transfer_type):
        """数量選択ダイアログを表示"""
        quantity_menu = UIMenu("quantity_selection_menu", f"{item.get_name()} の数量選択")
        
        max_quantity = item_instance.quantity
        
        # 1個ずつのオプション
        quantity_menu.add_menu_item(
            "1個",
            self._execute_transfer_with_quantity,
            [character, slot_index, 1, transfer_type]
        )
        
        # 半分のオプション（2個以上の場合）
        if max_quantity >= 2:
            half_quantity = max_quantity // 2
            quantity_menu.add_menu_item(
                f"{half_quantity}個（半分）",
                self._execute_transfer_with_quantity,
                [character, slot_index, half_quantity, transfer_type]
            )
        
        # 全部のオプション
        quantity_menu.add_menu_item(
            f"{max_quantity}個（全部）",
            self._execute_transfer_with_quantity,
            [character, slot_index, max_quantity, transfer_type]
        )
        
        quantity_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._show_character_item_detail,
            [character]
        )
        
        self._show_submenu(quantity_menu)
    
    def _execute_transfer_with_quantity(self, character, slot_index, quantity, transfer_type):
        """指定数量でアイテム転送を実行"""
        if transfer_type == "storage_to_character":
            success = self._execute_storage_to_character_transfer(character, slot_index, quantity)
        else:
            success = self._execute_character_to_storage_transfer(character, slot_index, quantity)
        
        # 転送後、キャラクター詳細に戻る
        self._show_character_item_detail(character)
    
    def _execute_storage_to_character_transfer(self, character, slot_index, quantity):
        """倉庫→キャラクター転送を実行"""
        from src.overworld.inn_storage import inn_storage_manager
        
        success = inn_storage_manager.transfer_to_character_inventory(character, slot_index, quantity)
        
        if success:
            self._show_success_message(f"アイテムを{character.name}に渡しました。")
        else:
            self._show_error_message(f"{character.name}のインベントリが満杯です。")
        
        return success
    
    def _execute_character_to_storage_transfer(self, character, slot_index, quantity):
        """キャラクター→倉庫転送を実行"""
        from src.overworld.inn_storage import inn_storage_manager
        
        success = inn_storage_manager.transfer_from_character_inventory(character, slot_index, quantity)
        
        if success:
            self._show_success_message(f"{character.name}のアイテムを倉庫に預けました。")
        else:
            self._show_error_message("宿屋倉庫が満杯です。")
        
        return success
    
    def _show_character_item_usage(self, character):
        """キャラクターアイテム使用"""
        usage_info = f"【{character.name} のアイテム使用】\\n\\n"
        usage_info += "所持アイテムを使用できます。\\n"
        usage_info += "※この機能は後の段階で実装予定です"
        
        self._show_dialog(
            "character_item_usage_dialog",
            f"{character.name} のアイテム使用",
            usage_info
        )
    
    def _show_character_inventory_status(self, character):
        """キャラクター所持状況確認"""
        char_inventory = character.get_inventory()
        used_slots = sum(1 for slot in char_inventory.slots if not slot.is_empty())
        
        status_info = f"【{character.name} の所持状況】\\n\\n"
        status_info += f"個人インベントリ: {used_slots}/{len(char_inventory.slots)} スロット\\n\\n"
        
        if used_slots > 0:
            status_info += "所持アイテム:\\n"
            for i, slot in enumerate(char_inventory.slots):
                if not slot.is_empty():
                    item_instance = slot.item_instance
                    item = item_manager.get_item(item_instance.item_id)
                    if item:
                        quantity_text = f" x{item_instance.quantity}" if item_instance.quantity > 1 else ""
                        status_info += f"  [{i+1:2d}] {item.get_name()}{quantity_text}\\n"
        else:
            status_info += "所持アイテムなし"
        
        self._show_dialog(
            "character_inventory_status_dialog",
            f"{character.name} の所持状況",
            status_info,
            buttons=["戻る"]
        )
    
    def _cleanup_inn_item_ui(self):
        """宿屋UIのクリーンアップ（pygame版では不要）"""
        # pygame版ではUIMenuが自動的に管理されるため、クリーンアップは不要
        pass
    
    def _cleanup_and_return_to_character_detail(self, character):
        """UIをクリーンアップしてキャラクター詳細に戻る"""
        # pygame版では単純にキャラクター詳細に戻る
        self._show_character_item_detail(character)
    
    def _back_to_character_detail(self, character):
        """pygame版用：キャラクター詳細に戻る"""
        self._show_character_item_detail(character)
    
    def _show_spell_item_usage(self):
        """魔術・祈祷書の使用メニュー"""
        if not self.current_party:
            return
        
        # 宿屋倉庫から魔術書・祈祷書を検索
        from src.overworld.inn_storage import inn_storage_manager
        storage = inn_storage_manager.get_storage()
        
        spell_items = []
        for slot_index, item_instance in storage.get_all_items():
            item = item_manager.get_item(item_instance.item_id)
            if item and item.item_type.value == "spellbook":
                spell_items.append((slot_index, item_instance, item))
        
        if not spell_items:
            self._show_dialog(
                "no_spell_items_dialog",
                "魔術・祈祷書の使用",
                "宿屋倉庫に魔術書・祈祷書がありません。\\n\\n"
                "魔術協会や教会で購入してください。"
            )
            return
        
        # 魔術書・祈祷書選択メニュー
        usage_menu = UIMenu("spell_item_usage_menu", "魔術・祈祷書の使用")
        
        for slot_index, item_instance, item in spell_items:
            item_info = f"{item.get_name()}"
            if hasattr(item, 'spell_id'):
                item_info += f" ({item.spell_id})"
            if item_instance.quantity > 1:
                item_info += f" x{item_instance.quantity}"
            
            usage_menu.add_menu_item(
                item_info,
                self._use_spell_item,
                [slot_index, item_instance, item]
            )
        
        usage_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._back_to_main_menu_from_submenu,
            [usage_menu]
        )
        
        self._show_submenu(usage_menu)
    
    def _use_spell_item(self, slot_index: int, item_instance, item):
        """魔術書・祈祷書を使用"""
        if not self.current_party:
            return
        
        # 使用可能なキャラクターを特定
        eligible_characters = []
        for character in self.current_party.get_all_characters():
            if self._can_character_use_spell_item(character, item):
                eligible_characters.append(character)
        
        if not eligible_characters:
            self._show_dialog(
                "no_eligible_characters_dialog",
                "使用不可",
                f"{item.get_name()}を使用できる\\n"
                "キャラクターがいません。\\n\\n"
                "必要な職業や能力値を確認してください。"
            )
            return
        
        # キャラクター選択メニュー
        character_menu = UIMenu("spell_item_character_menu", f"{item.get_name()}の使用対象")
        
        for character in eligible_characters:
            char_info = f"{character.name} ({character.character_class})"
            character_menu.add_menu_item(
                char_info,
                self._confirm_spell_item_usage,
                [character, slot_index, item_instance, item]
            )
        
        character_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._show_spell_item_usage
        )
        
        self._show_submenu(character_menu)
    
    def _can_character_use_spell_item(self, character, item) -> bool:
        """キャラクターが魔術書・祈祷書を使用できるかチェック"""
        # 職業制限チェック
        if hasattr(item, 'required_class') and item.required_class:
            if character.character_class not in item.required_class:
                return False
        
        # 既に習得済みかチェック
        if hasattr(item, 'spell_id'):
            try:
                from src.magic.spells import spell_manager
                if hasattr(character, 'learned_spells'):
                    if item.spell_id in character.learned_spells:
                        return False
            except:
                pass
        
        return True
    
    def _confirm_spell_item_usage(self, character, slot_index: int, item_instance, item):
        """魔術書・祈祷書使用の確認"""
        confirm_info = f"【{item.get_name()}の使用確認】\\n\\n"
        confirm_info += f"対象: {character.name} ({character.character_class})\\n"
        confirm_info += f"効果: {item.get_description()}\\n\\n"
        
        if hasattr(item, 'spell_id'):
            confirm_info += f"習得する魔法: {item.spell_id}\\n\\n"
        
        confirm_info += "このアイテムを使用しますか？\\n"
        confirm_info += "※使用後、アイテムは消滅します"
        
        self._show_dialog(
            "spell_item_usage_confirm_dialog",
            "使用確認",
            confirm_info,
            buttons=[
                {
                    'text': "使用する",
                    'command': lambda: self._execute_spell_item_usage(character, slot_index, item_instance, item)
                },
                {
                    'text': "キャンセル",
                    'command': self._close_dialog
                }
            ]
        )
    
    def _execute_spell_item_usage(self, character, slot_index: int, item_instance, item):
        """魔術書・祈祷書使用を実行"""
        self._close_dialog()
        
        try:
            # 魔法習得処理
            if hasattr(item, 'spell_id'):
                if not hasattr(character, 'learned_spells'):
                    character.learned_spells = []
                
                if item.spell_id not in character.learned_spells:
                    character.learned_spells.append(item.spell_id)
                    logger.info(f"{character.name} が {item.spell_id} を習得しました")
            
            # アイテムを倉庫から削除
            from src.overworld.inn_storage import inn_storage_manager
            storage = inn_storage_manager.get_storage()
            removed_item = storage.remove_item(slot_index, 1)
            
            if removed_item:
                success_message = f"{character.name} が {item.get_name()} を使用しました。\\n\\n"
                if hasattr(item, 'spell_id'):
                    success_message += f"魔法「{item.spell_id}」を習得しました！"
                
                self._show_dialog(
                    "spell_item_usage_success_dialog",
                    "使用完了",
                    success_message
                )
            else:
                self._show_error_message("アイテムの削除に失敗しました")
                
        except Exception as e:
            logger.error(f"魔術書・祈祷書使用エラー: {e}")
            self._show_error_message(f"アイテム使用に失敗しました: {str(e)}")
    
    def _show_inventory_ui(self, inventory):
        """インベントリUIを表示"""
        # インベントリの内容を取得
        inventory_info = "【パーティインベントリ】\n\n"
        
        if hasattr(inventory, 'slots'):
            used_slots = sum(1 for slot in inventory.slots if not slot.is_empty())
            total_slots = len(inventory.slots)
            inventory_info += f"使用スロット: {used_slots}/{total_slots}\n\n"
            
            if used_slots == 0:
                inventory_info += "アイテムがありません。\n\n"
            else:
                for i, slot in enumerate(inventory.slots):
                    if not slot.is_empty():
                        item_instance = slot.item_instance
                        item = item_manager.get_item(item_instance.item_id)
                        if item:
                            quantity_text = f" x{item_instance.quantity}" if item_instance.quantity > 1 else ""
                            inventory_info += f"[{i+1:2d}] {item.get_name()}{quantity_text}\n"
        else:
            inventory_info += "インベントリシステムにアクセスできません。"
        
        inventory_info += "\n※詳細なアイテム管理はインベントリUIで行えます"
        
        self._show_dialog(
            "inventory_ui_dialog",
            "アイテム整理",
            inventory_info
        )
    
    def _show_spell_slot_management(self):
        """魔術スロット管理画面を表示（新システム）"""
        if not self.current_party:
            return
        
        try:
            # 魔法を使用できるキャラクターを検索
            spell_users = []
            for character in self.current_party.get_all_characters():
                if character.character_class in ['mage', 'priest', 'bishop']:
                    spell_users.append(character)
            
            if not spell_users:
                self._show_dialog(
                    "no_spell_users_dialog",
                    "魔術スロット設定",
                    "パーティに魔法を使用できる\n"
                    "キャラクターがいません。\n\n"
                    "魔術師、僧侶、司教のみが\n"
                    "魔法を使用できます。"
                )
                return
            
            # 新しい魔法使いキャラクター選択メニューを表示
            self._show_new_spell_user_selection(spell_users)
            
        except Exception as e:
            logger.error(f"魔術スロット管理画面表示エラー: {e}")
            self._show_error_message(f"魔術スロット管理画面の表示に失敗しました: {str(e)}")
    
    def _show_new_spell_user_selection(self, spell_users):
        """新しい魔法使いキャラクター選択画面"""
        spell_user_menu = UIMenu("spell_user_selection", "魔術スロット設定 - キャラクター選択")
        
        for character in spell_users:
            # キャラクターの魔法情報を取得
            spell_info = self._get_character_spell_summary(character)
            display_name = f"{character.name} ({character.character_class})\\n{spell_info}"
            
            spell_user_menu.add_menu_item(
                display_name,
                self._show_character_spell_slot_detail,
                [character]
            )
        
        spell_user_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._back_to_main_menu_from_submenu,
            [spell_user_menu]
        )
        
        self._show_submenu(spell_user_menu)
    
    def _get_character_spell_summary(self, character) -> str:
        """キャラクターの魔法要約情報を取得"""
        try:
            # スペルブックを取得または初期化
            spellbook = self._get_or_create_spellbook(character)
            
            learned_count = len(spellbook.learned_spells)
            
            # スロット使用状況を計算
            total_slots = 0
            equipped_slots = 0
            
            for level, slots in spellbook.spell_slots.items():
                total_slots += len(slots)
                equipped_slots += sum(1 for slot in slots if not slot.is_empty())
            
            return f"習得魔法: {learned_count}個\\nスロット: {equipped_slots}/{total_slots}"
        except:
            return "魔法情報取得不可"
    
    def _get_or_create_spellbook(self, character):
        """キャラクターのスペルブックを取得または作成"""
        from src.magic.spells import SpellBook
        
        # キャラクターにスペルブックがない場合は作成
        if not hasattr(character, 'spellbook'):
            character.spellbook = SpellBook(character.character_id)
            
            # 基本魔法を習得させる（テスト用）
            if character.character_class == 'mage':
                character.spellbook.learn_spell('fireball')
                character.spellbook.learn_spell('ice_shard')
                character.spellbook.learn_spell('lightning_bolt')
            elif character.character_class == 'priest':
                character.spellbook.learn_spell('heal')
                character.spellbook.learn_spell('cure_poison')
                character.spellbook.learn_spell('blessing')
            elif character.character_class == 'bishop':
                character.spellbook.learn_spell('fireball')
                character.spellbook.learn_spell('heal')
                character.spellbook.learn_spell('dispel_magic')
        
        return character.spellbook
    
    def _show_character_spell_slot_detail(self, character):
        """キャラクターの魔術スロット詳細管理"""
        spell_mgmt_menu = UIMenu("character_spell_mgmt_menu", f"{character.name} の魔術スロット管理")
        
        spell_mgmt_menu.add_menu_item(
            "スロット状況確認",
            self._show_spell_slot_status,
            [character]
        )
        
        spell_mgmt_menu.add_menu_item(
            "魔法をスロットに装備",
            self._show_spell_equip_menu,
            [character]
        )
        
        spell_mgmt_menu.add_menu_item(
            "スロットから魔法を解除",
            self._show_spell_unequip_menu,
            [character]
        )
        
        spell_mgmt_menu.add_menu_item(
            "習得済み魔法一覧",
            self._show_learned_spells_list,
            [character]
        )
        
        spell_mgmt_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._show_adventure_preparation
        )
        
        self._show_submenu(spell_mgmt_menu)
    
    def _get_spell_users(self):
        """魔法使いキャラクターリストを取得"""
        spell_users = []
        for character in self.current_party.get_all_characters():
            if character.character_class in ['mage', 'priest', 'bishop']:
                spell_users.append(character)
        return spell_users
    
    def _show_spell_slot_status(self, character):
        """スロット状況を表示"""
        spellbook = self._get_or_create_spellbook(character)
        
        status_info = f"【{character.name} のスロット状況】\\n\\n"
        status_info += f"職業: {character.character_class}\\n"
        status_info += f"レベル: {character.experience.level}\\n\\n"
        
        # レベル別スロット状況
        for level in sorted(spellbook.spell_slots.keys()):
            slots = spellbook.spell_slots[level]
            status_info += f"Lv.{level} スロット ({len(slots)}個):\\n"
            
            for i, slot in enumerate(slots):
                if slot.is_empty():
                    status_info += f"  [{i+1}] 空\\n"
                else:
                    uses_text = f" ({slot.current_uses}/{slot.max_uses}回)"
                    status_info += f"  [{i+1}] {slot.spell_id}{uses_text}\\n"
            status_info += "\\n"
        
        status_info += "※スロットに装備した魔法は戦闘で使用できます"
        
        self._show_dialog(
            "spell_slot_status_dialog",
            f"{character.name} のスロット状況",
            status_info
        )
    
    def _show_spell_equip_menu(self, character):
        """魔法装備メニューを表示"""
        spellbook = self._get_or_create_spellbook(character)
        
        if not spellbook.learned_spells:
            self._show_dialog(
                "no_learned_spells_dialog",
                "魔法装備",
                f"{character.name}は魔法を習得していません。\\n\\n"
                "魔術師ギルドで魔術書を購入するか、\\n"
                "アイテムから魔法を習得してください。"
            )
            return
        
        # 装備可能な魔法のリストを表示
        self._show_equippable_spells_list(character, spellbook)
    
    def _show_equippable_spells_list(self, character, spellbook):
        """装備可能魔法リストをpygame UIメニューで表示"""
        from src.magic.spells import spell_manager
        
        title_text = f"{character.name} - 魔法装備"
        spell_menu = UIMenu("equippable_spells_list", title_text)
        
        # 魔法リストを追加
        for spell_id in spellbook.learned_spells:
            spell = spell_manager.get_spell(spell_id)
            if spell:
                display_name = f"🔮 Lv.{spell.level} {spell.get_name()}"
                spell_menu.add_menu_item(
                    display_name,
                    self._show_slot_selection_for_equip,
                    [character, spell]
                )
        
        # 戻るボタン
        spell_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._back_to_spell_detail,
            [character]
        )
        
        self._show_submenu(spell_menu)
    
    def _show_slot_selection_for_equip(self, character, spell):
        """魔法装備用のスロット選択"""
        self._cleanup_spell_mgmt_ui()
        
        spellbook = self._get_or_create_spellbook(character)
        
        slot_menu = UIMenu("slot_selection_menu", f"{spell.get_name()} の装備スロット選択")
        
        # 装備可能なスロットレベルのみ表示
        for level in sorted(spellbook.spell_slots.keys()):
            if spell.level <= level:  # 魔法レベル以上のスロットのみ
                slots = spellbook.spell_slots[level]
                for i, slot in enumerate(slots):
                    slot_status = "空" if slot.is_empty() else f"装備中: {slot.spell_id}"
                    slot_name = f"Lv.{level} スロット[{i+1}] - {slot_status}"
                    
                    slot_menu.add_menu_item(
                        slot_name,
                        self._equip_spell_to_slot,
                        [character, spell.spell_id, level, i]
                    )
        
        slot_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._show_spell_equip_menu,
            [character]
        )
        
        self._show_submenu(slot_menu)
    
    def _equip_spell_to_slot(self, character, spell_id, level, slot_index):
        """魔法をスロットに装備"""
        spellbook = self._get_or_create_spellbook(character)
        
        success = spellbook.equip_spell_to_slot(spell_id, level, slot_index)
        
        if success:
            # 成功メッセージ表示後にメニューに戻るためのコールバックを設定
            def on_success_ok():
                if self.use_new_menu_system:
                    # 新システム: ダイアログのみ閉じて、メニューは明示的に表示
                    # back_to_previous_menu()は使わず、直接メニューに戻る
                    pass
                else:
                    # 旧システム: ダイアログを閉じて明示的にメニューに戻る
                    self._close_dialog()
                # 必ずキャラクタースペルスロット詳細に戻る
                self._show_character_spell_slot_detail(character)
            
            # 新システムを優先的に使用
            if self.use_new_menu_system and self.dialog_template:
                # 新システムでダイアログ表示
                self.show_success_dialog(
                    "装備完了",
                    f"{spell_id}をLv.{level}スロット[{slot_index+1}]に装備しました。",
                    on_success_ok
                )
            else:
                # 旧システムでダイアログ表示
                self._show_dialog(
                    f"{self.facility_id}_spell_equip_success",
                    "装備完了",
                    f"{spell_id}をLv.{level}スロット[{slot_index+1}]に装備しました。",
                    buttons=[
                        {
                            'text': config_manager.get_text("common.ok"),
                            'command': on_success_ok
                        }
                    ]
                )
        else:
            # エラーメッセージ表示後にメニューに戻るためのコールバックを設定
            def on_error_ok():
                if self.use_new_menu_system:
                    # 新システム: ダイアログのみ閉じて、メニューは明示的に表示
                    # back_to_previous_menu()は使わず、直接メニューに戻る
                    pass
                else:
                    # 旧システム: ダイアログを閉じて明示的にメニューに戻る
                    self._close_dialog()
                # 必ずキャラクタースペルスロット詳細に戻る
                self._show_character_spell_slot_detail(character)
            
            # 新システムを優先的に使用
            if self.use_new_menu_system and self.dialog_template:
                # 新システムでダイアログ表示
                self.show_error_dialog(
                    config_manager.get_text("common.error"),
                    "魔法の装備に失敗しました。",
                    on_error_ok
                )
            else:
                # 旧システムでダイアログ表示
                self._show_dialog(
                    f"{self.facility_id}_spell_equip_error",
                    config_manager.get_text("common.error"),
                    "魔法の装備に失敗しました。",
                    buttons=[
                        {
                            'text': config_manager.get_text("common.ok"),
                            'command': on_error_ok
                        }
                    ]
                )
    
    def _cleanup_spell_mgmt_ui(self):
        """魔法管理UIのクリーンアップ（pygame版では不要）"""
        # pygame版ではUIMenuが自動的に管理されるため、クリーンアップは不要
        pass
    
    def _cleanup_and_return_to_spell_detail(self, character):
        """UIをクリーンアップして魔法詳細に戻る"""
        # pygame版では単純に魔法詳細に戻る
        self._show_character_spell_slot_detail(character)
    
    def _back_to_spell_detail(self, character):
        """pygame版用：魔法詳細に戻る"""
        self._show_character_spell_slot_detail(character)
    
    def _show_spell_unequip_menu(self, character):
        """魔法解除メニュー"""
        unequip_info = f"【{character.name} の魔法解除】\\n\\n"
        unequip_info += "装備中の魔法をスロットから解除できます。\\n"
        unequip_info += "※この機能は次の段階で実装予定です"
        
        self._show_dialog(
            "spell_unequip_dialog",
            f"{character.name} の魔法解除",
            unequip_info
        )
    
    def _show_learned_spells_list(self, character):
        """習得済み魔法一覧"""
        spellbook = self._get_or_create_spellbook(character)
        
        spells_info = f"【{character.name} の習得済み魔法】\\n\\n"
        
        if not spellbook.learned_spells:
            spells_info += "習得済み魔法がありません。\\n\\n"
            spells_info += "魔術師ギルドで魔術書を購入するか、\\n"
            spells_info += "アイテムから魔法を習得してください。"
        else:
            from src.magic.spells import spell_manager
            
            for spell_id in spellbook.learned_spells:
                spell = spell_manager.get_spell(spell_id)
                if spell:
                    spells_info += f"🔮 Lv.{spell.level} {spell.get_name()}\\n"
                    spells_info += f"    {spell.get_description()}\\n\\n"
        
        self._show_dialog(
            "learned_spells_dialog",
            f"{character.name} の習得済み魔法",
            spells_info
        )
    
    def _show_spell_user_selection(self, spell_users):
        """魔法使いキャラクター選択画面を表示"""
        spell_user_menu = UIMenu("spell_user_selection", "魔法使いキャラクター選択")
        
        for character in spell_users:
            # キャラクターの魔法スロット状況を取得
            slot_info = self._get_spell_slot_info(character)
            display_name = f"{character.name} ({character.character_class})\n{slot_info}"
            
            spell_user_menu.add_menu_item(
                display_name,
                self._show_character_spell_management,
                [character]
            )
        
        spell_user_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._back_to_main_menu_from_submenu,
            [spell_user_menu]
        )
        
        self._show_submenu(spell_user_menu)
    
    def _get_spell_slot_info(self, character) -> str:
        """キャラクターの魔法スロット情報を取得"""
        try:
            if hasattr(character, 'spell_slots'):
                equipped_spells = sum(1 for slot in character.spell_slots if slot is not None)
                total_slots = len(character.spell_slots)
                return f"装備中: {equipped_spells}/{total_slots}スロット"
            else:
                return "魔法スロット: 未実装"
        except:
            return "魔法スロット: 情報取得不可"
    
    def _show_character_spell_management(self, character):
        """キャラクターの魔法管理画面を表示"""
        spell_info = f"【{character.name} の魔法管理】\n\n"
        spell_info += f"職業: {character.character_class}\n"
        spell_info += f"レベル: {character.experience.level}\n\n"
        
        # 習得済み魔法の表示
        if hasattr(character, 'learned_spells'):
            spell_info += "習得済み魔法:\n"
            if character.learned_spells:
                for spell_id in character.learned_spells:
                    spell_info += f"  • {spell_id}\n"
            else:
                spell_info += "  なし\n"
        else:
            spell_info += "習得済み魔法: システム未実装\n"
        
        spell_info += "\n"
        
        # 装備中魔法の表示
        if hasattr(character, 'spell_slots'):
            spell_info += "装備中魔法:\n"
            for i, spell in enumerate(character.spell_slots):
                if spell:
                    spell_info += f"  スロット{i+1}: {spell}\n"
                else:
                    spell_info += f"  スロット{i+1}: 空\n"
        else:
            spell_info += "魔法スロット: システム未実装"
        
        spell_info += "\n※詳細な魔法管理は専用UIで行えます"
        
        self._show_dialog(
            "character_spell_dialog",
            f"{character.name} の魔法管理",
            spell_info
        )
    
    def _show_prayer_slot_management(self):
        """祈祷スロット管理画面を表示"""
        if not self.current_party:
            return
        
        try:
            # 祈祷を使用できるキャラクターを検索（僧侶系）
            prayer_users = []
            for character in self.current_party.get_all_characters():
                if character.character_class in ['priest', 'bishop']:
                    prayer_users.append(character)
            
            if not prayer_users:
                self._show_dialog(
                    "no_prayer_users_dialog",
                    "祈祷スロット設定",
                    "パーティに祈祷を使用できる\n"
                    "キャラクターがいません。\n\n"
                    "僧侶、司教のみが\n"
                    "祈祷を使用できます。"
                )
                return
            
            # 祈祷使いキャラクター選択メニューを表示
            self._show_prayer_user_selection(prayer_users)
            
        except Exception as e:
            logger.error(f"祈祷スロット管理画面表示エラー: {e}")
            self._show_error_message(f"祈祷スロット管理画面の表示に失敗しました: {str(e)}")
    
    def _show_prayer_user_selection(self, prayer_users):
        """祈祷使いキャラクター選択画面を表示"""
        prayer_user_menu = UIMenu("prayer_user_selection", "祈祷使いキャラクター選択")
        
        for character in prayer_users:
            # キャラクターの祈祷スロット状況を取得
            slot_info = self._get_prayer_slot_info(character)
            display_name = f"{character.name} ({character.character_class})\n{slot_info}"
            
            prayer_user_menu.add_menu_item(
                display_name,
                self._show_character_prayer_management,
                [character]
            )
        
        prayer_user_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._back_to_main_menu_from_submenu,
            [prayer_user_menu]
        )
        
        self._show_submenu(prayer_user_menu)
    
    def _get_prayer_slot_info(self, character) -> str:
        """キャラクターの祈祷スロット情報を取得"""
        try:
            if hasattr(character, 'prayer_slots'):
                equipped_prayers = sum(1 for slot in character.prayer_slots if slot is not None)
                total_slots = len(character.prayer_slots)
                return f"装備中: {equipped_prayers}/{total_slots}スロット"
            elif hasattr(character, 'spell_slots'):  # 祈祷も魔法システムを使用
                equipped_spells = sum(1 for slot in character.spell_slots if slot is not None)
                total_slots = len(character.spell_slots)
                return f"装備中: {equipped_spells}/{total_slots}スロット"
            else:
                return "祈祷スロット: 未実装"
        except:
            return "祈祷スロット: 情報取得不可"
    
    def _show_character_prayer_management(self, character):
        """キャラクターの祈祷管理画面を表示"""
        prayer_info = f"【{character.name} の祈祷管理】\n\n"
        prayer_info += f"職業: {character.character_class}\n"
        prayer_info += f"レベル: {character.experience.level}\n\n"
        
        # 習得済み祈祷の表示
        if hasattr(character, 'learned_prayers'):
            prayer_info += "習得済み祈祷:\n"
            if character.learned_prayers:
                for prayer_id in character.learned_prayers:
                    prayer_info += f"  • {prayer_id}\n"
            else:
                prayer_info += "  なし\n"
        elif hasattr(character, 'learned_spells'):  # 祈祷も魔法システムを使用
            prayer_info += "習得済み祈祷:\n"
            priest_spells = [spell for spell in character.learned_spells if 'heal' in spell or 'cure' in spell or 'blessing' in spell]
            if priest_spells:
                for spell_id in priest_spells:
                    prayer_info += f"  • {spell_id}\n"
            else:
                prayer_info += "  なし\n"
        else:
            prayer_info += "習得済み祈祷: システム未実装\n"
        
        prayer_info += "\n"
        
        # 装備中祈祷の表示
        if hasattr(character, 'prayer_slots'):
            prayer_info += "装備中祈祷:\n"
            for i, prayer in enumerate(character.prayer_slots):
                if prayer:
                    prayer_info += f"  スロット{i+1}: {prayer}\n"
                else:
                    prayer_info += f"  スロット{i+1}: 空\n"
        elif hasattr(character, 'spell_slots'):
            prayer_info += "装備中祈祷（魔法スロット共用）:\n"
            for i, spell in enumerate(character.spell_slots):
                if spell:
                    prayer_info += f"  スロット{i+1}: {spell}\n"
                else:
                    prayer_info += f"  スロット{i+1}: 空\n"
        else:
            prayer_info += "祈祷スロット: システム未実装"
        
        prayer_info += "\n※詳細な祈祷管理は専用UIで行えます"
        
        self._show_dialog(
            "character_prayer_dialog",
            f"{character.name} の祈祷管理",
            prayer_info
        )
    
    def _show_party_equipment_status(self):
        """パーティ装備管理画面を表示（新システム）"""
        if not self.current_party:
            return
        
        try:
            # キャラクター選択メニューを表示
            self._show_equipment_character_selection()
            
        except Exception as e:
            logger.error(f"装備管理画面表示エラー: {e}")
            self._show_error_message(f"装備管理画面の表示に失敗しました: {str(e)}")
    
    def _show_equipment_character_selection(self):
        """装備管理キャラクター選択画面"""
        equipment_char_menu = UIMenu("equipment_char_menu", "装備管理 - キャラクター選択")
        
        for character in self.current_party.get_all_characters():
            # キャラクターの装備要約を取得
            equipment_summary = self._get_character_equipment_summary(character)
            display_name = f"{character.name} ({character.character_class})\\n{equipment_summary}"
            
            equipment_char_menu.add_menu_item(
                display_name,
                self._show_character_equipment_detail,
                [character]
            )
        
        equipment_char_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._back_to_main_menu_from_submenu,
            [equipment_char_menu]
        )
        
        self._show_submenu(equipment_char_menu)
    
    def _get_character_equipment_summary(self, character) -> str:
        """キャラクターの装備要約を取得"""
        try:
            equipment = character.get_equipment()
            equipped_count = 0
            total_slots = 4  # 武器、防具、アクセサリ×2
            
            for slot_name in ['weapon', 'armor', 'accessory_1', 'accessory_2']:
                if hasattr(equipment, 'slots') and equipment.slots.get(slot_name):
                    equipped_count += 1
            
            return f"装備: {equipped_count}/{total_slots} スロット"
        except:
            return "装備情報取得不可"
    
    def _show_character_equipment_detail(self, character):
        """キャラクターの装備詳細管理"""
        equipment_mgmt_menu = UIMenu("character_equipment_mgmt_menu", f"{character.name} の装備管理")
        
        equipment_mgmt_menu.add_menu_item(
            "装備状況確認",
            self._show_equipment_status,
            [character]
        )
        
        equipment_mgmt_menu.add_menu_item(
            "アイテムを装備",
            self._show_equipment_equip_menu,
            [character]
        )
        
        equipment_mgmt_menu.add_menu_item(
            "装備を解除",
            self._show_equipment_unequip_menu,
            [character]
        )
        
        equipment_mgmt_menu.add_menu_item(
            "装備比較",
            self._show_equipment_comparison,
            [character]
        )
        
        equipment_mgmt_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._show_equipment_character_selection
        )
        
        self._show_submenu(equipment_mgmt_menu)
    
    def _show_equipment_status(self, character):
        """装備状況を表示"""
        try:
            equipment = character.get_equipment()
            
            status_info = f"【{character.name} の装備状況】\\n\\n"
            status_info += f"職業: {character.character_class}\\n"
            status_info += f"レベル: {character.experience.level}\\n\\n"
            
            # 装備情報
            slot_names = {
                'weapon': '武器',
                'armor': '防具', 
                'accessory_1': 'アクセサリ1',
                'accessory_2': 'アクセサリ2'
            }
            
            for slot_name, display_name in slot_names.items():
                equipment_name = self._get_equipment_name(equipment, slot_name)
                status_info += f"{display_name}: {equipment_name}\\n"
            
            # 装備ボーナス
            if hasattr(equipment, 'get_total_bonus'):
                bonus = equipment.get_total_bonus()
                if any(getattr(bonus, attr, 0) > 0 for attr in ['strength', 'agility', 'intelligence', 'faith', 'luck', 'attack_power', 'defense_power']):
                    status_info += "\\n装備ボーナス:\\n"
                    if bonus.strength > 0: status_info += f"  力: +{bonus.strength}\\n"
                    if bonus.agility > 0: status_info += f"  敏捷: +{bonus.agility}\\n"
                    if bonus.intelligence > 0: status_info += f"  知恵: +{bonus.intelligence}\\n"
                    if bonus.faith > 0: status_info += f"  信仰: +{bonus.faith}\\n"
                    if bonus.luck > 0: status_info += f"  運: +{bonus.luck}\\n"
                    if bonus.attack_power > 0: status_info += f"  攻撃力: +{bonus.attack_power}\\n"
                    if bonus.defense_power > 0: status_info += f"  防御力: +{bonus.defense_power}\\n"
            
            status_info += "\\n※装備の変更は「アイテムを装備」で行えます"
            
            self._show_dialog(
                "character_equipment_status_dialog",
                f"{character.name} の装備状況",
                status_info
            )
        except Exception as e:
            logger.error(f"装備状況表示エラー: {e}")
            self._show_error_message("装備状況の表示に失敗しました")
    
    def _show_equipment_equip_menu(self, character):
        """装備可能アイテム選択メニュー"""
        # キャラクターインベントリと宿屋倉庫から装備可能アイテムを検索
        equippable_items = self._get_equippable_items_for_character(character)
        
        if not equippable_items:
            self._show_dialog(
                "no_equippable_items_dialog",
                f"{character.name} の装備変更",
                "装備可能なアイテムがありません。\\n\\n"
                "商店で武器・防具を購入してください。"
            )
            return
        
        # 装備タイプ別メニュー
        equip_type_menu = UIMenu("equipment_type_menu", f"{character.name} - 装備タイプ選択")
        
        # アイテムタイプでグループ化
        weapons = [item for item in equippable_items if item[2].item_type.value == "weapon"]
        armor = [item for item in equippable_items if item[2].item_type.value == "armor"]
        
        if weapons:
            equip_type_menu.add_menu_item(
                f"武器 ({len(weapons)}個)",
                self._show_equipment_category_selection,
                [character, weapons, "weapon"]
            )
        
        if armor:
            equip_type_menu.add_menu_item(
                f"防具 ({len(armor)}個)",
                self._show_equipment_category_selection,
                [character, armor, "armor"]
            )
        
        equip_type_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._show_character_equipment_detail,
            [character]
        )
        
        self._show_submenu(equip_type_menu)
    
    def _get_equippable_items_for_character(self, character):
        """キャラクターが装備可能なアイテムを取得"""
        equippable_items = []
        
        # キャラクターインベントリから検索
        char_inventory = character.get_inventory()
        for i, slot in enumerate(char_inventory.slots):
            if not slot.is_empty():
                item = item_manager.get_item(slot.item_instance.item_id)
                if item and self._can_character_equip(character, item):
                    equippable_items.append(("character", i, item, slot.item_instance))
        
        # 宿屋倉庫から検索
        from src.overworld.inn_storage import inn_storage_manager
        storage = inn_storage_manager.get_storage()
        for slot_index, item_instance in storage.get_all_items():
            item = item_manager.get_item(item_instance.item_id)
            if item and self._can_character_equip(character, item):
                equippable_items.append(("storage", slot_index, item, item_instance))
        
        return equippable_items
    
    def _can_character_equip(self, character, item) -> bool:
        """キャラクターがアイテムを装備できるかチェック"""
        # アイテムタイプチェック
        if item.item_type.value not in ["weapon", "armor"]:
            return False
        
        # 職業制限チェック
        if hasattr(item, 'usable_classes') and item.usable_classes:
            if character.character_class not in item.usable_classes:
                return False
        
        return True
    
    def _show_equipment_category_selection(self, character, items, category):
        """装備カテゴリ選択表示"""
        category_menu = UIMenu("equipment_category_menu", f"{character.name} - {category}選択")
        
        for source, index, item, item_instance in items:
            source_text = "所持" if source == "character" else "倉庫"
            item_name = f"[{source_text}] {item.get_name()}"
            
            # アイテム詳細情報追加
            if item.item_type.value == "weapon" and hasattr(item, 'attack_power'):
                item_name += f" (攻撃力{item.attack_power})"
            elif item.item_type.value == "armor" and hasattr(item, 'defense'):
                item_name += f" (防御力{item.defense})"
            
            category_menu.add_menu_item(
                item_name,
                self._confirm_equipment_change,
                [character, source, index, item, item_instance]
            )
        
        category_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._show_equipment_equip_menu,
            [character]
        )
        
        self._show_submenu(category_menu)
    
    def _confirm_equipment_change(self, character, source, index, item, item_instance):
        """装備変更確認"""
        equipment = character.get_equipment()
        
        # 装備スロット決定
        if item.item_type.value == "weapon":
            slot_name = "weapon"
        elif item.item_type.value == "armor":
            slot_name = "armor"
        else:
            self._show_error_message("装備できないアイテムです")
            return
        
        confirm_info = f"【装備変更確認】\\n\\n"
        confirm_info += f"キャラクター: {character.name}\\n"
        confirm_info += f"新しい装備: {item.get_name()}\\n"
        
        # 現在の装備を確認
        current_equipment_name = self._get_equipment_name(equipment, slot_name)
        confirm_info += f"現在の装備: {current_equipment_name}\\n\\n"
        
        # ステータス比較
        if item.item_type.value == "weapon" and hasattr(item, 'attack_power'):
            confirm_info += f"攻撃力: {item.attack_power}\\n"
        elif item.item_type.value == "armor" and hasattr(item, 'defense'):
            confirm_info += f"防御力: {item.defense}\\n"
        
        confirm_info += "\\n装備を変更しますか？"
        
        self._show_dialog(
            "equipment_change_confirm_dialog",
            "装備変更確認",
            confirm_info,
            buttons=[
                {
                    'text': "装備する",
                    'command': lambda: self._execute_equipment_change(character, source, index, item, item_instance, slot_name)
                },
                {
                    'text': "キャンセル",
                    'command': self._close_dialog
                }
            ]
        )
    
    def _execute_equipment_change(self, character, source, index, item, item_instance, slot_name):
        """装備変更を実行"""
        self._close_dialog()
        
        try:
            equipment = character.get_equipment()
            
            # 現在の装備を外す（キャラクターインベントリに戻す）
            if hasattr(equipment, 'slots') and slot_name in equipment.slots and equipment.slots[slot_name]:
                current_item = equipment.slots[slot_name]
                char_inventory = character.get_inventory()
                if not char_inventory.add_item(current_item):
                    self._show_error_message("インベントリが満杯で装備を外せません")
                    return
            
            # 新しいアイテムを装備
            if source == "character":
                # キャラクターインベントリから取得
                char_inventory = character.get_inventory()
                removed_item = char_inventory.remove_item(index, 1)
            else:
                # 宿屋倉庫から取得
                from src.overworld.inn_storage import inn_storage_manager
                storage = inn_storage_manager.get_storage()
                removed_item = storage.remove_item(index, 1)
            
            if not removed_item:
                self._show_error_message("アイテムの取得に失敗しました")
                return
            
            # 装備セット
            if not hasattr(equipment, 'slots'):
                equipment.slots = {}
            equipment.slots[slot_name] = removed_item
            
            success_message = f"{character.name} が {item.get_name()} を装備しました。"
            self._show_dialog(
                "equipment_change_success_dialog",
                "装備変更完了",
                success_message
            )
            
            logger.info(f"{character.name} が {item.get_name()} を装備")
            
        except Exception as e:
            logger.error(f"装備変更エラー: {e}")
            self._show_error_message(f"装備変更に失敗しました: {str(e)}")
    
    def _show_equipment_unequip_menu(self, character):
        """装備解除メニュー"""
        equipment = character.get_equipment()
        
        # 装備中のアイテムを取得
        equipped_items = []
        slot_names = {
            'weapon': '武器',
            'armor': '防具',
            'accessory_1': 'アクセサリ1', 
            'accessory_2': 'アクセサリ2'
        }
        
        for slot_name, display_name in slot_names.items():
            if hasattr(equipment, 'slots') and slot_name in equipment.slots and equipment.slots[slot_name]:
                item_instance = equipment.slots[slot_name]
                item = item_manager.get_item(item_instance.item_id)
                if item:
                    equipped_items.append((slot_name, display_name, item, item_instance))
        
        if not equipped_items:
            self._show_dialog(
                "no_equipped_items_dialog",
                f"{character.name} の装備解除",
                "装備中のアイテムがありません。"
            )
            return
        
        # 装備解除選択メニュー
        unequip_menu = UIMenu("equipment_unequip_menu", f"{character.name} - 装備解除")
        
        for slot_name, display_name, item, item_instance in equipped_items:
            item_info = f"{display_name}: {item.get_name()}"
            unequip_menu.add_menu_item(
                item_info,
                self._confirm_equipment_unequip,
                [character, slot_name, display_name, item, item_instance]
            )
        
        unequip_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._show_character_equipment_detail,
            [character]
        )
        
        self._show_submenu(unequip_menu)
    
    def _confirm_equipment_unequip(self, character, slot_name, display_name, item, item_instance):
        """装備解除確認"""
        confirm_info = f"【装備解除確認】\\n\\n"
        confirm_info += f"キャラクター: {character.name}\\n"
        confirm_info += f"解除する装備: {display_name} - {item.get_name()}\\n\\n"
        confirm_info += "この装備を解除してインベントリに戻しますか？"
        
        self._show_dialog(
            "equipment_unequip_confirm_dialog",
            "装備解除確認",
            confirm_info,
            buttons=[
                {
                    'text': "解除する",
                    'command': lambda: self._execute_equipment_unequip(character, slot_name, display_name, item, item_instance)
                },
                {
                    'text': "キャンセル",
                    'command': self._close_dialog
                }
            ]
        )
    
    def _execute_equipment_unequip(self, character, slot_name, display_name, item, item_instance):
        """装備解除を実行"""
        self._close_dialog()
        
        try:
            equipment = character.get_equipment()
            char_inventory = character.get_inventory()
            
            # インベントリに空きがあるかチェック
            if not char_inventory.add_item(item_instance):
                self._show_error_message("インベントリが満杯で装備を外せません")
                return
            
            # 装備スロットをクリア
            if hasattr(equipment, 'slots') and slot_name in equipment.slots:
                equipment.slots[slot_name] = None
            
            success_message = f"{character.name} の {display_name} ({item.get_name()}) を解除しました。\\n\\n"
            success_message += "アイテムはインベントリに戻されました。"
            
            self._show_dialog(
                "equipment_unequip_success_dialog",
                "装備解除完了",
                success_message
            )
            
            logger.info(f"{character.name} が {item.get_name()} を解除")
            
        except Exception as e:
            logger.error(f"装備解除エラー: {e}")
            self._show_error_message(f"装備解除に失敗しました: {str(e)}")
    
    def _show_equipment_comparison(self, character):
        """装備比較機能"""
        comparison_info = f"【{character.name} の装備比較】\\n\\n"
        comparison_info += "現在の装備と新しいアイテムの\\n"
        comparison_info += "ステータスを比較して、\\n"
        comparison_info += "最適な装備を選択できます。\\n\\n"
        comparison_info += "※この機能は次の段階で実装予定です"
        
        self._show_dialog(
            "equipment_comparison_dialog",
            f"{character.name} の装備比較",
            comparison_info
        )
    
    def _get_equipment_name(self, equipment, slot_name: str) -> str:
        """装備スロットのアイテム名を取得"""
        try:
            if hasattr(equipment, 'slots') and slot_name in equipment.slots:
                item_instance = equipment.slots[slot_name]
                if item_instance:
                    item = item_manager.get_item(item_instance.item_id)
                    if item:
                        return item.get_name()
            return "未装備"
        except:
            return "情報取得不可"
    
    def _show_submenu(self, submenu: UIMenu):
        """サブメニューを表示"""
        # メインメニューを隠す
        if self.main_menu:
            ui_manager.hide_menu(self.main_menu.menu_id)
        
        ui_manager.add_menu(submenu)
        ui_manager.show_menu(submenu.menu_id, modal=True)
    
    def _back_to_main_menu_from_submenu(self, submenu: UIMenu):
        """サブメニューからメインメニューに戻る"""
        ui_manager.hide_menu(submenu.menu_id)
        
        
        if self.main_menu:
            ui_manager.show_menu(self.main_menu.menu_id)
