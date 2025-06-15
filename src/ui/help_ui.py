"""ヘルプ・チュートリアルUIシステム"""

from typing import Dict, List, Optional, Any, Callable
from enum import Enum

from src.ui.base_ui import UIElement, UIButton, UIText, UIMenu, UIDialog, UIState, ui_manager
from src.core.config_manager import config_manager
from src.core.input_manager import InputAction, GamepadButton
from src.utils.logger import logger


class HelpCategory(Enum):
    """ヘルプカテゴリ"""
    BASIC_CONTROLS = "basic_controls"
    DUNGEON_EXPLORATION = "dungeon_exploration"
    COMBAT_SYSTEM = "combat_system"
    MAGIC_SYSTEM = "magic_system"
    EQUIPMENT_SYSTEM = "equipment_system"
    INVENTORY_MANAGEMENT = "inventory_management"
    CHARACTER_DEVELOPMENT = "character_development"
    OVERWORLD_NAVIGATION = "overworld_navigation"


class HelpUI:
    """ヘルプ・チュートリアルUI管理クラス"""
    
    def __init__(self):
        # UI状態
        self.is_open = False
        self.current_category: Optional[HelpCategory] = None
        self.callback_on_close: Optional[Callable] = None
        
        # ヘルプコンテンツ
        self.help_content = self._initialize_help_content()
        
        logger.info("HelpUIを初期化しました")
    
    def _initialize_help_content(self) -> Dict[HelpCategory, Dict[str, Any]]:
        """ヘルプコンテンツを初期化"""
        return {
            HelpCategory.BASIC_CONTROLS: {
                "title": "基本操作",
                "sections": [
                    {
                        "title": "移動操作",
                        "keyboard": [
                            "W / ↑ : 前進",
                            "S / ↓ : 後退",
                            "A / ← : 左移動",
                            "D / → : 右移動",
                            "Q : 左回転",
                            "E : 右回転"
                        ],
                        "gamepad": [
                            "左スティック : 移動",
                            "右スティック : 視点回転",
                            "十字キー : 方向移動"
                        ]
                    },
                    {
                        "title": "UI操作",
                        "keyboard": [
                            "TAB : メインメニュー",
                            "I : インベントリ",
                            "M : 魔法",
                            "C : 装備",
                            "ESC : キャンセル/戻る",
                            "Enter : 決定"
                        ],
                        "gamepad": [
                            "START : メインメニュー",
                            "A / × : 決定",
                            "B / ○ : キャンセル",
                            "Y / △ : アクション",
                            "X / □ : 詳細"
                        ]
                    }
                ]
            },
            HelpCategory.DUNGEON_EXPLORATION: {
                "title": "ダンジョン探索",
                "sections": [
                    {
                        "title": "探索の基本",
                        "content": [
                            "• ダンジョンは3Dビューで探索します",
                            "• 壁に沿って移動し、隠し扉を探しましょう",
                            "• 定期的に休憩してHP/MPを回復しましょう",
                            "• 宝箱やアイテムを見つけたら調べてみましょう"
                        ]
                    },
                    {
                        "title": "危険への対処",
                        "content": [
                            "• モンスターとのエンカウントに注意",
                            "• 罠がある可能性があります",
                            "• HPが低くなったら地上部に戻りましょう",
                            "• セーブポイントを活用しましょう"
                        ]
                    }
                ]
            },
            HelpCategory.COMBAT_SYSTEM: {
                "title": "戦闘システム",
                "sections": [
                    {
                        "title": "戦闘の基本",
                        "content": [
                            "• ターン制戦闘システムです",
                            "• 敏捷性が行動順に影響します",
                            "• 攻撃、魔法、アイテム、逃走が選択可能",
                            "• 敵の弱点を見つけて有効活用しましょう"
                        ]
                    },
                    {
                        "title": "戦闘のコツ",
                        "content": [
                            "• 前衛は攻撃・防御、後衛は魔法・回復",
                            "• MP管理は非常に重要です",
                            "• ステータス効果を活用しましょう",
                            "• 強敵との戦いでは逃走も選択肢です"
                        ]
                    }
                ]
            },
            HelpCategory.MAGIC_SYSTEM: {
                "title": "魔法システム",
                "sections": [
                    {
                        "title": "魔法の基本",
                        "content": [
                            "• 魔法はスロット制です",
                            "• 習得した魔法をスロットに装備して使用",
                            "• MP消費量に注意しましょう",
                            "• 学派によって使用可能クラスが異なります"
                        ]
                    },
                    {
                        "title": "魔法の習得",
                        "content": [
                            "• ギルドや神殿で魔法を習得",
                            "• キャラクターレベルが必要",
                            "• 金貨を支払って習得",
                            "• 知力・信仰値が魔法効果に影響"
                        ]
                    }
                ]
            },
            HelpCategory.EQUIPMENT_SYSTEM: {
                "title": "装備システム",
                "sections": [
                    {
                        "title": "装備の基本",
                        "content": [
                            "• 武器、防具、アクセサリの3種類",
                            "• 各キャラクターに4つの装備スロット",
                            "• 装備により能力値が向上",
                            "• クラス制限がある装備もあります"
                        ]
                    },
                    {
                        "title": "装備の管理",
                        "content": [
                            "• 装備画面で変更・比較が可能",
                            "• 効果プレビューで差分を確認",
                            "• 耐久度に注意しましょう",
                            "• 鑑定が必要なアイテムもあります"
                        ]
                    }
                ]
            },
            HelpCategory.INVENTORY_MANAGEMENT: {
                "title": "インベントリ管理",
                "sections": [
                    {
                        "title": "アイテム管理",
                        "content": [
                            "• 各キャラクターが個別のインベントリを保持",
                            "• アイテムの使用、装備、破棄が可能",
                            "• 重量制限があります",
                            "• スタック可能なアイテムもあります"
                        ]
                    },
                    {
                        "title": "アイテムの活用",
                        "content": [
                            "• 回復アイテムは戦闘・探索時に重要",
                            "• 鑑定アイテムで未知の装備を特定",
                            "• 不要なアイテムは売却しましょう",
                            "• 消耗品の補充を忘れずに"
                        ]
                    }
                ]
            },
            HelpCategory.CHARACTER_DEVELOPMENT: {
                "title": "キャラクター育成",
                "sections": [
                    {
                        "title": "レベルアップ",
                        "content": [
                            "• 経験値を獲得してレベルアップ",
                            "• 能力値の上昇",
                            "• 新しい魔法の習得が可能に",
                            "• クラス転職の条件が解放"
                        ]
                    },
                    {
                        "title": "能力値の意味",
                        "content": [
                            "• 筋力: 物理攻撃力・持運重量",
                            "• 敏捷性: 行動速度・回避率",
                            "• 知力: 魔法攻撃力・魔法習得",
                            "• 信仰: 回復魔法効果・魔法抵抗",
                            "• 運: クリティカル率・宝箱発見"
                        ]
                    }
                ]
            },
            HelpCategory.OVERWORLD_NAVIGATION: {
                "title": "地上部ナビゲーション",
                "sections": [
                    {
                        "title": "施設の利用",
                        "content": [
                            "• ギルド: パーティ編成・依頼受注",
                            "• 宿屋: 休息・HP/MP回復・セーブ",
                            "• 商店: アイテム売買",
                            "• 神殿: 蘇生・状態異常回復・魔法習得",
                            "• 酒場: 情報収集・新キャラ勧誘"
                        ]
                    },
                    {
                        "title": "冒険の準備",
                        "content": [
                            "• パーティ編成は戦略的に",
                            "• 十分な回復アイテムを準備",
                            "• 装備の確認と強化",
                            "• 魔法スロットの設定",
                            "• セーブを忘れずに"
                        ]
                    }
                ]
            }
        }
    
    def show_help_menu(self):
        """ヘルプメインメニューを表示"""
        help_menu = UIMenu("help_main", "ヘルプ・チュートリアル")
        
        # カテゴリ別ヘルプ
        for category in HelpCategory:
            content = self.help_content[category]
            help_menu.add_menu_item(
                content["title"],
                self._show_category_help,
                [category]
            )
        
        # クイックリファレンス
        help_menu.add_menu_item(
            "クイックリファレンス",
            self._show_quick_reference
        )
        
        # 操作ガイド
        help_menu.add_menu_item(
            "キー操作ガイド",
            self._show_controls_guide
        )
        
        help_menu.add_menu_item(
            config_manager.get_text("menu.close"),
            self._close_help_ui
        )
        
        ui_manager.register_element(help_menu)
        ui_manager.show_element(help_menu.element_id, modal=True)
        self.is_open = True
        
        logger.info("ヘルプメニューを表示")
    
    def _show_category_help(self, category: HelpCategory):
        """カテゴリ別ヘルプを表示"""
        self.current_category = category
        content = self.help_content[category]
        
        category_menu = UIMenu("help_category", content["title"])
        
        # セクション別に表示
        sections = content.get("sections", [])
        for i, section in enumerate(sections):
            section_title = section.get("title", f"セクション{i+1}")
            category_menu.add_menu_item(
                section_title,
                self._show_section_detail,
                [section]
            )
        
        category_menu.add_menu_item(
            "戻る",
            self._back_to_main_help
        )
        
        ui_manager.register_element(category_menu)
        ui_manager.show_element(category_menu.element_id, modal=True)
    
    def _show_section_detail(self, section: Dict[str, Any]):
        """セクション詳細を表示"""
        title = section.get("title", "詳細")
        
        details = f"【{title}】\\n\\n"
        
        # コンテンツ表示
        if "content" in section:
            for item in section["content"]:
                details += f"{item}\\n"
        
        # キーボード操作
        if "keyboard" in section:
            details += "\\n【キーボード】\\n"
            for control in section["keyboard"]:
                details += f"{control}\\n"
        
        # ゲームパッド操作
        if "gamepad" in section:
            details += "\\n【ゲームパッド】\\n"
            for control in section["gamepad"]:
                details += f"{control}\\n"
        
        dialog = UIDialog(
            "help_section_detail",
            title,
            details,
            buttons=[
                {"text": "閉じる", "command": self._close_dialog}
            ]
        )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)
    
    def _show_quick_reference(self):
        """クイックリファレンスを表示"""
        reference_text = "【クイックリファレンス】\\n\\n"
        
        reference_text += "■ 緊急時の操作\\n"
        reference_text += "ESC / Bボタン : メニューを閉じる\\n"
        reference_text += "TAB / STARTボタン : メインメニュー\\n"
        reference_text += "I / Yボタン : インベントリ\\n"
        reference_text += "H : ヘルプ表示\\n\\n"
        
        reference_text += "■ 戦闘中の操作\\n"
        reference_text += "数字キー1-4 : 行動選択\\n"
        reference_text += "R : 逃走\\n"
        reference_text += "Space : 決定\\n\\n"
        
        reference_text += "■ 探索中の操作\\n"
        reference_text += "WASD : 移動\\n"
        reference_text += "QE : 回転\\n"
        reference_text += "F : 調べる\\n"
        reference_text += "C : キャンプ\\n\\n"
        
        reference_text += "■ ステータス確認\\n"
        reference_text += "S : ステータス\\n"
        reference_text += "M : 魔法\\n"
        reference_text += "C : 装備\\n"
        reference_text += "V : 状態効果"
        
        dialog = UIDialog(
            "quick_reference",
            "クイックリファレンス",
            reference_text,
            buttons=[
                {"text": "閉じる", "command": self._close_dialog}
            ]
        )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)
    
    def _show_controls_guide(self):
        """操作ガイドを表示"""
        guide_text = "【操作ガイド】\\n\\n"
        
        guide_text += "■ 基本的な考え方\\n"
        guide_text += "• キーボード操作を基本とし、ゲームパッドは補助\\n"
        guide_text += "• メニュー操作は矢印キー + Enter\\n"
        guide_text += "• 探索は WASD + マウス（または QE）\\n"
        guide_text += "• 緊急時は ESC で安全にメニューへ\\n\\n"
        
        guide_text += "■ 効率的な操作のコツ\\n"
        guide_text += "• ショートカットキーを覚えましょう\\n"
        guide_text += "• ダンジョンでは TAB からメニューへ素早くアクセス\\n"
        guide_text += "• 戦闘中は数字キーで素早く選択\\n"
        guide_text += "• インベントリは I キーで即座に開けます\\n\\n"
        
        guide_text += "■ カスタマイズ\\n"
        guide_text += "• 設定画面でキーバインドを変更可能\\n"
        guide_text += "• ゲームパッドの感度調整ができます\\n"
        guide_text += "• 左利きの方向けのレイアウトも用意\\n\\n"
        
        guide_text += "■ トラブルシューティング\\n"
        guide_text += "• 操作が効かない場合は一度 ESC を押してください\\n"
        guide_text += "• ゲームパッドが認識されない場合は設定を確認\\n"
        guide_text += "• キーが重複している場合は警告が表示されます"
        
        dialog = UIDialog(
            "controls_guide",
            "操作ガイド",
            guide_text,
            buttons=[
                {"text": "閉じる", "command": self._close_dialog}
            ]
        )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)
    
    def show_context_help(self, context: str):
        """コンテキスト別ヘルプを表示"""
        context_help = {
            "combat": "戦闘中です。攻撃・魔法・アイテム・逃走から選択してください。",
            "dungeon": "ダンジョン探索中です。WASD で移動、F で調べる、TAB でメニューです。",
            "overworld": "地上部です。各施設をクリックして利用できます。",
            "inventory": "インベントリ画面です。アイテムを選択して使用・装備・破棄ができます。",
            "equipment": "装備画面です。装備を変更して能力値を向上させましょう。",
            "magic": "魔法画面です。習得した魔法をスロットに装備して使用します。"
        }
        
        help_text = context_help.get(context, "このコンテキストのヘルプは未実装です。")
        
        dialog = UIDialog(
            "context_help",
            "操作ヘルプ",
            help_text,
            buttons=[
                {"text": "OK", "command": self._close_dialog},
                {"text": "詳細ヘルプ", "command": self.show_help_menu}
            ]
        )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)
    
    def show_first_time_help(self):
        """初回起動時のヘルプを表示"""
        welcome_text = "【ようこそダンジョンRPGへ！】\\n\\n"
        welcome_text += "これは本格的な3Dダンジョン探索RPGです。\\n\\n"
        welcome_text += "■ 基本的な流れ\\n"
        welcome_text += "1. 地上部でパーティを編成\\n"
        welcome_text += "2. 装備・アイテムを準備\\n"
        welcome_text += "3. ダンジョンに挑戦\\n"
        welcome_text += "4. 戦闘・探索でレベルアップ\\n"
        welcome_text += "5. より深い階層に挑戦\\n\\n"
        welcome_text += "■ 操作方法\\n"
        welcome_text += "• H キー: いつでもヘルプを表示\\n"
        welcome_text += "• TAB キー: メインメニュー\\n"
        welcome_text += "• ESC キー: 戻る・キャンセル\\n\\n"
        welcome_text += "困ったときは H キーでヘルプを確認してください！"
        
        dialog = UIDialog(
            "first_time_help",
            "ゲームガイド",
            welcome_text,
            buttons=[
                {"text": "始める", "command": self._close_dialog},
                {"text": "詳細ヘルプ", "command": self.show_help_menu}
            ]
        )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)
    
    def show(self):
        """ヘルプUIを表示"""
        self.show_help_menu()
    
    def hide(self):
        """ヘルプUIを非表示"""
        try:
            ui_manager.hide_element("help_main")
        except:
            pass
        self.is_open = False
        logger.debug("ヘルプUIを非表示にしました")
    
    def destroy(self):
        """ヘルプUIを破棄"""
        self.hide()
        self.current_category = None
        logger.debug("HelpUIを破棄しました")
    
    def set_close_callback(self, callback: Callable):
        """閉じるコールバックを設定"""
        self.callback_on_close = callback
    
    def _back_to_main_help(self):
        """メインヘルプに戻る"""
        self.show_help_menu()
    
    def _close_help_ui(self):
        """ヘルプUIを閉じる"""
        self.hide()
        if self.callback_on_close:
            self.callback_on_close()
    
    def _close_dialog(self):
        """ダイアログを閉じる"""
        ui_manager.hide_all_elements()


# グローバルインスタンス
help_ui = HelpUI()