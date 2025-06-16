"""教会"""

from typing import Dict, List, Optional, Any
from src.overworld.base_facility import BaseFacility, FacilityType
from src.character.party import Party
from src.character.character import Character, CharacterStatus
from src.items.item import Item, ItemManager, ItemInstance, ItemType, item_manager
from src.ui.base_ui import UIMenu, UIDialog, ui_manager
from src.core.config_manager import config_manager
from src.utils.logger import logger


class Temple(BaseFacility):
    """教会"""
    
    def __init__(self):
        super().__init__(
            facility_id="temple",
            facility_type=FacilityType.TEMPLE,
            name_key="facility.temple"
        )
        
        # サービス料金
        self.service_costs = {
            'resurrection': 500,  # 蘇生
            'ash_restoration': 1000,  # 灰化回復
            'blessing': 100,  # 祝福
            'curse_removal': 200,  # 呪い解除
        }
    
    def _setup_menu_items(self, menu: UIMenu):
        """教会固有のメニュー項目を設定"""
        menu.add_menu_item(
            "蘇生サービス",
            self._show_resurrection_menu
        )
        
        menu.add_menu_item(
            "祝福サービス",
            self._show_blessing_menu
        )
        
        menu.add_menu_item(
            "神父と話す",
            self._talk_to_priest
        )
        
        menu.add_menu_item(
            "祈祷書購入",
            self._show_prayerbook_shop
        )
        
        menu.add_menu_item(
            "寄付をする",
            self._show_donation_menu
        )
    
    def _on_enter(self):
        """教会入場時の処理"""
        logger.info("教会に入りました")
        
        # 入場時のメッセージ
        welcome_message = (
            "「神の加護がありますように。\n\n"
            "ここは聖なる場所です。\n"
            "疲れた魂を癒し、\n"
            "失われた命を取り戻し、\n"
            "神の祝福を授けることができます。\n\n"
            "何かお困りのことはありませんか？」"
        )
        
        self._show_dialog(
            "temple_welcome_dialog",
            "神父",
            welcome_message
        )
    
    def _on_exit(self):
        """教会退場時の処理"""
        logger.info("教会から出ました")
    
    def _show_resurrection_menu(self):
        """蘇生メニューを表示"""
        if not self.current_party:
            self._show_error_message("パーティが設定されていません")
            return
        
        # 死亡・灰化状態のキャラクターを探す
        resurrection_candidates = []
        ash_candidates = []
        
        for character in self.current_party.get_all_characters():
            if character.status == CharacterStatus.DEAD:
                resurrection_candidates.append(character)
            elif character.status == CharacterStatus.ASHES:
                ash_candidates.append(character)
        
        if not resurrection_candidates and not ash_candidates:
            self._show_dialog(
                "no_resurrection_dialog",
                "蘇生サービス",
                "蘇生が必要なキャラクターはいません。\n\n"
                "皆さん健康で何よりです！"
            )
            return
        
        resurrection_menu = UIMenu("resurrection_menu", "蘇生サービス")
        
        # 死亡キャラクターの蘇生
        for character in resurrection_candidates:
            cost = self.service_costs['resurrection']
            char_info = f"{character.name} の蘇生 - {cost}G"
            resurrection_menu.add_menu_item(
                char_info,
                self._resurrect_character,
                [character]
            )
        
        # 灰化キャラクターの復活
        for character in ash_candidates:
            cost = self.service_costs['ash_restoration']
            char_info = f"{character.name} の復活 - {cost}G"
            resurrection_menu.add_menu_item(
                char_info,
                self._restore_from_ashes,
                [character]
            )
        
        resurrection_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._back_to_main_menu_from_submenu,
            [resurrection_menu]
        )
        
        self._show_submenu(resurrection_menu)
    
    def _resurrect_character(self, character: Character):
        """キャラクター蘇生"""
        if not self.current_party:
            return
        
        cost = self.service_costs['resurrection']
        
        if self.current_party.gold < cost:
            self._show_error_message(f"ゴールドが不足しています。（必要: {cost}G）")
            return
        
        # 蘇生確認
        confirmation_text = (
            f"{character.name} を蘇生しますか？\n\n"
            f"費用: {cost}G\n"
            f"現在のゴールド: {self.current_party.gold}G\n\n"
            "蘇生後はHP・MPが1まで回復します。"
        )
        
        self._show_confirmation(
            confirmation_text,
            lambda: self._perform_resurrection(character, cost)
        )
    
    def _perform_resurrection(self, character: Character, cost: int):
        """蘇生実行"""
        if not self.current_party:
            return
        
        # ゴールド支払い
        self.current_party.gold -= cost
        
        # 蘇生処理
        character.status = CharacterStatus.GOOD
        character.derived_stats.current_hp = 1
        character.derived_stats.current_mp = 1
        
        success_message = (
            f"{character.name} が蘇生されました！\n\n"
            "神の奇跡により命が戻りました。\n"
            "しかし体力はまだ回復していません。\n"
            "地上部に戻って完全回復しましょう。\n\n"
            f"残りゴールド: {self.current_party.gold}G"
        )
        
        self._show_success_message(success_message)
        logger.info(f"キャラクター蘇生: {character.name}")
    
    def _restore_from_ashes(self, character: Character):
        """灰化状態から復活"""
        if not self.current_party:
            return
        
        cost = self.service_costs['ash_restoration']
        
        if self.current_party.gold < cost:
            self._show_error_message(f"ゴールドが不足しています。（必要: {cost}G）")
            return
        
        # 復活確認
        confirmation_text = (
            f"{character.name} を灰から復活させますか？\n\n"
            f"費用: {cost}G\n"
            f"現在のゴールド: {self.current_party.gold}G\n\n"
            "これは非常に高度な奇跡です。\n"
            "復活後はHP・MPが1まで回復します。"
        )
        
        self._show_confirmation(
            confirmation_text,
            lambda: self._perform_ash_restoration(character, cost)
        )
    
    def _perform_ash_restoration(self, character: Character, cost: int):
        """灰化復活実行"""
        if not self.current_party:
            return
        
        # ゴールド支払い
        self.current_party.gold -= cost
        
        # 復活処理
        character.status = CharacterStatus.GOOD
        character.derived_stats.current_hp = 1
        character.derived_stats.current_mp = 1
        
        success_message = (
            f"{character.name} が灰から復活しました！\n\n"
            "これは神の最大の奇跡です。\n"
            "失われた魂が戻ってきました。\n"
            "地上部に戻って完全回復しましょう。\n\n"
            f"残りゴールド: {self.current_party.gold}G"
        )
        
        self._show_success_message(success_message)
        logger.info(f"灰化復活: {character.name}")
    
    def _show_blessing_menu(self):
        """祝福メニューを表示"""
        if not self.current_party:
            self._show_error_message("パーティが設定されていません")
            return
        
        cost = self.service_costs['blessing']
        
        blessing_info = (
            "【祝福サービス】\n\n"
            "神の加護により、パーティ全体に\n"
            "幸運の祝福を授けます。\n\n"
            "効果:\n"
            "• 次の冒険での運が上昇\n"
            "• 宝箱発見率アップ\n"
            "• クリティカル率上昇\n\n"
            f"費用: {cost}G\n"
            f"現在のゴールド: {self.current_party.gold}G\n\n"
            "祝福を受けますか？"
        )
        
        if self.current_party.gold >= cost:
            dialog = UIDialog(
                "blessing_dialog",
                "祝福サービス",
                blessing_info,
                buttons=[
                    {
                        'text': "祝福を受ける",
                        'command': lambda: self._perform_blessing(cost)
                    },
                    {
                        'text': "戻る",
                        'command': self._close_blessing_dialog
                    }
                ]
            )
        else:
            dialog = UIDialog(
                "blessing_dialog",
                "祝福サービス",
                blessing_info + "\n※ ゴールドが不足しています",
                buttons=[
                    {
                        'text': "戻る",
                        'command': self._close_blessing_dialog
                    }
                ]
            )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)
    
    def _close_blessing_dialog(self):
        """祝福ダイアログを閉じてメインメニューに戻る"""
        ui_manager.hide_element("blessing_dialog")
        ui_manager.unregister_element("blessing_dialog")
        
        # メインメニューを再表示
        if self.main_menu:
            ui_manager.show_element(self.main_menu.element_id)
    
    def _perform_blessing(self, cost: int):
        """祝福実行"""
        if not self.current_party:
            return
        
        self._close_dialog()
        
        # ゴールド支払い
        self.current_party.gold -= cost
        
        # TODO: Phase 4で祝福効果をパーティステータスに追加
        
        success_message = (
            "パーティが神の祝福を受けました！\n\n"
            "光に包まれ、幸運のオーラが\n"
            "皆さんを包んでいます。\n\n"
            "次の冒険が成功しますように...\n\n"
            f"残りゴールド: {self.current_party.gold}G"
        )
        
        self._show_success_message(success_message)
        logger.info(f"パーティ祝福実行: {self.current_party.name}")
    
    def _show_donation_menu(self):
        """寄付メニューを表示"""
        if not self.current_party:
            self._show_error_message("パーティが設定されていません")
            return
        
        donation_amounts = [10, 50, 100, 500, 1000]
        
        donation_menu = UIMenu("donation_menu", "寄付")
        
        for amount in donation_amounts:
            if self.current_party.gold >= amount:
                donation_menu.add_menu_item(
                    f"{amount}G を寄付",
                    self._make_donation,
                    [amount]
                )
        
        donation_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._back_to_main_menu_from_submenu,
            [donation_menu]
        )
        
        self._show_submenu(donation_menu)
    
    def _make_donation(self, amount: int):
        """寄付実行"""
        if not self.current_party:
            return
        
        if self.current_party.gold < amount:
            self._show_error_message("ゴールドが不足しています")
            return
        
        # 寄付処理
        self.current_party.gold -= amount
        
        # TODO: Phase 4で寄付による名声ポイント等を実装
        
        gratitude_message = (
            f"{amount}G のご寄付をありがとうございます！\n\n"
            "あなたの善意は必ず報われるでしょう。\n"
            "神の加護がありますように。\n\n"
            f"残りゴールド: {self.current_party.gold}G"
        )
        
        self._show_success_message(gratitude_message)
        logger.info(f"教会寄付: {amount}G by {self.current_party.name}")
    
    def _show_prayerbook_shop(self):
        """祈祷書購入ショップ"""
        # 祈祷書（SPELLBOOK）タイプのアイテムを取得
        prayerbook_items = item_manager.get_items_by_type(ItemType.SPELLBOOK)
        
        if not prayerbook_items:
            self._show_error_message("現在、祈祷書の在庫がありません")
            return
        
        prayerbook_menu = UIMenu("prayerbook_shop_menu", "祈祷書購入")
        
        for item in prayerbook_items:
            item_info = f"{item.get_name()} - {item.price}G"
            prayerbook_menu.add_menu_item(
                item_info,
                self._show_prayerbook_details,
                [item]
            )
        
        prayerbook_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._back_to_main_menu_from_submenu,
            [prayerbook_menu]
        )
        
        self._show_submenu(prayerbook_menu)
    
    def _show_prayerbook_details(self, item: Item):
        """祈祷書詳細表示"""
        if not self.current_party:
            return
        
        details = f"【{item.get_name()}】\n\n"
        details += f"説明: {item.get_description()}\n"
        details += f"価格: {item.price}G\n"
        details += f"習得祈祷: {item.get_spell_id()}\n"
        details += f"現在のゴールド: {self.current_party.gold}G\n"
        
        if self.current_party.gold >= item.price:
            details += "\n購入しますか？"
            
            dialog = UIDialog(
                "prayerbook_detail_dialog",
                "祈祷書詳細",
                details,
                buttons=[
                    {
                        'text': "購入する",
                        'command': lambda: self._buy_prayerbook(item)
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
                "prayerbook_detail_dialog",
                "祈祷書詳細",
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
    
    def _buy_prayerbook(self, item: Item):
        """祈祷書購入処理"""
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
            "祈祷書を使用することで\n"
            "新しい祈祷を習得できます。\n\n"
            "神の教えが込められた聖なる書物です。\n"
            "大切に扱ってください。\n\n"
            f"残りゴールド: {self.current_party.gold}G"
        )
        
        self._show_success_message(success_message)
        logger.info(f"祈祷書購入: {item.item_id} ({item.price}G)")
    
    def _talk_to_priest(self):
        """神父との会話"""
        messages = [
            (
                "神について",
                "「神は常に我々を見守っています。\n"
                "困難な時こそ、信仰の力が\n"
                "あなたを支えてくれるでしょう。\n"
                "祈りを忘れずに。」"
            ),
            (
                "冒険について",
                "「冒険は魂を鍛える修行です。\n"
                "危険はありますが、それを乗り越えた時\n"
                "あなたは一回り大きくなっているでしょう。\n"
                "神の加護がありますように。」"
            ),
            (
                "蘇生について",
                "「死は終わりではありません。\n"
                "神の力により、失われた命を\n"
                "取り戻すことができます。\n"
                "諦めてはいけません。」"
            ),
            (
                "教会について",
                "「この教会は多くの冒険者の\n"
                "心の支えとなってきました。\n"
                "いつでもお気軽にお越しください。\n"
                "神の平安がありますように。」"
            )
        ]
        
        # ランダムにメッセージを選択
        import random
        title, message = random.choice(messages)
        
        self._show_dialog(
            "priest_dialog",
            f"神父 - {title}",
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