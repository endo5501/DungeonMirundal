"""教会"""

from typing import Dict, List, Optional, Any
import pygame
from src.overworld.base_facility import BaseFacility, FacilityType
from src.character.party import Party
from src.character.character import Character, CharacterStatus
from src.items.item import Item, ItemManager, ItemInstance, ItemType, item_manager
from src.ui.window_system import WindowManager
from src.ui.window_system.facility_menu_window import FacilityMenuWindow
from src.ui.window_system.temple_service_window import TempleServiceWindow
from src.ui.selection_list_ui import ItemSelectionList
from src.ui.base_ui_pygame import ui_manager
# NOTE: UIMenu removed - migrated to TempleServiceWindow
from src.core.config_manager import config_manager
from src.utils.logger import logger

# 教会施設定数
SERVICE_COST_RESURRECTION = 500
SERVICE_COST_ASH_RESTORATION = 1000
SERVICE_COST_BLESSING = 100
SERVICE_COST_CURSE_REMOVAL = 200
SERVICE_COST_POISON_CURE = 50
SERVICE_COST_PARALYSIS_CURE = 80
SERVICE_COST_SLEEP_CURE = 30
SERVICE_COST_ALL_STATUS_CURE = 150
SERVICE_LIST_RECT_X = 100
SERVICE_LIST_RECT_Y = 100
SERVICE_LIST_RECT_WIDTH = 600
SERVICE_LIST_RECT_HEIGHT = 500


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
            'resurrection': SERVICE_COST_RESURRECTION,  # 蘇生
            'ash_restoration': SERVICE_COST_ASH_RESTORATION,  # 灰化回復
            'blessing': SERVICE_COST_BLESSING,  # 祝福
            'curse_removal': SERVICE_COST_CURSE_REMOVAL,  # 呪い解除
            'poison_cure': SERVICE_COST_POISON_CURE,   # 毒治療
            'paralysis_cure': SERVICE_COST_PARALYSIS_CURE,  # 麻痺治療
            'sleep_cure': SERVICE_COST_SLEEP_CURE,    # 睡眠治療
            'all_status_cure': SERVICE_COST_ALL_STATUS_CURE,  # 全状態異常治療
        }
    
    def _create_facility_menu_config(self):
        """共通の_create_facility_menu_config実装"""
        return self._create_temple_menu_config()
    
    def _create_temple_menu_config(self):
        """Temple用のFacilityMenuWindow設定を作成"""
        menu_items = [
            {
                'id': 'resurrection',
                'label': "蘇生サービス",
                'type': 'action',
                'enabled': self.current_party is not None
            },
            {
                'id': 'healing_services',
                'label': "治療・祝福サービス",
                'type': 'action',
                'enabled': self.current_party is not None
            },
            {
                'id': 'talk_priest',
                'label': "神父と話す",
                'type': 'action',
                'enabled': True
            },
            {
                'id': 'prayerbook_shop',
                'label': "祈祷書購入",
                'type': 'action',
                'enabled': True
            },
            {
                'id': 'exit',
                'label': config_manager.get_text("menu.exit"),
                'type': 'exit',
                'enabled': True
            }
        ]
        
        return {
            'facility_type': FacilityType.TEMPLE.value,
            'facility_name': config_manager.get_text("facility.temple"),
            'menu_items': menu_items,
            'party': self.current_party,
            'show_party_info': True,
            'show_gold': True
        }
    
    def show_menu(self):
        """Templeメインメニューを表示（FacilityMenuWindow使用）"""
        window_manager = WindowManager.get_instance()
        
        # メニュー設定を作成
        menu_config = self._create_facility_menu_config()
        
        # WindowManagerの正しい使用パターン: create_window -> show_window
        temple_window = window_manager.create_window(
            FacilityMenuWindow,
            'temple_main_menu',
            facility_config=menu_config
        )
        
        # メッセージハンドラーを設定
        temple_window.message_handler = self.handle_facility_message
        
        # ウィンドウを表示
        window_manager.show_window(temple_window, push_to_stack=True)
        
        logger.info("教会に入りました")
    
    def handle_facility_message(self, message_type: str, data: dict) -> bool:
        """FacilityMenuWindowからのメッセージを処理"""
        if message_type == 'menu_item_selected':
            item_id = data.get('id')
            
            if item_id == 'resurrection':
                return self._show_resurrection_menu()
            elif item_id == 'healing_services':
                return self._show_healing_services()
            elif item_id == 'talk_priest':
                return self._talk_to_priest()
            elif item_id == 'prayerbook_shop':
                return self._show_prayerbook_shop()
                
        elif message_type == 'facility_exit_requested':
            return self._handle_exit()
            
        return False
    
    def _handle_exit(self) -> bool:
        """施設退場処理"""
        logger.info("教会から出ました")
        
        # WindowManagerでウィンドウを閉じる
        window_manager = WindowManager.get_instance()
        if window_manager.get_active_window():
            window_manager.go_back()
            
        return True
    
    
    def _on_enter(self):
        """教会入場時の処理"""
        logger.info("教会に入りました")
    
    def _on_exit(self):
        """教会退場時の処理"""
        logger.info("教会から出ました")
    
    def _show_resurrection_menu(self):
        """蘇生メニューを表示（TempleServiceWindow使用）"""
        if not self.current_party:
            self._show_error_message("パーティが設定されていません")
            return
        
        # TempleServiceWindow設定を作成
        temple_config = {
            'parent_facility': self,
            'current_party': self.current_party,
            'service_types': ['resurrection'],
            'title': '蘇生サービス'
        }
        
        # TempleServiceWindowを作成
        resurrection_window = TempleServiceWindow('temple_resurrection', temple_config)
        
        # WindowManagerで表示
        window_manager = WindowManager.get_instance()
        window_manager.show_window(resurrection_window, push_to_stack=True)
        
        logger.info("蘇生サービスウィンドウを表示しました")
    
    def _show_healing_services(self):
        """治療・祝福サービス統合メニューを表示（TempleServiceWindow使用）"""
        if not self.current_party:
            self._show_error_message("パーティが設定されていません")
            return
        
        # TempleServiceWindow設定を作成
        temple_config = {
            'parent_facility': self,
            'current_party': self.current_party,
            'service_types': ['status_cure', 'blessing'],
            'title': '治療・祝福サービス'
        }
        
        # TempleServiceWindowを作成
        healing_window = TempleServiceWindow('temple_healing', temple_config)
        
        # WindowManagerで表示
        window_manager = WindowManager.get_instance()
        window_manager.show_window(healing_window, push_to_stack=True)
        
        logger.info("治療・祝福サービスウィンドウを表示しました")
    
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
            lambda confirmed=None: self._perform_resurrection(character, cost) if confirmed else None
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
            lambda confirmed=None: self._perform_ash_restoration(character, cost) if confirmed else None
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
            self._show_dialog(
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
                        'command': self._back_to_main_menu_from_blessing_dialog
                    }
                ]
            )
        else:
            self._show_dialog(
                "blessing_dialog",
                "祝福サービス",
                blessing_info + "\n※ ゴールドが不足しています",
                buttons=[
                    {
                        'text': "戻る",
                        'command': self._back_to_main_menu_from_blessing_dialog
                    }
                ]
            )
    
    def _close_blessing_dialog(self):
        """祝福ダイアログを閉じてメインメニューに戻る"""
        self._close_dialog()
    
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
    
    
    def _show_prayerbook_shop(self):
        """祈祷書購入ショップをリスト型UIで表示"""
        # 祈祷書（SPELLBOOK）タイプのアイテムを取得
        prayerbook_items = item_manager.get_items_by_type(ItemType.SPELLBOOK)
        
        if not prayerbook_items:
            self._show_error_message("現在、祈祷書の在庫がありません")
            return
        
        self._show_prayerbook_list_ui(prayerbook_items)
    
    def _show_prayerbook_list_ui(self, prayerbook_items: List[Item]):
        """祈祷書一覧をリスト型UIで表示"""
        # UISelectionListを使用したリスト型UI
        list_rect = pygame.Rect(SERVICE_LIST_RECT_X, SERVICE_LIST_RECT_Y, SERVICE_LIST_RECT_WIDTH, SERVICE_LIST_RECT_HEIGHT)
        
        # pygame_gui_managerが存在しない場合（テスト環境など）は処理をスキップ
        if not self._check_pygame_gui_manager():
            self._show_error_message("祈祷書購入メニューの表示に失敗しました。")
            return
        
        self.prayerbook_selection_list = ItemSelectionList(
            relative_rect=list_rect,
            manager=ui_manager.pygame_gui_manager,
            title="祈祷書購入"
        )
        
        # 祈祷書を追加
        for item in prayerbook_items:
            display_name = f"📜 {item.get_name()} - {item.price}G"
            self.prayerbook_selection_list.add_item_data(item, display_name)
        
        # コールバック設定
        self.prayerbook_selection_list.on_item_selected = self._on_prayerbook_selected_for_purchase
        self.prayerbook_selection_list.on_item_details = self._show_prayerbook_details
        
        # 表示
        self.prayerbook_selection_list.show()
    
    def _on_prayerbook_selected_for_purchase(self, item):
        """購入用祈祷書選択時のコールバック"""
        self._hide_prayerbook_selection_list()
        self._show_prayerbook_details(item)
    
    def _hide_prayerbook_selection_list(self):
        """祈祷書選択リストを非表示"""
        if hasattr(self, 'prayerbook_selection_list') and self.prayerbook_selection_list:
            self.prayerbook_selection_list.hide()
            self.prayerbook_selection_list.kill()
            self.prayerbook_selection_list = None
    
    def _handle_ui_selection_events(self, event: pygame.event.Event) -> bool:
        """UISelectionListのイベント処理をオーバーライド"""
        # 祈祷書購入リスト
        if hasattr(self, 'prayerbook_selection_list') and self.prayerbook_selection_list and self.prayerbook_selection_list.handle_event(event):
            return True
        
        return False
    
    def _cleanup_temple_ui(self):
        """教会UIのクリーンアップ（pygame版では不要）"""
        # pygame版では自動的に管理されるため、特別なクリーンアップは不要
        pass
    
    def _cleanup_and_return_to_main_temple(self):
        """UIをクリーンアップしてメインメニューに戻る"""
        # pygame版では単純にメインメニューに戻る
        self._show_main_menu()
    
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
            
            self._show_dialog(
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
                        'command': self._back_to_main_menu_from_prayerbook_dialog
                    }
                ]
            )
        else:
            details += "\n※ ゴールドが不足しています"
            
            self._show_dialog(
                "prayerbook_detail_dialog",
                "祈祷書詳細",
                details,
                buttons=[
                    {
                        'text': "戻る",
                        'command': self._back_to_main_menu_from_prayerbook_dialog
                    }
                ]
            )
    
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
            message,
            buttons=[
                {
                    'text': config_manager.get_text("menu.back"),
                    'command': self._back_to_main_menu_from_priest_dialog
                }
            ]
        )
    
    # UIMenu削除済み: _show_submenu()と_back_to_main_menu_from_submenu()はWindowSystem移行により不要
    
    # UIMenu削除済み: _show_status_cure_menu()は_show_healing_services()に統合されました
    
    # UIMenu削除済み: _show_character_status_cure()は_show_healing_services()に統合されました
    
    def _cure_specific_status(self, character: Character, effect_type, cost: int):
        """特定の状態異常を治療"""
        if not self.current_party:
            return
        
        if self.current_party.gold < cost:
            self._show_error_message("ゴールドが不足しています")
            return
        
        # 治療処理
        status_effects = character.get_status_effects()
        success, result = status_effects.remove_effect(effect_type, character)
        
        if success:
            self.current_party.gold -= cost
            
            effect_name = self._get_status_effect_name(effect_type)
            message = (
                f"{character.name}の{effect_name}を治療しました！\n\n"
                f"神の力により、{character.name}は\n"
                f"{effect_name}から解放されました。\n\n"
                f"治療費: {cost}G\n"
                f"残りゴールド: {self.current_party.gold}G"
            )
            
            self._show_success_message(message)
            logger.info(f"状態異常治療: {character.name} - {effect_type.value}")
        else:
            self._show_error_message("治療に失敗しました")
    
    def _cure_all_character_status(self, character: Character, cost: int):
        """キャラクターの全状態異常を治療"""
        if not self.current_party:
            return
        
        if self.current_party.gold < cost:
            self._show_error_message("ゴールドが不足しています")
            return
        
        # 全状態異常治療
        status_effects = character.get_status_effects()
        cured_effects = status_effects.cure_negative_effects(character)
        
        if cured_effects:
            self.current_party.gold -= cost
            
            message = (
                f"{character.name}の全ての状態異常を治療しました！\n\n"
                f"神の力により、{character.name}は\n"
                f"全ての苦痛から解放されました。\n\n"
                f"治療費: {cost}G\n"
                f"残りゴールド: {self.current_party.gold}G"
            )
            
            self._show_success_message(message)
            logger.info(f"全状態異常治療: {character.name}")
        else:
            self._show_error_message("治療できる状態異常がありませんでした")
    
    def _cure_all_party_status(self):
        """パーティ全体の状態異常治療"""
        if not self.current_party:
            return
        
        # 治療対象キャラクターを取得
        affected_characters = []
        for character in self.current_party.get_all_characters():
            if character.status in [CharacterStatus.GOOD, CharacterStatus.INJURED]:
                status_effects = character.get_status_effects()
                if status_effects.active_effects:
                    affected_characters.append(character)
        
        if not affected_characters:
            self._show_error_message("治療が必要なキャラクターがいません")
            return
        
        total_cost = self.service_costs['all_status_cure'] * len(affected_characters)
        
        if self.current_party.gold < total_cost:
            self._show_error_message("ゴールドが不足しています")
            return
        
        # 全体治療処理
        cured_count = 0
        for character in affected_characters:
            status_effects = character.get_status_effects()
            cured_effects = status_effects.cure_negative_effects(character)
            if cured_effects:
                cured_count += 1
        
        if cured_count > 0:
            self.current_party.gold -= total_cost
            
            message = (
                f"パーティ全体の状態異常を治療しました！\n\n"
                f"{cured_count}人のキャラクターが\n"
                f"神の力により癒されました。\n\n"
                f"治療費: {total_cost}G\n"
                f"残りゴールド: {self.current_party.gold}G"
            )
            
            self._show_success_message(message)
            logger.info(f"パーティ全体状態異常治療: {cured_count}人")
        else:
            self._show_error_message("治療できる状態異常がありませんでした")
    
    def _get_status_effect_name(self, effect_type) -> str:
        """状態異常の日本語名を取得"""
        from src.effects.status_effects import StatusEffectType
        
        names = {
            StatusEffectType.POISON: "毒",
            StatusEffectType.PARALYSIS: "麻痺", 
            StatusEffectType.SLEEP: "睡眠",
            StatusEffectType.CONFUSION: "混乱",
            StatusEffectType.CHARM: "魅了",
            StatusEffectType.FEAR: "恐怖",
            StatusEffectType.BLIND: "盲目",
            StatusEffectType.SILENCE: "沈黙",
            StatusEffectType.STONE: "石化",
            StatusEffectType.SLOW: "減速"
        }
        
        return names.get(effect_type, effect_type.value)
    
    def _get_status_cure_cost(self, effect_type) -> int:
        """状態異常治療の費用を取得"""
        from src.effects.status_effects import StatusEffectType
        
        cost_map = {
            StatusEffectType.POISON: self.service_costs['poison_cure'],
            StatusEffectType.PARALYSIS: self.service_costs['paralysis_cure'],
            StatusEffectType.SLEEP: self.service_costs['sleep_cure'],
            StatusEffectType.CONFUSION: 100,
            StatusEffectType.CHARM: 120,
            StatusEffectType.FEAR: 60,
            StatusEffectType.BLIND: 80,
            StatusEffectType.SILENCE: 90,
            StatusEffectType.STONE: 200,
            StatusEffectType.SLOW: 40
        }
        
        return cost_map.get(effect_type, 100)
    
    def _back_to_main_menu_from_blessing_dialog(self):
        """祝福ダイアログからメインメニューに戻る"""
        self._close_dialog()
        if self.main_menu:
            ui_mgr = self._get_effective_ui_manager()
            if ui_mgr:
                ui_mgr.show_menu(self.main_menu.menu_id, modal=True)
    
    def _back_to_main_menu_from_priest_dialog(self):
        """神父会話ダイアログからメインメニューに戻る"""
        self._close_dialog()
        if self.main_menu:
            ui_mgr = self._get_effective_ui_manager()
            if ui_mgr:
                ui_mgr.show_menu(self.main_menu.menu_id, modal=True)
    
    def _back_to_main_menu_from_prayerbook_dialog(self):
        """祈祷書ダイアログからメインメニューに戻る"""
        self._close_dialog()
        if self.main_menu:
            ui_mgr = self._get_effective_ui_manager()
            if ui_mgr:
                ui_mgr.show_menu(self.main_menu.menu_id, modal=True)