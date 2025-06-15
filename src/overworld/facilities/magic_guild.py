"""魔術師ギルド"""

from typing import Dict, List, Optional, Any
from src.overworld.base_facility import BaseFacility, FacilityType
from src.character.party import Party
from src.character.character import Character
from src.items.item import Item, ItemManager, ItemInstance, ItemType, item_manager
from src.ui.base_ui import UIMenu, UIDialog, ui_manager
from src.core.config_manager import config_manager
from src.utils.logger import logger


class MagicGuild(BaseFacility):
    """魔術師ギルド"""
    
    def __init__(self):
        super().__init__(
            facility_id="magic_guild",
            facility_type=FacilityType.MAGIC_GUILD,
            name_key="facility.magic_guild"
        )
        
        self.item_manager = item_manager
        
        # サービス料金
        self.service_costs = {
            'spell_learning': 200,  # 魔法習得
            'item_identification': 100,  # アイテム鑑定
            'magical_analysis': 300,  # 魔法分析
            'enchantment': 500,  # エンチャント
            'curse_analysis': 150,  # 呪い分析
        }
        
        # 習得可能魔法一覧
        self.available_spells = {
            'fire': {'name': 'ファイア', 'level': 1, 'cost': 200},
            'heal': {'name': 'ヒール', 'level': 1, 'cost': 200},
            'cure': {'name': 'キュア', 'level': 1, 'cost': 150},
            'light': {'name': 'ライト', 'level': 1, 'cost': 100},
            'fireball': {'name': 'ファイアボール', 'level': 3, 'cost': 500},
            'greater_heal': {'name': 'グレーターヒール', 'level': 3, 'cost': 500},
            'teleport': {'name': 'テレポート', 'level': 5, 'cost': 1000},
            'resurrection': {'name': 'リザレクション', 'level': 7, 'cost': 2000}
        }
    
    def _setup_menu_items(self, menu: UIMenu):
        """魔術師ギルド固有のメニュー項目を設定"""
        menu.add_menu_item(
            "魔法習得",
            self._show_spell_learning_menu
        )
        
        menu.add_menu_item(
            "アイテム鑑定",
            self._show_identification_menu
        )
        
        menu.add_menu_item(
            "魔法分析",
            self._show_analysis_menu
        )
        
        menu.add_menu_item(
            "魔法書購入",
            self._show_spellbook_shop
        )
        
        menu.add_menu_item(
            "大魔術師と話す",
            self._talk_to_archmage
        )
    
    def _on_enter(self):
        """魔術師ギルド入場時の処理"""
        logger.info("魔術師ギルドに入りました")
        
        # 入場時のメッセージ
        welcome_message = (
            "「ようこそ、魔術師ギルドへ。\n\n"
            "ここでは魔法の習得、アイテムの鑑定、\n"
            "そして様々な魔術的サービスを\n"
            "提供しております。\n\n"
            "知識こそ力、魔法こそ真理です。\n"
            "何かご用件はありますか？」"
        )
        
        self._show_dialog(
            "magic_guild_welcome_dialog",
            "大魔術師",
            welcome_message
        )
    
    def _on_exit(self):
        """魔術師ギルド退場時の処理"""
        logger.info("魔術師ギルドから出ました")
    
    def _show_spell_learning_menu(self):
        """魔法習得メニューを表示"""
        if not self.current_party:
            self._show_error_message("パーティが設定されていません")
            return
        
        # 魔法を習得可能なキャラクターを探す
        magic_users = []
        for character in self.current_party.get_all_characters():
            if character.get_class_name() in ['mage', 'priest', 'bishop']:
                magic_users.append(character)
        
        if not magic_users:
            self._show_dialog(
                "no_magic_users_dialog",
                "魔法習得",
                "パーティに魔法を習得できる\n"
                "キャラクターがいません。\n\n"
                "魔法習得可能クラス:\n"
                "• 魔術師 (Mage)\n"
                "• 僧侶 (Priest)\n"
                "• 司教 (Bishop)"
            )
            return
        
        learning_menu = UIMenu("spell_learning_menu", "魔法習得")
        
        for character in magic_users:
            char_info = f"{character.name} (Lv.{character.experience.level} {character.get_class_name()})"
            learning_menu.add_menu_item(
                char_info,
                self._show_available_spells,
                [character]
            )
        
        learning_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._back_to_main_menu_from_submenu,
            [learning_menu]
        )
        
        self._show_submenu(learning_menu)
    
    def _show_available_spells(self, character: Character):
        """習得可能魔法一覧を表示"""
        spells_menu = UIMenu("available_spells_menu", f"{character.name} の魔法習得")
        
        # キャラクターのレベルに応じて習得可能な魔法を表示
        character_level = character.experience.level
        available_for_character = []
        
        for spell_id, spell_data in self.available_spells.items():
            if spell_data['level'] <= character_level:
                # TODO: Phase 4で既習得魔法チェック機能実装
                available_for_character.append((spell_id, spell_data))
        
        if not available_for_character:
            self._show_error_message(f"{character.name} が習得できる魔法がありません")
            return
        
        for spell_id, spell_data in available_for_character:
            spell_info = f"{spell_data['name']} Lv.{spell_data['level']} - {spell_data['cost']}G"
            spells_menu.add_menu_item(
                spell_info,
                self._learn_spell,
                [character, spell_id, spell_data]
            )
        
        spells_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._show_spell_learning_menu
        )
        
        self._show_submenu(spells_menu)
    
    def _learn_spell(self, character: Character, spell_id: str, spell_data: Dict[str, Any]):
        """魔法習得処理"""
        if not self.current_party:
            return
        
        cost = spell_data['cost']
        
        if self.current_party.gold < cost:
            self._show_error_message(f"ゴールドが不足しています。（必要: {cost}G）")
            return
        
        # 習得確認
        confirmation_text = (
            f"{character.name} が {spell_data['name']} を習得しますか？\n\n"
            f"魔法レベル: {spell_data['level']}\n"
            f"費用: {cost}G\n"
            f"現在のゴールド: {self.current_party.gold}G\n\n"
            "一度習得した魔法は永続的に使用できます。"
        )
        
        self._show_confirmation(
            confirmation_text,
            lambda: self._perform_spell_learning(character, spell_id, spell_data, cost)
        )
    
    def _perform_spell_learning(self, character: Character, spell_id: str, spell_data: Dict[str, Any], cost: int):
        """魔法習得実行"""
        if not self.current_party:
            return
        
        # ゴールド支払い
        self.current_party.gold -= cost
        
        # TODO: Phase 4で魔法習得システム実装
        # character.learn_spell(spell_id)
        
        success_message = (
            f"{character.name} が {spell_data['name']} を習得しました！\n\n"
            "新しい魔法の知識が\n"
            "キャラクターの記憶に刻まれました。\n\n"
            f"残りゴールド: {self.current_party.gold}G"
        )
        
        self._show_success_message(success_message)
        logger.info(f"魔法習得: {character.name} - {spell_id}")
    
    def _show_identification_menu(self):
        """アイテム鑑定メニューを表示"""
        if not self.current_party:
            self._show_error_message("パーティが設定されていません")
            return
        
        # パーティインベントリから未鑑定アイテムを検索
        party_inventory = self.current_party.get_party_inventory()
        unidentified_items = []
        
        for slot in party_inventory.slots:
            if not slot.is_empty():
                item_instance = slot.item_instance
                if not item_instance.identified:
                    item = item_manager.get_item(item_instance.item_id)
                    if item:
                        unidentified_items.append((slot, item_instance, item))
        
        if not unidentified_items:
            self._show_dialog(
                "no_unidentified_items_dialog",
                "アイテム鑑定",
                "現在、未鑑定のアイテムはありません。\n\n"
                "ダンジョンで見つけた未知のアイテムを\n"
                "持参してください。\n\n"
                f"鑑定費用: {self.service_costs['item_identification']}G/個"
            )
            return
        
        # 鑑定メニューを作成
        identification_menu = UIMenu("identification_menu", "アイテム鑑定")
        
        for slot, item_instance, item in unidentified_items:
            # アイテム表示名を作成
            item_name = f"未鑑定の{item.item_type.value}"
            if item_instance.quantity > 1:
                item_name += f" x{item_instance.quantity}"
            
            identification_cost = self.service_costs['item_identification']
            total_cost = identification_cost * item_instance.quantity
            
            item_info = f"{item_name} ({total_cost}G)"
            
            identification_menu.add_menu_item(
                item_info,
                self._show_identification_confirmation,
                [slot, item_instance, item]
            )
        
        identification_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._back_to_main_menu_from_submenu,
            [identification_menu]
        )
        
        self._show_submenu(identification_menu)
    
    def _show_analysis_menu(self):
        """魔法分析メニューを表示"""
        if not self.current_party:
            self._show_error_message("パーティが設定されていません")
            return
        
        analysis_menu = UIMenu("analysis_menu", "魔法分析")
        
        analysis_menu.add_menu_item(
            "パーティの魔法適性分析",
            self._analyze_party_magic_aptitude
        )
        
        analysis_menu.add_menu_item(
            "キャラクター個別分析",
            self._show_character_analysis_menu
        )
        
        analysis_menu.add_menu_item(
            "魔法使用回数確認",
            self._show_spell_usage_info
        )
        
        analysis_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._back_to_main_menu_from_submenu,
            [analysis_menu]
        )
        
        self._show_submenu(analysis_menu)
    
    def _analyze_party_magic_aptitude(self):
        """パーティの魔法適性分析"""
        if not self.current_party:
            return
        
        cost = self.service_costs['magical_analysis']
        
        if self.current_party.gold < cost:
            self._show_error_message(f"ゴールドが不足しています。（必要: {cost}G）")
            return
        
        # 分析実行
        self.current_party.gold -= cost
        
        analysis_result = "【パーティ魔法適性分析結果】\n\n"
        
        magic_users = 0
        total_int = 0
        total_faith = 0
        
        for character in self.current_party.get_all_characters():
            class_name = character.get_class_name()
            
            analysis_result += f"• {character.name} ({class_name})\n"
            
            if class_name in ['mage', 'priest', 'bishop']:
                magic_users += 1
                analysis_result += f"  知恵: {character.base_stats.intelligence}\n"
                analysis_result += f"  信仰心: {character.base_stats.faith}\n"
                
                if class_name == 'mage':
                    analysis_result += "  → 攻撃魔法に優れています\n"
                elif class_name == 'priest':
                    analysis_result += "  → 回復・補助魔法に優れています\n"
                elif class_name == 'bishop':
                    analysis_result += "  → 全ての魔法を習得可能です\n"
            else:
                analysis_result += "  → 魔法は使用できません\n"
            
            total_int += character.base_stats.intelligence
            total_faith += character.base_stats.faith
            
            analysis_result += "\n"
        
        # 総合評価
        party_size = len(self.current_party.characters)
        avg_int = total_int / party_size if party_size > 0 else 0
        avg_faith = total_faith / party_size if party_size > 0 else 0
        
        analysis_result += "【総合評価】\n"
        analysis_result += f"魔法使用者: {magic_users}人\n"
        analysis_result += f"平均知恵: {avg_int:.1f}\n"
        analysis_result += f"平均信仰心: {avg_faith:.1f}\n\n"
        
        if magic_users == 0:
            analysis_result += "魔法バランス: 物理特化型\n"
        elif magic_users >= party_size // 2:
            analysis_result += "魔法バランス: 魔法重視型\n"
        else:
            analysis_result += "魔法バランス: バランス型\n"
        
        analysis_result += f"\n分析費用: {cost}G\n"
        analysis_result += f"残りゴールド: {self.current_party.gold}G"
        
        self._show_dialog(
            "aptitude_analysis_dialog",
            "魔法適性分析",
            analysis_result
        )
        
        logger.info(f"パーティ魔法適性分析実行: {self.current_party.name}")
    
    def _show_character_analysis_menu(self):
        """キャラクター個別分析メニュー"""
        if not self.current_party:
            return
        
        char_menu = UIMenu("character_analysis_menu", "キャラクター分析")
        
        for character in self.current_party.get_all_characters():
            char_info = f"{character.name} (Lv.{character.experience.level})"
            char_menu.add_menu_item(
                char_info,
                self._analyze_character,
                [character]
            )
        
        char_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._show_analysis_menu
        )
        
        self._show_submenu(char_menu)
    
    def _analyze_character(self, character: Character):
        """キャラクター個別分析"""
        analysis = f"【{character.name} の魔法分析】\n\n"
        
        analysis += f"種族: {character.get_race_name()}\n"
        analysis += f"職業: {character.get_class_name()}\n"
        analysis += f"レベル: {character.experience.level}\n\n"
        
        analysis += "【基本能力】\n"
        analysis += f"知恵: {character.base_stats.intelligence}\n"
        analysis += f"信仰心: {character.base_stats.faith}\n\n"
        
        # 魔法適性判定を改善（クラス名の正規化）
        class_name = character.get_class_name().lower()
        magic_classes = ['mage', 'priest', 'bishop', '魔術師', '僧侶', '司教', 'wizard', 'cleric']
        
        # 知恵と信仰心による魔法使用可能判定も追加
        intelligence_check = character.base_stats.intelligence >= 12  # 最低知恵要件
        faith_check = character.base_stats.faith >= 12  # 最低信仰心要件
        
        can_use_magic = (any(magic_class in class_name for magic_class in magic_classes) or 
                        (intelligence_check and faith_check))
        
        if can_use_magic:
            analysis += "【魔法適性】\n"
            
            if 'mage' in class_name or '魔術師' in class_name:
                analysis += "• 攻撃魔法の習得・使用が可能\n"
                analysis += "• 知恵の値が魔法威力に影響\n"
                analysis += "• 高レベル破壊魔法の習得可能\n"
            elif 'priest' in class_name or '僧侶' in class_name:
                analysis += "• 回復・補助魔法の習得・使用が可能\n"
                analysis += "• 信仰心の値が魔法効果に影響\n"
                analysis += "• 蘇生魔法の習得可能\n"
            elif 'bishop' in class_name or '司教' in class_name:
                analysis += "• 全系統の魔法習得・使用が可能\n"
                analysis += "• 知恵と信仰心の両方が重要\n"
                analysis += "• 最高位魔法の習得可能\n"
            else:
                # 能力値ベースの魔法使用
                analysis += "• 能力値により限定的な魔法使用が可能\n"
                if intelligence_check:
                    analysis += "• 知恵により基本的な攻撃魔法が使用可能\n"
                if faith_check:
                    analysis += "• 信仰心により基本的な回復魔法が使用可能\n"
            
            # TODO: Phase 4で習得済み魔法一覧表示
            analysis += "\n【習得可能魔法レベル】\n"
            max_spell_level = min(character.experience.level, 9)
            analysis += f"Lv.1 ～ Lv.{max_spell_level} の魔法\n"
            
            # 具体的な魔法使用条件を表示
            analysis += "\n【魔法使用条件】\n"
            analysis += f"現在の知恵: {character.base_stats.intelligence} "
            analysis += f"({'✓' if intelligence_check else '✗'} 攻撃魔法使用可能)\n"
            analysis += f"現在の信仰心: {character.base_stats.faith} "
            analysis += f"({'✓' if faith_check else '✗'} 回復魔法使用可能)\n"
        else:
            analysis += "【魔法適性】\n"
            analysis += "• 魔法の習得・使用はできません\n"
            analysis += "• 魔法系アイテムの使用は一部可能\n"
            analysis += "\n【改善提案】\n"
            if character.base_stats.intelligence < 12:
                analysis += f"• 知恵を {12 - character.base_stats.intelligence} ポイント上げると攻撃魔法使用可能\n"
            if character.base_stats.faith < 12:
                analysis += f"• 信仰心を {12 - character.base_stats.faith} ポイント上げると回復魔法使用可能\n"
        
        analysis += "\n※ この分析は無料サービスです"
        
        self._show_dialog(
            "character_analysis_dialog",
            f"{character.name} の分析結果",
            analysis
        )
    
    def _show_spell_usage_info(self):
        """魔法使用回数情報表示"""
        info_text = (
            "【魔法使用回数について】\n\n"
            "このゲームシステムでは、\n"
            "地上部に戻ると魔法使用回数が\n"
            "自動的に全回復します。\n\n"
            "そのため、ダンジョン探索中は\n"
            "魔法使用回数を気にせず\n"
            "積極的に魔法を活用できます。\n\n"
            "詳細な魔法システムは\n"
            "Phase 4で実装予定です。\n\n"
            "※ 現在は魔法使用回数の\n"
            "　 詳細表示はできません"
        )
        
        self._show_dialog(
            "spell_usage_info_dialog",
            "魔法使用回数について",
            info_text
        )
    
    def _show_spellbook_shop(self):
        """魔法書購入ショップ"""
        spellbook_items = self.item_manager.get_items_by_type(ItemType.SPELLBOOK)
        
        if not spellbook_items:
            self._show_error_message("現在、魔法書の在庫がありません")
            return
        
        spellbook_menu = UIMenu("spellbook_shop_menu", "魔法書購入")
        
        for item in spellbook_items:
            item_info = f"{item.get_name()} - {item.price}G"
            spellbook_menu.add_menu_item(
                item_info,
                self._show_spellbook_details,
                [item]
            )
        
        spellbook_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._back_to_main_menu_from_submenu,
            [spellbook_menu]
        )
        
        self._show_submenu(spellbook_menu)
    
    def _show_spellbook_details(self, item: Item):
        """魔法書詳細表示"""
        if not self.current_party:
            return
        
        details = f"【{item.get_name()}】\n\n"
        details += f"説明: {item.get_description()}\n"
        details += f"価格: {item.price}G\n"
        details += f"習得魔法: {item.get_spell_id()}\n"
        details += f"現在のゴールド: {self.current_party.gold}G\n"
        
        if self.current_party.gold >= item.price:
            details += "\n購入しますか？"
            
            dialog = UIDialog(
                "spellbook_detail_dialog",
                "魔法書詳細",
                details,
                buttons=[
                    {
                        'text': "購入する",
                        'command': lambda: self._buy_spellbook(item)
                    },
                    {
                        'text': "戻る",
                        'command': self._close_dialog
                    }
                ]
            )
        else:
            details += "\n※ ゴールドが不足しています"
            
            dialog = UIDialog(
                "spellbook_detail_dialog",
                "魔法書詳細",
                details,
                buttons=[
                    {
                        'text': "戻る",
                        'command': self._close_dialog
                    }
                ]
            )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)
    
    def _buy_spellbook(self, item: Item):
        """魔法書購入処理"""
        if not self.current_party:
            return
        
        self._close_dialog()
        
        if self.current_party.gold < item.price:
            self._show_error_message("ゴールドが不足しています")
            return
        
        # 購入処理
        self.current_party.gold -= item.price
        
        # TODO: Phase 4でインベントリシステム実装後、アイテム追加
        
        success_message = (
            f"{item.get_name()} を購入しました！\n\n"
            "魔法書を使用することで\n"
            "新しい魔法を習得できます。\n\n"
            f"残りゴールド: {self.current_party.gold}G"
        )
        
        self._show_success_message(success_message)
        logger.info(f"魔法書購入: {item.item_id} ({item.price}G)")
    
    def _talk_to_archmage(self):
        """大魔術師との会話"""
        messages = [
            (
                "魔法について",
                "「魔法は知識と理解の結晶です。\n"
                "ただ唱えるだけではなく、\n"
                "その原理を理解することが\n"
                "真の魔術師への道です。」"
            ),
            (
                "魔術師ギルドについて",
                "「ここは知識の殿堂です。\n"
                "多くの魔術師がここで学び、\n"
                "そして新たな発見をしてきました。\n"
                "あなたも是非、学んでいってください。」"
            ),
            (
                "冒険での魔法活用",
                "「ダンジョンでは魔法が命を救います。\n"
                "攻撃魔法だけでなく、回復や補助、\n"
                "探索魔法も重要です。\n"
                "バランスよく習得しましょう。」"
            ),
            (
                "高位魔法について",
                "「レベルが上がれば、より強力な\n"
                "魔法を習得できるようになります。\n"
                "しかし、力だけでなく\n"
                "責任も伴うことを忘れずに。」"
            ),
            (
                "魔法研究",
                "「現在、新しい魔法の研究を\n"
                "進めています。近い将来、\n"
                "より多様な魔法を提供できる\n"
                "かもしれません。期待していてください。」"
            )
        ]
        
        # ランダムにメッセージを選択
        import random
        title, message = random.choice(messages)
        
        self._show_dialog(
            "archmage_dialog",
            f"大魔術師 - {title}",
            message
        )
    
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
    
    def _show_identification_confirmation(self, slot, item_instance: ItemInstance, item: Item):
        """鑑定確認ダイアログを表示"""
        if not self.current_party:
            return
        
        identification_cost = self.service_costs['item_identification']
        
        # アイテム情報を作成
        details = f"【アイテム鑑定】\n\n"
        details += f"対象: 未鑑定の{item.item_type.value}\n"
        
        if item_instance.quantity > 1:
            details += f"数量: {item_instance.quantity}個\n"
            total_cost = identification_cost * item_instance.quantity
            details += f"鑑定費用: {identification_cost}G x{item_instance.quantity} = {total_cost}G\n"
        else:
            total_cost = identification_cost
            details += f"鑑定費用: {identification_cost}G\n"
        
        details += f"\n現在のゴールド: {self.current_party.gold}G\n"
        
        if self.current_party.gold >= total_cost:
            details += f"鑑定後: {self.current_party.gold - total_cost}G\n"
            details += "\n鑑定を実行しますか？\n"
            details += "※ 鑑定したアイテムの正体が明らかになります。"
            
            dialog = UIDialog(
                "identification_confirmation_dialog",
                "鑑定確認",
                details,
                buttons=[
                    {
                        'text': "鑑定する",
                        'command': lambda: self._identify_item(slot, item_instance, item, total_cost)
                    },
                    {
                        'text': "戻る",
                        'command': self._close_dialog
                    }
                ]
            )
        else:
            details += "\n※ ゴールドが不足しています"
            
            dialog = UIDialog(
                "identification_confirmation_dialog",
                "鑑定確認",
                details,
                buttons=[
                    {
                        'text': "戻る",
                        'command': self._close_dialog
                    }
                ]
            )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)
    
    def _identify_item(self, slot, item_instance: ItemInstance, item: Item, cost: int):
        """アイテム鑑定処理"""
        if not self.current_party:
            return
        
        self._close_dialog()
        
        # ゴールドチェック
        if self.current_party.gold < cost:
            self._show_error_message("ゴールドが不足しています")
            return
        
        # 鑑定処理
        self.current_party.gold -= cost
        item_instance.identified = True
        
        # 鑑定結果を表示
        result_message = f"【鑑定結果】\n\n"
        result_message += f"アイテム名: {item.get_name()}\n\n"
        result_message += f"説明: {item.get_description()}\n\n"
        
        if item.is_weapon():
            result_message += f"タイプ: 武器\n"
            result_message += f"攻撃力: +{item.get_attack_power()}\n"
            if item.get_attribute():
                result_message += f"属性: {item.get_attribute()}\n"
        elif item.is_armor():
            result_message += f"タイプ: 防具\n"
            result_message += f"防御力: +{item.get_defense()}\n"
        elif item.is_consumable():
            result_message += f"タイプ: 消耗品\n"
            result_message += f"効果: {item.get_effect_type()}\n"
            if item.get_effect_value() > 0:
                result_message += f"効果値: {item.get_effect_value()}\n"
        
        result_message += f"\n希少度: {item.rarity.value}\n"
        result_message += f"重量: {item.weight}\n"
        result_message += f"価値: {item.price}G\n"
        
        if item.usable_classes:
            result_message += f"使用可能クラス: {', '.join(item.usable_classes)}\n"
        
        if item_instance.quantity > 1:
            result_message += f"\n所持数: {item_instance.quantity}個\n"
        
        result_message += f"\n鑑定費用: {cost}G\n"
        result_message += f"残りゴールド: {self.current_party.gold}G\n\n"
        result_message += "鑑定完了！ アイテムの正体が判明しました。"
        
        self._show_dialog(
            "identification_result_dialog",
            "鑑定結果",
            result_message
        )
        
        logger.info(f"アイテム鑑定: {item.item_id} x{item_instance.quantity} ({cost}G)")