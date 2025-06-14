"""宿屋"""

from typing import Dict, List, Optional, Any
from src.overworld.base_facility import BaseFacility, FacilityType
from src.character.party import Party
from src.ui.base_ui import UIMenu, UIDialog, ui_manager
from src.core.config_manager import config_manager
from src.utils.logger import logger


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
            "宿泊について",
            self._show_lodging_info
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
                "冒険について",
                "「最近のダンジョンは昔と比べて\n"
                "少し変わったようですね。\n"
                "魔物も強くなっているという話ですが、\n"
                "皆さんも以前より逞しくなっています。」"
            ),
            (
                "町の様子",
                "「この町には優秀な商人や\n"
                "信頼できる神官がいます。\n"
                "冒険前の準備は怠らないことです。\n"
                "装備と心の準備、両方が大切ですよ。」"
            ),
            (
                "宿屋の歴史",
                "「この宿屋は私の祖父の代から\n"
                "続いています。\n"
                "多くの冒険者がここから旅立ち、\n"
                "そして無事に帰ってきました。」"
            )
        ]
        
        # ランダムにメッセージを選択
        import random
        title, message = random.choice(messages)
        
        self._show_dialog(
            "innkeeper_dialog",
            f"宿屋の主人 - {title}",
            message
        )
    
    def _show_travel_info(self):
        """旅の情報を表示"""
        travel_info = (
            "【旅の心得】\n\n"
            "• 地上部に戻ると体力・魔力が自動回復します\n"
            "• 状態異常も（死亡・灰化以外は）治癒されます\n"
            "• 冒険前は装備と消耗品の準備を忘れずに\n"
            "• パーティの編成バランスも重要です\n\n"
            "【施設案内】\n"
            "• 冒険者ギルド：キャラクター作成・パーティ編成\n"
            "• 商店：武器・防具・消耗品の購入\n"
            "• 教会：蘇生・治療・祝福\n"
            "• 魔術師ギルド：魔法の習得・鑑定\n\n"
            "安全な冒険を！"
        )
        
        self._show_dialog(
            "travel_info_dialog",
            "旅の情報",
            travel_info
        )
    
    def _show_tavern_rumors(self):
        """酒場の噂話を表示"""
        rumors = [
            (
                "ダンジョンの話",
                "「最近、ダンジョンの奥で\n"
                "光る宝箱を見たという話があります。\n"
                "でも、そこまで行くには\n"
                "相当な実力が必要だとか...」"
            ),
            (
                "魔物の話",
                "「昔より魔物が賢くなっているという\n"
                "噂があります。\n"
                "罠を仕掛けたり、集団で襲ってきたり。\n"
                "油断は禁物ですね。」"
            ),
            (
                "伝説の装備",
                "「昔の英雄が使っていたという\n"
                "伝説の装備が、まだダンジョンの\n"
                "どこかに眠っているらしいです。\n"
                "見つけられたら一攫千金ですね！」"
            ),
            (
                "他の冒険者",
                "「この間、新人の冒険者パーティが\n"
                "見事にダンジョンを攻略したそうです。\n"
                "準備と連携の大切さを\n"
                "改めて感じますね。」"
            ),
            (
                "町の商人",
                "「商店の主人は元冒険者だそうです。\n"
                "だから冒険者の気持ちがよく分かって、\n"
                "良い装備を適正価格で\n"
                "売ってくれるんですよ。」"
            )
        ]
        
        # ランダムに噂を選択
        import random
        title, rumor = random.choice(rumors)
        
        self._show_dialog(
            "rumor_dialog",
            f"酒場の噂 - {title}",
            rumor
        )
    
    def _show_lodging_info(self):
        """宿泊についての説明"""
        lodging_info = (
            "【宿泊について】\n\n"
            "申し訳ございませんが、現在この町では\n"
            "特別な魔法の効果により、地上部に戻るだけで\n"
            "完全に体力が回復するようになっております。\n\n"
            "そのため、宿泊による休息サービスは\n"
            "一時的に停止させていただいています。\n\n"
            "ご不便をおかけして申し訳ありません。\n"
            "代わりに、旅の情報や美味しい食事で\n"
            "おもてなしいたします！\n\n"
            "※ システム上、地上部帰還時に自動回復するため\n"
            "　 宿屋での休息機能は提供していません"
        )
        
        self._show_dialog(
            "lodging_info_dialog",
            "宿泊について",
            lodging_info
        )