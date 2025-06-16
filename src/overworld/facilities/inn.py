"""宿屋"""

from typing import Dict, List, Optional, Any
from src.overworld.base_facility import BaseFacility, FacilityType
from src.character.party import Party
from src.ui.base_ui import UIMenu, UIDialog, UIInputDialog, ui_manager
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
    
    def _change_party_name(self):
        """パーティ名変更機能"""
        if not self.current_party:
            self._show_dialog(
                "no_party_error_dialog",
                "エラー",
                "現在パーティが存在しません。\n"
                "まず冒険者ギルドでパーティを作成してください。"
            )
            return
        
        # 現在のパーティ名を取得
        current_name = self.current_party.name if self.current_party.name else "無名のパーティ"
        
        # パーティ名変更ダイアログを表示
        name_input_dialog = UIInputDialog(
            "party_name_input_dialog",
            "パーティ名変更",
            f"現在のパーティ名: {current_name}\n\n"
            "新しいパーティ名を入力してください:",
            initial_text=current_name,
            placeholder="パーティ名",
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
                "入力エラー",
                "有効なパーティ名を入力してください。\n"
                "名前は1文字以上30文字以下で入力してください。"
            )
            return
        
        # パーティ名を更新
        old_name = self.current_party.name
        self.current_party.name = validated_name
        
        # 入力ダイアログを閉じる
        ui_manager.hide_element("party_name_input_dialog")
        ui_manager.unregister_element("party_name_input_dialog")
        
        # 成功メッセージを表示
        success_message = (
            f"パーティ名を変更しました！\n\n"
            f"旧名: {old_name}\n"
            f"新名: {validated_name}\n\n"
            "素晴らしい名前ですね！\n"
            "きっと伝説の冒険者になれますよ！"
        )
        
        self._show_dialog(
            "name_change_success_dialog",
            "パーティ名変更完了",
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
            return "勇者一行"  # デフォルト名
        
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
            return "勇者一行"
        
        return name