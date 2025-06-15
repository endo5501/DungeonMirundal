"""装備UI管理システム"""

from typing import Dict, List, Optional, Any, Tuple, Callable
from enum import Enum

from src.ui.base_ui import UIElement, UIButton, UIText, UIMenu, UIDialog, UIState, ui_manager
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
    """装備UI管理クラス"""
    
    def __init__(self):
        self.current_party: Optional[Party] = None
        self.current_character: Optional[Character] = None
        self.current_equipment: Optional[Equipment] = None
        self.current_mode = EquipmentUIMode.OVERVIEW
        self.selected_slot: Optional[EquipmentSlot] = None
        self.comparison_item: Optional[ItemInstance] = None
        
        # UI状態
        self.is_open = False
        self.callback_on_close: Optional[Callable] = None
        
        logger.info("EquipmentUIを初期化しました")
    
    def set_party(self, party: Party):
        """パーティを設定"""
        self.current_party = party
        logger.debug(f"パーティを設定: {party.name}")
    
    def show_party_equipment_menu(self, party: Party):
        """パーティ装備メニューを表示"""
        self.set_party(party)
        self.current_mode = EquipmentUIMode.OVERVIEW
        
        main_menu = UIMenu("party_equipment_main", "パーティ装備")
        
        # 各キャラクターの装備
        for character in party.get_all_characters():
            equipment = character.get_equipment()
            summary = equipment.get_equipment_summary()
            equipped_count = summary['equipped_count']
            
            char_info = f"{character.name} ({equipped_count}/4)"
            main_menu.add_menu_item(
                char_info,
                self._show_character_equipment,
                [character]
            )
        
        # パーティ装備統計
        main_menu.add_menu_item(
            "パーティ装備統計",
            self._show_party_equipment_stats
        )
        
        main_menu.add_menu_item(
            config_manager.get_text("menu.close"),
            self._close_equipment_ui
        )
        
        ui_manager.register_element(main_menu)
        ui_manager.show_element(main_menu.element_id, modal=True)
        self.is_open = True
        
        logger.info("パーティ装備メニューを表示")
    
    def _show_character_equipment(self, character: Character):
        """キャラクター装備画面を表示"""
        self.current_character = character
        self.current_equipment = character.get_equipment()
        
        equipment_menu = UIMenu("character_equipment", f"{character.name}の装備")
        
        # 装備スロット表示
        for slot in EquipmentSlot:
            item_instance = self.current_equipment.get_equipped_item(slot)
            
            if item_instance:
                item = item_manager.get_item(item_instance.item_id)
                if item:
                    if item_instance.identified:
                        item_name = item.get_name()
                        condition_text = f" ({int(item_instance.condition * 100)}%)"
                    else:
                        item_name = f"未鑑定の{item.item_type.value}"
                        condition_text = ""
                    
                    slot_text = f"{self._get_slot_name(slot)}: {item_name}{condition_text}"
                else:
                    slot_text = f"{self._get_slot_name(slot)}: 不明なアイテム"
            else:
                slot_text = f"{self._get_slot_name(slot)}: (なし)"
            
            equipment_menu.add_menu_item(
                slot_text,
                self._show_slot_options,
                [slot]
            )
        
        # 装備ボーナス表示
        equipment_menu.add_menu_item(
            "装備ボーナス詳細",
            self._show_equipment_bonus
        )
        
        # 装備効果確認
        equipment_menu.add_menu_item(
            "装備効果確認",
            self._show_equipment_effects
        )
        
        equipment_menu.add_menu_item(
            "戻る",
            self._back_to_main_menu
        )
        
        ui_manager.register_element(equipment_menu)
        ui_manager.show_element(equipment_menu.element_id, modal=True)
    
    def _show_slot_options(self, slot: EquipmentSlot):
        """スロットオプションメニューを表示"""
        self.selected_slot = slot
        
        options_menu = UIMenu("slot_options", f"{self._get_slot_name(slot)}の操作")
        
        item_instance = self.current_equipment.get_equipped_item(slot)
        
        if item_instance:
            # 装備中の場合
            item = item_manager.get_item(item_instance.item_id)
            if item:
                options_menu.add_menu_item(
                    "アイテム詳細",
                    self._show_equipped_item_details,
                    [item_instance, item]
                )
                
                options_menu.add_menu_item(
                    "装備を外す",
                    self._unequip_item,
                    [slot]
                )
        
        # 装備変更
        options_menu.add_menu_item(
            "装備を変更する",
            self._show_equipment_selection,
            [slot]
        )
        
        options_menu.add_menu_item(
            "戻る",
            self._back_to_character_equipment
        )
        
        ui_manager.register_element(options_menu)
        ui_manager.show_element(options_menu.element_id, modal=True)
    
    def _show_equipment_selection(self, slot: EquipmentSlot):
        """装備選択メニューを表示"""
        if not self.current_character:
            return
        
        selection_menu = UIMenu("equipment_selection", f"{self._get_slot_name(slot)}に装備するアイテム")
        
        # キャラクターのインベントリから装備可能なアイテムを取得
        inventory = self.current_character.get_inventory()
        suitable_items = []
        
        for i, inventory_slot in enumerate(inventory.slots):
            if not inventory_slot.is_empty():
                item_instance = inventory_slot.item_instance
                item = item_manager.get_item(item_instance.item_id)
                
                if item and self._can_equip_in_slot(item, slot):
                    can_equip, reason = self.current_equipment.can_equip_item(
                        item_instance, slot, self.current_character.character_class.value
                    )
                    
                    if can_equip:
                        suitable_items.append((i, item_instance, item))
        
        if not suitable_items:
            selection_menu.add_menu_item(
                "装備可能なアイテムがありません",
                lambda: None
            )
        else:
            for inventory_index, item_instance, item in suitable_items:
                if item_instance.identified:
                    item_name = item.get_name()
                    # 装備効果プレビュー
                    preview_text = self._get_equipment_preview(item, item_instance, slot)
                    item_text = f"{item_name} {preview_text}"
                else:
                    item_text = f"未鑑定の{item.item_type.value}"
                
                selection_menu.add_menu_item(
                    item_text,
                    self._equip_item_from_inventory,
                    [item_instance, slot, inventory_index]
                )
        
        selection_menu.add_menu_item(
            "キャンセル",
            self._back_to_slot_options
        )
        
        ui_manager.register_element(selection_menu)
        ui_manager.show_element(selection_menu.element_id, modal=True)
    
    def _equip_item_from_inventory(self, item_instance: ItemInstance, slot: EquipmentSlot, inventory_index: int):
        """インベントリからアイテムを装備"""
        if not self.current_character or not self.current_equipment:
            return
        
        # 装備試行
        success, reason, replaced_item = self.current_equipment.equip_item(
            item_instance, slot, self.current_character.character_class.value
        )
        
        if success:
            # インベントリからアイテムを除去
            inventory = self.current_character.get_inventory()
            inventory.remove_item(inventory_index, 1)
            
            # 置き換えられたアイテムがあればインベントリに追加
            if replaced_item:
                if not inventory.add_item(replaced_item):
                    # インベントリに空きがない場合の処理
                    self._show_message("インベントリに空きがないため、外した装備が失われました")
            
            item = item_manager.get_item(item_instance.item_id)
            item_name = item.get_name() if item and item_instance.identified else "アイテム"
            self._show_message(f"{item_name}を装備しました")
            
            # キャラクターステータスを更新
            self.current_character.update_derived_stats()
            
            # 画面を更新
            self._back_to_character_equipment()
        else:
            self._show_message(f"装備に失敗: {reason}")
    
    def _unequip_item(self, slot: EquipmentSlot):
        """アイテムの装備を解除"""
        if not self.current_character or not self.current_equipment:
            return
        
        item_instance = self.current_equipment.unequip_item(slot)
        
        if item_instance:
            # インベントリに追加
            inventory = self.current_character.get_inventory()
            if inventory.add_item(item_instance):
                item = item_manager.get_item(item_instance.item_id)
                item_name = item.get_name() if item and item_instance.identified else "アイテム"
                self._show_message(f"{item_name}の装備を解除しました")
                
                # キャラクターステータスを更新
                self.current_character.update_derived_stats()
                
                # 画面を更新
                self._back_to_character_equipment()
            else:
                # インベントリに空きがない場合、装備を戻す
                self.current_equipment.equipped_items[slot] = item_instance
                self._show_message("インベントリに空きがありません")
    
    def _show_equipped_item_details(self, item_instance: ItemInstance, item: Item):
        """装備中アイテムの詳細を表示"""
        if not item_instance.identified:
            details = f"【未鑑定のアイテム】\\n\\n"
            details += f"種類: {item.item_type.value}\\n"
            details += f"状態: {int(item_instance.condition * 100)}%\\n\\n"
            details += "このアイテムは鑑定が必要です。"
        else:
            details = f"【{item.get_name()}】\\n\\n"
            details += f"説明: {item.get_description()}\\n"
            details += f"種類: {item.item_type.value}\\n"
            details += f"状態: {int(item_instance.condition * 100)}%\\n"
            details += f"重量: {item.weight}\\n"
            details += f"価値: {item.price}G\\n\\n"
            
            # 装備効果
            if item.is_weapon():
                attack_power = int(item.get_attack_power() * item_instance.condition)
                details += f"攻撃力: +{attack_power}\\n"
                if item.get_attribute():
                    details += f"属性: {item.get_attribute()}\\n"
            elif item.is_armor():
                defense = int(item.get_defense() * item_instance.condition)
                details += f"防御力: +{defense}\\n"
            
            # 追加ボーナス
            bonuses = item.item_data.get('bonuses', {})
            if bonuses:
                details += "\\n追加効果:\\n"
                for stat, value in bonuses.items():
                    if value > 0:
                        stat_name = self._get_stat_name(stat)
                        details += f"{stat_name}: +{value}\\n"
            
            if item.usable_classes:
                details += f"\\n使用可能クラス: {', '.join(item.usable_classes)}"
        
        dialog = UIDialog(
            "equipped_item_detail",
            "装備詳細",
            details,
            buttons=[
                {"text": "閉じる", "command": self._close_dialog}
            ]
        )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)
    
    def _show_equipment_bonus(self):
        """装備ボーナス詳細を表示"""
        if not self.current_equipment:
            return
        
        bonus = self.current_equipment.calculate_equipment_bonus()
        
        details = "【装備ボーナス合計】\\n\\n"
        details += f"筋力: +{bonus.strength}\\n"
        details += f"敏捷性: +{bonus.agility}\\n"
        details += f"知力: +{bonus.intelligence}\\n"
        details += f"信仰: +{bonus.faith}\\n"
        details += f"運: +{bonus.luck}\\n\\n"
        details += f"攻撃力: +{bonus.attack_power}\\n"
        details += f"防御力: +{bonus.defense}\\n"
        details += f"魔法力: +{bonus.magic_power}\\n"
        details += f"魔法抵抗: +{bonus.magic_resistance}\\n\\n"
        details += f"装備重量: {self.current_equipment.get_total_weight():.1f}kg"
        
        dialog = UIDialog(
            "equipment_bonus_detail",
            "装備ボーナス",
            details,
            buttons=[
                {"text": "閉じる", "command": self._close_dialog}
            ]
        )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)
    
    def _show_equipment_effects(self):
        """装備効果確認を表示"""
        if not self.current_character or not self.current_equipment:
            return
        
        # 装備前後のステータス比較
        original_stats = self.current_character.get_base_stats()
        current_stats = self.current_character.get_derived_stats()
        equipment_bonus = self.current_equipment.calculate_equipment_bonus()
        
        details = "【装備効果確認】\\n\\n"
        details += "ベース → 装備込み (装備効果)\\n\\n"
        
        # 基本ステータス
        details += f"筋力: {original_stats.strength} → {current_stats.strength} (+{equipment_bonus.strength})\\n"
        details += f"敏捷性: {original_stats.agility} → {current_stats.agility} (+{equipment_bonus.agility})\\n"
        details += f"知力: {original_stats.intelligence} → {current_stats.intelligence} (+{equipment_bonus.intelligence})\\n"
        details += f"信仰: {original_stats.faith} → {current_stats.faith} (+{equipment_bonus.faith})\\n"
        details += f"運: {original_stats.luck} → {current_stats.luck} (+{equipment_bonus.luck})\\n\\n"
        
        # 戦闘ステータス
        details += f"攻撃力: {current_stats.attack_power - equipment_bonus.attack_power} → {current_stats.attack_power} (+{equipment_bonus.attack_power})\\n"
        details += f"防御力: {current_stats.defense - equipment_bonus.defense} → {current_stats.defense} (+{equipment_bonus.defense})\\n"
        details += f"魔法力: {current_stats.magic_power - equipment_bonus.magic_power} → {current_stats.magic_power} (+{equipment_bonus.magic_power})\\n"
        details += f"魔法抵抗: {current_stats.magic_resistance - equipment_bonus.magic_resistance} → {current_stats.magic_resistance} (+{equipment_bonus.magic_resistance})"
        
        dialog = UIDialog(
            "equipment_effects_detail",
            "装備効果確認",
            details,
            buttons=[
                {"text": "閉じる", "command": self._close_dialog}
            ]
        )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)
    
    def _show_party_equipment_stats(self):
        """パーティ装備統計を表示"""
        if not self.current_party:
            return
        
        stats_text = "【パーティ装備統計】\\n\\n"
        
        total_equipped = 0
        total_slots = 0
        total_weight = 0.0
        total_value = 0
        
        for character in self.current_party.get_all_characters():
            equipment = character.get_equipment()
            summary = equipment.get_equipment_summary()
            
            total_equipped += summary['equipped_count']
            total_slots += len(EquipmentSlot)
            total_weight += summary['total_weight']
            
            # アイテム価値計算
            for item_instance in equipment.get_all_equipped_items().values():
                if item_instance:
                    item = item_manager.get_item(item_instance.item_id)
                    if item:
                        total_value += item.price
        
        stats_text += f"装備率: {total_equipped}/{total_slots} ({int(total_equipped/total_slots*100)}%)\\n"
        stats_text += f"総重量: {total_weight:.1f}kg\\n"
        stats_text += f"総価値: {total_value}G\\n\\n"
        
        # キャラクター別詳細
        stats_text += "【キャラクター別】\\n"
        for character in self.current_party.get_all_characters():
            equipment = character.get_equipment()
            summary = equipment.get_equipment_summary()
            stats_text += f"{character.name}: {summary['equipped_count']}/4 ({summary['total_weight']:.1f}kg)\\n"
        
        dialog = UIDialog(
            "party_equipment_stats",
            "パーティ装備統計",
            stats_text,
            buttons=[
                {"text": "閉じる", "command": self._close_dialog}
            ]
        )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)
    
    def _can_equip_in_slot(self, item: Item, slot: EquipmentSlot) -> bool:
        """アイテムがスロットに装備可能かチェック"""
        if slot == EquipmentSlot.WEAPON:
            return item.is_weapon()
        elif slot == EquipmentSlot.ARMOR:
            return item.is_armor()
        elif slot in [EquipmentSlot.ACCESSORY_1, EquipmentSlot.ACCESSORY_2]:
            # 暫定的にTREASUREをアクセサリとして扱う
            return item.item_type.value == "treasure"
        return False
    
    def _get_equipment_preview(self, item: Item, item_instance: ItemInstance, slot: EquipmentSlot) -> str:
        """装備効果プレビューを取得"""
        if not item_instance.identified:
            return ""
        
        preview = ""
        
        if item.is_weapon():
            attack_power = int(item.get_attack_power() * item_instance.condition)
            current_item = self.current_equipment.get_equipped_item(slot)
            
            if current_item:
                current_attack = 0
                current_item_data = item_manager.get_item(current_item.item_id)
                if current_item_data and current_item_data.is_weapon():
                    current_attack = int(current_item_data.get_attack_power() * current_item.condition)
                
                diff = attack_power - current_attack
                if diff > 0:
                    preview = f"(+{diff})"
                elif diff < 0:
                    preview = f"({diff})"
            else:
                preview = f"(+{attack_power})"
                
        elif item.is_armor():
            defense = int(item.get_defense() * item_instance.condition)
            current_item = self.current_equipment.get_equipped_item(slot)
            
            if current_item:
                current_defense = 0
                current_item_data = item_manager.get_item(current_item.item_id)
                if current_item_data and current_item_data.is_armor():
                    current_defense = int(current_item_data.get_defense() * current_item.condition)
                
                diff = defense - current_defense
                if diff > 0:
                    preview = f"(+{diff})"
                elif diff < 0:
                    preview = f"({diff})"
            else:
                preview = f"(+{defense})"
        
        return preview
    
    def _get_slot_name(self, slot: EquipmentSlot) -> str:
        """スロット名を取得"""
        slot_names = {
            EquipmentSlot.WEAPON: "武器",
            EquipmentSlot.ARMOR: "防具",
            EquipmentSlot.ACCESSORY_1: "アクセサリ1",
            EquipmentSlot.ACCESSORY_2: "アクセサリ2"
        }
        return slot_names.get(slot, slot.value)
    
    def _get_stat_name(self, stat: str) -> str:
        """ステータス名を取得"""
        stat_names = {
            "strength": "筋力",
            "agility": "敏捷性", 
            "intelligence": "知力",
            "faith": "信仰",
            "luck": "運",
            "attack_power": "攻撃力",
            "defense": "防御力",
            "magic_power": "魔法力",
            "magic_resistance": "魔法抵抗"
        }
        return stat_names.get(stat, stat)
    
    def show(self):
        """装備UIを表示"""
        if self.current_party:
            self.show_party_equipment_menu(self.current_party)
        else:
            logger.warning("パーティが設定されていません")
    
    def hide(self):
        """装備UIを非表示"""
        try:
            ui_manager.hide_element("party_equipment_main")
        except:
            pass
        self.is_open = False
        logger.debug("装備UIを非表示にしました")
    
    def destroy(self):
        """装備UIを破棄"""
        self.hide()
        self.current_party = None
        self.current_character = None
        self.current_equipment = None
        self.selected_slot = None
        self.comparison_item = None
        logger.debug("EquipmentUIを破棄しました")
    
    def set_close_callback(self, callback: Callable):
        """閉じるコールバックを設定"""
        self.callback_on_close = callback
    
    def _back_to_main_menu(self):
        """メインメニューに戻る"""
        if self.current_party:
            self.show_party_equipment_menu(self.current_party)
    
    def _back_to_character_equipment(self):
        """キャラクター装備画面に戻る"""
        if self.current_character:
            self._show_character_equipment(self.current_character)
    
    def _back_to_slot_options(self):
        """スロットオプションに戻る"""
        if self.selected_slot:
            self._show_slot_options(self.selected_slot)
    
    def _close_equipment_ui(self):
        """装備UIを閉じる"""
        self.hide()
        if self.callback_on_close:
            self.callback_on_close()
    
    def _close_dialog(self):
        """ダイアログを閉じる"""
        ui_manager.hide_all_elements()
    
    def _show_message(self, message: str):
        """メッセージを表示"""
        dialog = UIDialog(
            "equipment_message",
            "装備",
            message,
            buttons=[
                {"text": "OK", "command": self._close_dialog}
            ]
        )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)


# グローバルインスタンス
equipment_ui = EquipmentUI()