"""ヘルプコンテンツ管理クラス

Fowler Extract Classパターンにより、HelpWindowからヘルプコンテンツ管理に関する責任を抽出。
単一責任の原則に従い、ヘルプコンテンツの管理・取得・多言語化機能を専門的に扱う。
"""

from typing import Dict, List, Optional, Any
from enum import Enum

from src.ui.window_system.help_enums import HelpCategory, HelpContext
from src.core.config_manager import config_manager
from src.utils.logger import logger


class ContentType(Enum):
    """コンテンツタイプ"""
    SECTION = "section"
    QUICK_REFERENCE = "quick_reference"
    CONTROLS_GUIDE = "controls_guide"
    FIRST_TIME_HELP = "first_time_help"


class HelpContentManager:
    """ヘルプコンテンツ管理クラス
    
    ヘルプシステムのコンテンツ管理・多言語化対応・動的コンテンツ生成を担当。
    Extract Classパターンにより、HelpWindowからコンテンツ管理ロジックを分離。
    """
    
    def __init__(self):
        """ヘルプコンテンツマネージャー初期化"""
        self.help_categories: Dict[HelpCategory, Dict[str, Any]] = {}
        self.context_help: Dict[HelpContext, Dict[str, Any]] = {}
        self.quick_reference_content: Dict[str, Any] = {}
        self.controls_guide_content: Dict[str, Any] = {}
        self.first_time_help_content: Dict[str, Any] = {}
        
        # コンテンツを初期化
        self._initialize_all_content()
        
        logger.debug("HelpContentManagerを初期化しました")
    
    def _initialize_all_content(self) -> None:
        """全てのヘルプコンテンツを初期化"""
        self._initialize_category_content()
        self._initialize_context_content()
        self._initialize_quick_reference()
        self._initialize_controls_guide()
        self._initialize_first_time_help()
    
    def _initialize_category_content(self) -> None:
        """カテゴリ別ヘルプコンテンツを初期化"""
        self.help_categories = {
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
    
    def _initialize_context_content(self) -> None:
        """コンテキストヘルプコンテンツを初期化"""
        self.context_help = {
            HelpContext.COMBAT: {
                "title": "戦闘中のヘルプ",
                "content": "戦闘中です。攻撃・魔法・アイテム・逃走から選択してください。",
                "tips": [
                    "敵の弱点を狙いましょう",
                    "HP/MPの管理に注意",
                    "ステータス効果を活用"
                ]
            },
            HelpContext.DUNGEON: {
                "title": "ダンジョン探索中のヘルプ",
                "content": "ダンジョン探索中です。WASD で移動、F で調べる、TAB でメニューです。",
                "tips": [
                    "壁に沿って移動",
                    "隠し扉を探す",
                    "定期的に休憩"
                ]
            },
            HelpContext.OVERWORLD: {
                "title": "地上部のヘルプ",
                "content": "地上部です。各施設をクリックして利用できます。",
                "tips": [
                    "宿屋で回復",
                    "商店で装備購入",
                    "ギルドで依頼確認"
                ]
            },
            HelpContext.INVENTORY: {
                "title": "インベントリのヘルプ",
                "content": "インベントリ画面です。アイテムを選択して使用・装備・破棄ができます。",
                "tips": [
                    "重量制限に注意",
                    "不要なアイテムは売却",
                    "スタック可能アイテムをまとめる"
                ]
            },
            HelpContext.EQUIPMENT: {
                "title": "装備画面のヘルプ",
                "content": "装備画面です。装備を変更して能力値を向上させましょう。",
                "tips": [
                    "装備効果をプレビュー",
                    "クラス制限を確認",
                    "耐久度をチェック"
                ]
            },
            HelpContext.MAGIC: {
                "title": "魔法画面のヘルプ",
                "content": "魔法画面です。習得した魔法をスロットに装備して使用します。",
                "tips": [
                    "MP消費量を確認",
                    "スロットレベルに注意",
                    "学派の制限を理解"
                ]
            }
        }
    
    def _initialize_quick_reference(self) -> None:
        """クイックリファレンスコンテンツを初期化"""
        self.quick_reference_content = {
            "title": "クイックリファレンス",
            "sections": {
                "emergency": {
                    "title": "緊急時の操作",
                    "items": [
                        "ESC / Bボタン : メニューを閉じる",
                        "TAB / STARTボタン : メインメニュー",
                        "I / Yボタン : インベントリ",
                        "H : ヘルプ表示"
                    ]
                },
                "combat": {
                    "title": "戦闘中の操作",
                    "items": [
                        "数字キー1-4 : 行動選択",
                        "R : 逃走",
                        "Space : 決定"
                    ]
                },
                "exploration": {
                    "title": "探索中の操作",
                    "items": [
                        "WASD : 移動",
                        "QE : 回転",
                        "F : 調べる",
                        "C : キャンプ"
                    ]
                },
                "status": {
                    "title": "ステータス確認",
                    "items": [
                        "S : ステータス",
                        "M : 魔法",
                        "C : 装備",
                        "V : 状態効果"
                    ]
                }
            }
        }
    
    def _initialize_controls_guide(self) -> None:
        """操作ガイドコンテンツを初期化"""
        self.controls_guide_content = {
            "title": "操作ガイド",
            "sections": {
                "basic_concept": {
                    "title": "基本的な考え方",
                    "items": [
                        "• キーボード操作を基本とし、ゲームパッドは補助",
                        "• メニュー操作は矢印キー + Enter",
                        "• 探索は WASD + マウス（または QE）",
                        "• 緊急時は ESC で安全にメニューへ"
                    ]
                },
                "efficiency_tips": {
                    "title": "効率的な操作のコツ",
                    "items": [
                        "• ショートカットキーを覚えましょう",
                        "• ダンジョンでは TAB からメニューへ素早くアクセス",
                        "• 戦闘中は数字キーで素早く選択",
                        "• インベントリは I キーで即座に開けます"
                    ]
                },
                "customization": {
                    "title": "カスタマイズ",
                    "items": [
                        "• 設定画面でキーバインドを変更可能",
                        "• ゲームパッドの感度調整ができます",
                        "• 左利きの方向けのレイアウトも用意"
                    ]
                },
                "troubleshooting": {
                    "title": "トラブルシューティング",
                    "items": [
                        "• 操作が効かない場合は一度 ESC を押してください",
                        "• ゲームパッドが認識されない場合は設定を確認",
                        "• キーが重複している場合は警告が表示されます"
                    ]
                }
            }
        }
    
    def _initialize_first_time_help(self) -> None:
        """初回起動時ヘルプコンテンツを初期化"""
        self.first_time_help_content = {
            "title": "ようこそダンジョンRPGへ！",
            "intro": "これは本格的な3Dダンジョン探索RPGです。",
            "basic_flow": {
                "title": "基本的な流れ",
                "steps": [
                    "1. 地上部でパーティを編成",
                    "2. 装備・アイテムを準備",
                    "3. ダンジョンに挑戦",
                    "4. 戦闘・探索でレベルアップ",
                    "5. より深い階層に挑戦"
                ]
            },
            "controls": {
                "title": "操作方法",
                "items": [
                    "• H キー: いつでもヘルプを表示",
                    "• TAB キー: メインメニュー",
                    "• ESC キー: 戻る・キャンセル"
                ]
            },
            "footer": "困ったときは H キーでヘルプを確認してください！"
        }
    
    def get_category_content(self, category: HelpCategory) -> Optional[Dict[str, Any]]:
        """カテゴリ別ヘルプコンテンツを取得
        
        Args:
            category: ヘルプカテゴリ
            
        Returns:
            Dict: ヘルプコンテンツ、または None
        """
        return self.help_categories.get(category)
    
    def get_context_content(self, context: HelpContext) -> Optional[Dict[str, Any]]:
        """コンテキストヘルプコンテンツを取得
        
        Args:
            context: ヘルプコンテキスト
            
        Returns:
            Dict: ヘルプコンテンツ、または None
        """
        return self.context_help.get(context)
    
    def get_quick_reference_content(self) -> Dict[str, Any]:
        """クイックリファレンスコンテンツを取得
        
        Returns:
            Dict: クイックリファレンスコンテンツ
        """
        return self.quick_reference_content
    
    def get_controls_guide_content(self) -> Dict[str, Any]:
        """操作ガイドコンテンツを取得
        
        Returns:
            Dict: 操作ガイドコンテンツ
        """
        return self.controls_guide_content
    
    def get_first_time_help_content(self) -> Dict[str, Any]:
        """初回起動時ヘルプコンテンツを取得
        
        Returns:
            Dict: 初回起動時ヘルプコンテンツ
        """
        return self.first_time_help_content
    
    def get_all_categories(self) -> List[HelpCategory]:
        """全てのヘルプカテゴリを取得
        
        Returns:
            List[HelpCategory]: ヘルプカテゴリリスト
        """
        return list(self.help_categories.keys())
    
    def get_localized_text(self, key: str, default: str = "") -> str:
        """多言語化されたテキストを取得
        
        Args:
            key: テキストキー
            default: デフォルトテキスト
            
        Returns:
            str: ローカライズされたテキスト
        """
        try:
            return config_manager.get_text(key)
        except:
            return default