"""宿屋"""

from typing import Dict, List, Optional, Any
from src.overworld.base_facility import BaseFacility, FacilityType
from src.character.party import Party
from src.ui.base_ui import UIMenu, UIDialog, UIInputDialog, ui_manager
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
    
    def _setup_menu_items(self, menu: UIMenu):
        """宿屋固有のメニュー項目を設定"""
        menu.add_menu_item(
            "冒険の準備",
            self._show_adventure_preparation
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
        
        # 入場時のメッセージを表示
        welcome_message = (
            "「いらっしゃいませ！\n"
            "最近は皆さん、地上に戻るだけで\n"
            "すっかり元気になってしまうので、\n"
            "宿泊客が少なくて困っています。\n\n"
            "でも、旅の情報や噂話なら\n"
            "いくらでもお聞かせしますよ！」"
        )
        
        self._show_dialog(
            "inn_welcome_dialog",
            "宿屋の主人",
            welcome_message
        )
    
    def _on_exit(self):
        """宿屋退場時の処理"""
        logger.info("宿屋から出ました")
    
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
        
        self._show_dialog(
            "innkeeper_dialog",
            f"{config_manager.get_text('inn.innkeeper.title')} - {title}",
            message
        )
    
    def _show_travel_info(self):
        """旅の情報を表示"""
        travel_info = config_manager.get_text("inn.travel_info.content")
        
        self._show_dialog(
            "travel_info_dialog",
            config_manager.get_text("inn.travel_info.title"),
            travel_info
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
        
        self._show_dialog(
            "rumor_dialog",
            f"{config_manager.get_text('inn.rumors.title')} - {title}",
            rumor
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
        
        ui_manager.register_element(name_input_dialog)
        ui_manager.show_element(name_input_dialog.element_id)
    
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
        ui_manager.hide_element("party_name_input_dialog")
        ui_manager.unregister_element("party_name_input_dialog")
        
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
        ui_manager.hide_element("party_name_input_dialog")
        ui_manager.unregister_element("party_name_input_dialog")
        
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
        
        prep_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._back_to_main_menu_from_submenu,
            [prep_menu]
        )
        
        self._show_submenu(prep_menu)
    
    def _show_item_organization(self):
        """アイテム整理画面を表示"""
        if not self.current_party:
            return
        
        try:
            # インベントリマネージャーを取得
            inventory_manager = InventoryManager()
            
            # パーティのインベントリを取得
            party_inventory = self.current_party.get_party_inventory()
            if not party_inventory:
                self._show_error_message("パーティインベントリが見つかりません")
                return
            
            # インベントリUIを表示
            self._show_inventory_ui(party_inventory)
            
        except Exception as e:
            logger.error(f"アイテム整理画面表示エラー: {e}")
            self._show_error_message(f"アイテム整理画面の表示に失敗しました: {str(e)}")
    
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
        """魔術スロット管理画面を表示"""
        if not self.current_party:
            return
        
        try:
            # 魔法を使用できるキャラクターを検索
            spell_users = []
            for character in self.current_party.get_all_characters():
                if hasattr(character, 'spell_slots') or character.character_class in ['mage', 'priest', 'bishop']:
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
            
            # 魔法使いキャラクター選択メニューを表示
            self._show_spell_user_selection(spell_users)
            
        except Exception as e:
            logger.error(f"魔術スロット管理画面表示エラー: {e}")
            self._show_error_message(f"魔術スロット管理画面の表示に失敗しました: {str(e)}")
    
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
        """パーティ装備状況確認画面を表示"""
        if not self.current_party:
            return
        
        try:
            equipment_info = "【パーティ装備状況】\n\n"
            
            for character in self.current_party.get_all_characters():
                equipment_info += f"◆ {character.name}\n"
                
                # 基本情報
                equipment_info += f"  職業: {character.character_class}\n"
                equipment_info += f"  レベル: {character.experience.level}\n"
                
                # 装備情報を取得
                if hasattr(character, 'equipment'):
                    equipment = character.equipment
                    equipment_info += f"  武器: {self._get_equipment_name(equipment, 'weapon')}\n"
                    equipment_info += f"  防具: {self._get_equipment_name(equipment, 'armor')}\n"
                    equipment_info += f"  アクセサリ1: {self._get_equipment_name(equipment, 'accessory_1')}\n"
                    equipment_info += f"  アクセサリ2: {self._get_equipment_name(equipment, 'accessory_2')}\n"
                    
                    # 装備ボーナス情報
                    if hasattr(equipment, 'get_total_bonus'):
                        bonus = equipment.get_total_bonus()
                        if any(getattr(bonus, attr, 0) > 0 for attr in ['strength', 'agility', 'intelligence', 'faith', 'luck', 'attack_power', 'defense_power']):
                            equipment_info += f"  装備ボーナス: "
                            bonuses = []
                            if bonus.strength > 0: bonuses.append(f"力+{bonus.strength}")
                            if bonus.agility > 0: bonuses.append(f"敏+{bonus.agility}")
                            if bonus.intelligence > 0: bonuses.append(f"知+{bonus.intelligence}")
                            if bonus.faith > 0: bonuses.append(f"信+{bonus.faith}")
                            if bonus.luck > 0: bonuses.append(f"運+{bonus.luck}")
                            if bonus.attack_power > 0: bonuses.append(f"攻+{bonus.attack_power}")
                            if bonus.defense_power > 0: bonuses.append(f"防+{bonus.defense_power}")
                            equipment_info += ", ".join(bonuses) + "\n"
                else:
                    equipment_info += f"  装備: システム未実装\n"
                
                equipment_info += "\n"
            
            equipment_info += "※詳細な装備管理は装備画面で行えます"
            
            self._show_dialog(
                "equipment_status_dialog",
                "パーティ装備状況",
                equipment_info
            )
            
        except Exception as e:
            logger.error(f"装備状況表示エラー: {e}")
            self._show_error_message(f"装備状況の表示に失敗しました: {str(e)}")
    
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
            ui_manager.hide_element(self.main_menu.element_id)
        
        ui_manager.register_element(submenu)
        ui_manager.show_element(submenu.element_id, modal=True)
    
    def _back_to_main_menu_from_submenu(self, submenu: UIMenu):
        """サブメニューからメインメニューに戻る"""
        ui_manager.hide_element(submenu.element_id)
        ui_manager.unregister_element(submenu.element_id)
        
        if self.main_menu:
            ui_manager.show_element(self.main_menu.element_id)