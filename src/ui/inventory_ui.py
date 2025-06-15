"""インベントリUI管理システム"""

from typing import Dict, List, Optional, Any, Tuple, Callable
from enum import Enum

from src.ui.base_ui import UIMenu, UIDialog, ui_manager
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
    """インベントリUI管理クラス"""
    
    def __init__(self):
        self.current_party: Optional[Party] = None
        self.current_inventory: Optional[Inventory] = None
        self.current_character: Optional[Character] = None
        self.selected_slot: Optional[int] = None
        self.transfer_source: Optional[Tuple[Inventory, int]] = None
        
        logger.info("InventoryUIを初期化しました")
    
    def set_party(self, party: Party):
        """パーティを設定"""
        self.current_party = party
        logger.debug(f"パーティを設定: {party.name}")
    
    def show_party_inventory_menu(self, party: Party):
        """パーティインベントリメニューを表示"""
        self.set_party(party)
        
        main_menu = UIMenu("party_inventory_main", "パーティインベントリ")
        
        # パーティ共有インベントリ
        main_menu.add_menu_item(
            "パーティ共有アイテム",
            self._show_party_shared_inventory
        )
        
        # 各キャラクターのインベントリ
        for character in party.get_all_characters():
            char_info = f"{character.name}のアイテム"
            main_menu.add_menu_item(
                char_info,
                self._show_character_inventory,
                [character]
            )
        
        # アイテム整理
        main_menu.add_menu_item(
            "アイテム整理",
            self._show_inventory_management_menu
        )
        
        main_menu.add_menu_item(
            config_manager.get_text("menu.close"),
            self._close_inventory_ui
        )
        
        ui_manager.register_element(main_menu)
        ui_manager.show_element(main_menu.element_id, modal=True)
        
        logger.info("パーティインベントリメニューを表示")
    
    def _show_party_shared_inventory(self):
        """パーティ共有インベントリを表示"""
        if not self.current_party:
            return
        
        party_inventory = self.current_party.get_party_inventory()
        self._show_inventory_contents(
            party_inventory, 
            "パーティ共有アイテム",
            inventory_type="party"
        )
    
    def _show_character_inventory(self, character: Character):
        """キャラクターインベントリを表示"""
        self.current_character = character
        character_inventory = character.get_inventory()
        self._show_inventory_contents(
            character_inventory,
            f"{character.name}のアイテム",
            inventory_type="character"
        )
    
    def _show_inventory_contents(self, inventory: Inventory, title: str, inventory_type: str):
        """インベントリ内容を表示"""
        self.current_inventory = inventory
        
        inventory_menu = UIMenu(f"inventory_contents_{inventory_type}", title)
        
        # アイテムスロットを表示
        for i, slot in enumerate(inventory.slots):
            if slot.is_empty():
                slot_text = f"[{i+1:2d}] (空)"
                inventory_menu.add_menu_item(
                    slot_text,
                    self._show_empty_slot_options,
                    [i]
                )
            else:
                item = item_manager.get_item(slot.item_instance.item_id)
                if item:
                    # アイテム名（鑑定状態を考慮）
                    if slot.item_instance.identified:
                        item_name = item.get_name()
                    else:
                        item_name = f"未鑑定の{item.item_type.value}"
                    
                    # 数量表示
                    if slot.item_instance.quantity > 1:
                        slot_text = f"[{i+1:2d}] {item_name} x{slot.item_instance.quantity}"
                    else:
                        slot_text = f"[{i+1:2d}] {item_name}"
                    
                    inventory_menu.add_menu_item(
                        slot_text,
                        self._show_item_options,
                        [i, slot.item_instance, item]
                    )
        
        # インベントリ情報
        used_slots = len([slot for slot in inventory.slots if not slot.is_empty()])
        inventory_info = f"使用中: {used_slots}/{inventory.max_slots}"
        
        inventory_menu.add_menu_item(
            f"--- {inventory_info} ---",
            lambda: None  # 情報表示のみ
        )
        
        inventory_menu.add_menu_item(
            "戻る",
            self._back_to_main_inventory_menu
        )
        
        ui_manager.register_element(inventory_menu)
        ui_manager.show_element(inventory_menu.element_id, modal=True)
    
    def _show_item_options(self, slot_index: int, item_instance: ItemInstance, item: Item):
        """アイテムオプションメニューを表示"""
        self.selected_slot = slot_index
        
        options_menu = UIMenu("item_options", f"{item.get_name()} の操作")
        
        # アイテム詳細表示
        options_menu.add_menu_item(
            "詳細を見る",
            self._show_item_details,
            [item_instance, item]
        )
        
        # 使用（消耗品のみ）
        if item.is_consumable() and item_instance.identified:
            options_menu.add_menu_item(
                "使用する",
                self._show_item_usage_menu,
                [item_instance, item]
            )
        
        # 装備（装備品のみ、キャラクターインベントリから）
        if (item.is_weapon() or item.is_armor()) and self.current_character:
            if item_instance.identified:
                options_menu.add_menu_item(
                    "装備する",
                    self._equip_item,
                    [item_instance, item]
                )
        
        # 移動
        options_menu.add_menu_item(
            "別の場所に移動",
            self._show_transfer_menu,
            [item_instance, item]
        )
        
        # 破棄
        options_menu.add_menu_item(
            "破棄する",
            self._show_drop_confirmation,
            [item_instance, item]
        )
        
        options_menu.add_menu_item(
            "戻る",
            self._back_to_inventory_contents
        )
        
        ui_manager.register_element(options_menu)
        ui_manager.show_element(options_menu.element_id, modal=True)
    
    def _show_empty_slot_options(self, slot_index: int):
        """空スロットオプションを表示"""
        self.selected_slot = slot_index
        
        options_menu = UIMenu("empty_slot_options", "空スロット")
        
        # 転送先として設定（転送モード中の場合）
        if self.transfer_source:
            options_menu.add_menu_item(
                "ここに移動する",
                self._execute_transfer,
                [slot_index]
            )
        
        options_menu.add_menu_item(
            "戻る",
            self._back_to_inventory_contents
        )
        
        ui_manager.register_element(options_menu)
        ui_manager.show_element(options_menu.element_id, modal=True)
    
    def _show_item_details(self, item_instance: ItemInstance, item: Item):
        """アイテム詳細を表示"""
        if not item_instance.identified:
            details = f"【未鑑定のアイテム】\n\n"
            details += f"種類: {item.item_type.value}\n"
            details += f"数量: {item_instance.quantity}\n"
            details += f"重量: {item.weight}\n\n"
            details += "このアイテムは鑑定が必要です。\n"
            details += "魔術師ギルドで鑑定してください。"
        else:
            details = f"【{item.get_name()}】\n\n"
            details += f"説明: {item.get_description()}\n"
            details += f"種類: {item.item_type.value}\n"
            details += f"数量: {item_instance.quantity}\n"
            details += f"重量: {item.weight}\n"
            details += f"価値: {item.price}G\n"
            
            if item.is_weapon():
                details += f"攻撃力: +{item.get_attack_power()}\n"
                if item.get_attribute():
                    details += f"属性: {item.get_attribute()}\n"
            elif item.is_armor():
                details += f"防御力: +{item.get_defense()}\n"
            elif item.is_consumable():
                details += f"効果: {item.get_effect_type()}\n"
                if item.get_effect_value() > 0:
                    details += f"効果値: {item.get_effect_value()}\n"
            
            if item.usable_classes:
                details += f"使用可能クラス: {', '.join(item.usable_classes)}\n"
            
            details += f"\n希少度: {item.rarity.value}"
        
        dialog = UIDialog(
            "item_detail_dialog",
            "アイテム詳細",
            details,
            buttons=[
                {
                    'text': "閉じる",
                    'command': self._close_dialog
                }
            ]
        )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)
    
    def _show_item_usage_menu(self, item_instance: ItemInstance, item: Item):
        """アイテム使用メニューを表示"""
        if not self.current_party:
            return
        
        usage_menu = UIMenu("item_usage_menu", f"{item.get_name()} を使用")
        
        # 使用可能性をチェック
        usage_info = item_usage_manager.get_item_usage_info(item)
        if not usage_info['usable']:
            self._show_error_message(usage_info.get('reason', 'このアイテムは使用できません'))
            return
        
        # 対象が必要な場合
        if usage_info['target_required']:
            usage_menu.add_menu_item(
                "使用対象を選択:",
                lambda: None  # ヘッダー
            )
            
            for character in self.current_party.get_all_characters():
                char_status = "生存" if character.is_alive() else "死亡"
                target_text = f"{character.name} ({char_status})"
                
                usage_menu.add_menu_item(
                    target_text,
                    self._use_item_on_target,
                    [item_instance, character]
                )
        else:
            # 対象不要の場合（全体効果など）
            usage_menu.add_menu_item(
                "使用する",
                self._use_item_on_target,
                [item_instance, None]
            )
        
        usage_menu.add_menu_item(
            "キャンセル",
            self._back_to_item_options
        )
        
        ui_manager.register_element(usage_menu)
        ui_manager.show_element(usage_menu.element_id, modal=True)
    
    def _use_item_on_target(self, item_instance: ItemInstance, target: Optional[Character]):
        """アイテムを指定対象に使用"""
        if not self.current_character:
            self._show_error_message("使用者が設定されていません")
            return
        
        # アイテム使用
        result, message, results = item_usage_manager.use_item(
            item_instance, self.current_character, target, self.current_party
        )
        
        # 結果を表示
        if result == UsageResult.SUCCESS:
            self._show_success_message(message)
        else:
            self._show_error_message(message)
        
        # UIを更新（アイテム数量が変化した場合）
        self._refresh_current_inventory()
    
    def _equip_item(self, item_instance: ItemInstance, item: Item):
        """アイテムを装備"""
        if not self.current_character:
            return
        
        equipment = self.current_character.get_equipment()
        
        # 装備スロットを決定
        if item.is_weapon():
            slot_name = "weapon"
        elif item.is_armor():
            slot_name = "armor"
        else:
            self._show_error_message("このアイテムは装備できません")
            return
        
        from src.equipment.equipment import EquipmentSlot
        equipment_slot = EquipmentSlot(slot_name)
        
        # 装備試行
        success, reason, replaced_item = equipment.equip_item(
            item_instance, equipment_slot, self.current_character.character_class
        )
        
        if success:
            # インベントリからアイテムを除去
            if self.current_inventory and self.selected_slot is not None:
                self.current_inventory.remove_item(self.selected_slot, 1)
            
            # 置き換えられたアイテムがあればインベントリに追加
            if replaced_item:
                self.current_inventory.add_item(replaced_item)
            
            self._show_success_message(f"{item.get_name()}を装備しました")
            self._refresh_current_inventory()
        else:
            self._show_error_message(reason)
    
    def _show_transfer_menu(self, item_instance: ItemInstance, item: Item):
        """アイテム移動メニューを表示"""
        if not self.current_party:
            return
        
        # 転送元を設定
        self.transfer_source = (self.current_inventory, self.selected_slot)
        
        transfer_menu = UIMenu("transfer_menu", f"{item.get_name()} の移動先")
        
        # パーティインベントリ（現在のインベントリでない場合）
        party_inventory = self.current_party.get_party_inventory()
        if self.current_inventory != party_inventory:
            transfer_menu.add_menu_item(
                "パーティ共有アイテムへ",
                self._transfer_to_inventory,
                [party_inventory]
            )
        
        # 各キャラクターのインベントリ
        for character in self.current_party.get_all_characters():
            char_inventory = character.get_inventory()
            if self.current_inventory != char_inventory:
                transfer_menu.add_menu_item(
                    f"{character.name}へ",
                    self._transfer_to_inventory,
                    [char_inventory]
                )
        
        transfer_menu.add_menu_item(
            "キャンセル",
            self._cancel_transfer
        )
        
        ui_manager.register_element(transfer_menu)
        ui_manager.show_element(transfer_menu.element_id, modal=True)
    
    def _transfer_to_inventory(self, target_inventory: Inventory):
        """指定インベントリに転送"""
        if not self.transfer_source:
            return
        
        source_inventory, source_slot = self.transfer_source
        
        # アイテムを取得
        source_slot_obj = source_inventory.slots[source_slot]
        if source_slot_obj.is_empty():
            self._show_error_message("転送するアイテムがありません")
            return
        
        item_instance = source_slot_obj.item_instance
        
        # 転送先に空きがあるかチェック
        if not target_inventory.can_add_item(item_instance):
            self._show_error_message("転送先に空きがありません")
            return
        
        # アイテム転送
        success = inventory_manager.transfer_item(
            source_inventory, source_slot,
            target_inventory, item_instance.quantity
        )
        
        if success:
            self._show_success_message("アイテムを移動しました")
            self._refresh_current_inventory()
        else:
            self._show_error_message("アイテムの移動に失敗しました")
        
        self._cancel_transfer()
    
    def _execute_transfer(self, target_slot: int):
        """転送を実行"""
        if not self.transfer_source or not self.current_inventory:
            return
        
        source_inventory, source_slot = self.transfer_source
        
        # 同じインベントリ内での移動
        if source_inventory == self.current_inventory:
            success = self.current_inventory.move_item(source_slot, target_slot)
            if success:
                self._show_success_message("アイテムを移動しました")
                self._refresh_current_inventory()
            else:
                self._show_error_message("アイテムの移動に失敗しました")
        
        self._cancel_transfer()
    
    def _cancel_transfer(self):
        """転送をキャンセル"""
        self.transfer_source = None
        self._back_to_item_options()
    
    def _show_drop_confirmation(self, item_instance: ItemInstance, item: Item):
        """破棄確認ダイアログを表示"""
        confirm_text = f"{item.get_name()} を破棄しますか？\n\n"
        if item_instance.quantity > 1:
            confirm_text += f"数量: {item_instance.quantity}個\n"
        confirm_text += "一度破棄したアイテムは元に戻せません。"
        
        dialog = UIDialog(
            "drop_confirmation_dialog",
            "アイテム破棄確認",
            confirm_text,
            buttons=[
                {
                    'text': "破棄する",
                    'command': lambda: self._drop_item(item_instance, item)
                },
                {
                    'text': "キャンセル",
                    'command': self._close_dialog
                }
            ]
        )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)
    
    def _drop_item(self, item_instance: ItemInstance, item: Item):
        """アイテムを破棄"""
        if self.current_inventory and self.selected_slot is not None:
            self.current_inventory.remove_item(self.selected_slot, item_instance.quantity)
            self._show_success_message(f"{item.get_name()}を破棄しました")
            self._refresh_current_inventory()
        
        self._close_dialog()
    
    def _show_inventory_management_menu(self):
        """インベントリ管理メニューを表示"""
        if not self.current_party:
            return
        
        management_menu = UIMenu("inventory_management", "アイテム整理")
        
        management_menu.add_menu_item(
            "パーティアイテムを整理",
            self._sort_party_inventory
        )
        
        for character in self.current_party.get_all_characters():
            management_menu.add_menu_item(
                f"{character.name}のアイテムを整理",
                self._sort_character_inventory,
                [character]
            )
        
        management_menu.add_menu_item(
            "アイテム統計を表示",
            self._show_inventory_statistics
        )
        
        management_menu.add_menu_item(
            "戻る",
            self._back_to_main_inventory_menu
        )
        
        ui_manager.register_element(management_menu)
        ui_manager.show_element(management_menu.element_id, modal=True)
    
    def _sort_party_inventory(self):
        """パーティインベントリを整理"""
        if not self.current_party:
            return
        
        party_inventory = self.current_party.get_party_inventory()
        party_inventory.sort_items()
        
        self._show_success_message("パーティアイテムを整理しました")
        logger.info("パーティインベントリを整理")
    
    def _sort_character_inventory(self, character: Character):
        """キャラクターインベントリを整理"""
        character_inventory = character.get_inventory()
        character_inventory.sort_items()
        
        self._show_success_message(f"{character.name}のアイテムを整理しました")
        logger.info(f"キャラクターインベントリを整理: {character.name}")
    
    def _show_inventory_statistics(self):
        """インベントリ統計を表示"""
        if not self.current_party:
            return
        
        stats_text = "【アイテム統計】\n\n"
        
        # パーティインベントリ
        party_inventory = self.current_party.get_party_inventory()
        party_used = len([slot for slot in party_inventory.slots if not slot.is_empty()])
        stats_text += f"パーティ共有: {party_used}/{party_inventory.max_slots}\n"
        
        # 各キャラクター
        for character in self.current_party.get_all_characters():
            char_inventory = character.get_inventory()
            char_used = len([slot for slot in char_inventory.slots if not slot.is_empty()])
            stats_text += f"{character.name}: {char_used}/{char_inventory.max_slots}\n"
        
        # 総重量（実装されていれば）
        stats_text += "\n※ 重量制限システムは今後実装予定です"
        
        dialog = UIDialog(
            "inventory_stats_dialog",
            "インベントリ統計",
            stats_text,
            buttons=[
                {
                    'text': "閉じる",
                    'command': self._close_dialog
                }
            ]
        )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)
    
    def _refresh_current_inventory(self):
        """現在のインベントリ表示を更新"""
        # 実装簡略化のため、メニューを閉じて再表示
        self._back_to_inventory_contents()
    
    def show(self):
        """インベントリUIを表示"""
        if self.current_party:
            self.show_party_inventory_menu(self.current_party)
        else:
            logger.warning("パーティが設定されていません")
    
    def hide(self):
        """インベントリUIを非表示"""
        # 現在開いているメニューを閉じる
        try:
            ui_manager.hide_element("party_inventory_main")
        except:
            pass
        logger.debug("インベントリUIを非表示にしました")
    
    def destroy(self):
        """インベントリUIを破棄"""
        self.hide()
        self.current_party = None
        self.current_inventory = None
        self.current_character = None
        self.selected_slot = None
        self.transfer_source = None
        logger.debug("InventoryUIを破棄しました")
    
    def _back_to_main_inventory_menu(self):
        """メインインベントリメニューに戻る"""
        if self.current_party:
            self.show_party_inventory_menu(self.current_party)
    
    def _back_to_inventory_contents(self):
        """インベントリ内容表示に戻る"""
        if self.current_inventory:
            if self.current_character:
                self._show_character_inventory(self.current_character)
            else:
                self._show_party_shared_inventory()
    
    def _back_to_item_options(self):
        """アイテムオプションに戻る"""
        # 簡略化のため、インベントリ内容に戻る
        self._back_to_inventory_contents()
    
    def _close_inventory_ui(self):
        """インベントリUIを閉じる"""
        ui_manager.hide_all_elements()
        logger.info("インベントリUIを閉じました")
    
    def _close_dialog(self):
        """ダイアログを閉じる"""
        # すべてのダイアログを閉じる（簡略化）
        ui_manager.hide_all_elements()
    
    def _show_success_message(self, message: str):
        """成功メッセージを表示"""
        dialog = UIDialog(
            "success_dialog",
            "成功",
            message,
            buttons=[
                {
                    'text': "OK",
                    'command': self._close_dialog
                }
            ]
        )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)
    
    def _show_error_message(self, message: str):
        """エラーメッセージを表示"""
        dialog = UIDialog(
            "error_dialog",
            "エラー",
            message,
            buttons=[
                {
                    'text': "OK",
                    'command': self._close_dialog
                }
            ]
        )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)


# グローバルインスタンス
inventory_ui = InventoryUI()