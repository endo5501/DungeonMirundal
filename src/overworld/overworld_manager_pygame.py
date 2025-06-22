"""地上部管理システム（Pygame版）"""

from typing import Optional, Callable
import pygame
from src.character.party import Party
from src.ui.base_ui_pygame import UIMenu, UIButton, UIText
from src.utils.logger import logger
from src.core.config_manager import config_manager


class OverworldManager:
    """地上部管理クラス（Pygame版）"""
    
    def __init__(self):
        self.current_party: Optional[Party] = None
        self.ui_manager = None
        self.input_manager = None
        
        # コールバック
        self.enter_dungeon_callback: Optional[Callable] = None
        self.exit_game_callback: Optional[Callable] = None
        
        # UI要素
        self.main_menu: Optional[UIMenu] = None
        self.settings_menu: Optional[UIMenu] = None
        self.is_active = False
        self.settings_active = False
        
        logger.info("OverworldManager（Pygame版）を初期化しました")
    
    def set_ui_manager(self, ui_manager):
        """UIマネージャーを設定"""
        self.ui_manager = ui_manager
        self._create_main_menu()
        self._create_settings_menu()
    
    def set_input_manager(self, input_manager):
        """入力マネージャーを設定"""
        self.input_manager = input_manager
    
    def set_enter_dungeon_callback(self, callback: Callable):
        """ダンジョン入場コールバックを設定"""
        self.enter_dungeon_callback = callback
    
    def set_exit_game_callback(self, callback: Callable):
        """ゲーム終了コールバックを設定"""
        self.exit_game_callback = callback
    
    def _create_main_menu(self):
        """メインメニューを作成（6つの施設 + 設定画面）"""
        if not self.ui_manager:
            return
        
        # メインメニュー作成（日本語対応フォント使用）
        self.main_menu = UIMenu("overworld_main", "地上マップ")
        
        # 6つの施設ボタンを作成（2列3行レイアウト）
        # 左列
        guild_button = UIButton("guild", "冒険者ギルド", 150, 200, 200, 50)
        guild_button.on_click = self._on_guild
        self.main_menu.add_element(guild_button)
        
        inn_button = UIButton("inn", "宿屋", 150, 270, 200, 50)
        inn_button.on_click = self._on_inn
        self.main_menu.add_element(inn_button)
        
        shop_button = UIButton("shop", "商店", 150, 340, 200, 50)
        shop_button.on_click = self._on_shop
        self.main_menu.add_element(shop_button)
        
        # 右列
        temple_button = UIButton("temple", "教会", 450, 200, 200, 50)
        temple_button.on_click = self._on_temple
        self.main_menu.add_element(temple_button)
        
        magic_guild_button = UIButton("magic_guild", "魔術師ギルド", 450, 270, 200, 50)
        magic_guild_button.on_click = self._on_magic_guild
        self.main_menu.add_element(magic_guild_button)
        
        dungeon_button = UIButton("enter_dungeon", "ダンジョン入口", 450, 340, 200, 50)
        dungeon_button.on_click = self._on_enter_dungeon
        self.main_menu.add_element(dungeon_button)
        
        # 設定画面への案内テキスト
        help_text = UIText("esc_help", "[ESC] 設定画面", 300, 450)
        self.main_menu.add_element(help_text)
        
        # UIマネージャーに追加
        self.ui_manager.add_menu(self.main_menu)
        
        logger.info("オーバーワールドメインメニューを作成しました（6施設対応）")
    
    def _create_settings_menu(self):
        """設定画面を作成"""
        if not self.ui_manager:
            return
        
        # 設定メニュー作成
        self.settings_menu = UIMenu("settings_menu", "設定画面")
        
        # パーティ状況ボタン
        party_status_button = UIButton("party_status", "パーティ状況", 250, 200, 300, 50)
        party_status_button.on_click = self._on_party_status
        self.settings_menu.add_element(party_status_button)
        
        # ゲームを保存ボタン
        save_button = UIButton("save_game", "ゲームを保存", 250, 270, 300, 50)
        save_button.on_click = self._on_save_game
        self.settings_menu.add_element(save_button)
        
        # ゲームをロードボタン
        load_button = UIButton("load_game", "ゲームをロード", 250, 340, 300, 50)
        load_button.on_click = self._on_load_game
        self.settings_menu.add_element(load_button)
        
        # 設定ボタン
        config_button = UIButton("config", "設定", 250, 410, 300, 50)
        config_button.on_click = self._on_config
        self.settings_menu.add_element(config_button)
        
        # 終了ボタン
        exit_button = UIButton("exit_game", "終了", 250, 480, 300, 50)
        exit_button.on_click = self._on_exit_game
        self.settings_menu.add_element(exit_button)
        
        # 戻るボタン
        back_button = UIButton("back_to_overworld", "戻る", 250, 550, 300, 50)
        back_button.on_click = self._on_back_to_overworld
        self.settings_menu.add_element(back_button)
        
        # UIマネージャーに追加（最初は非表示）
        self.ui_manager.add_menu(self.settings_menu)
        self.settings_menu.hide()
        
        logger.info("設定画面メニューを作成しました")
    
    def _on_enter_dungeon(self):
        """ダンジョン入場"""
        logger.info("ダンジョン入場が選択されました")
        if self.enter_dungeon_callback:
            try:
                # メインメニューを隠す
                if self.main_menu:
                    self.main_menu.hide()
                self.is_active = False
                
                # ダンジョンに遷移
                self.enter_dungeon_callback("main_dungeon")
            except Exception as e:
                logger.error(f"ダンジョン入場エラー: {e}")
                # エラーの場合はメニューを再表示
                if self.main_menu:
                    self.main_menu.show()
                self.is_active = True
    
    # === 地上施設ハンドラー ===
    
    def _on_guild(self):
        """冒険者ギルド"""
        logger.info("冒険者ギルドが選択されました")
        try:
            from src.overworld.facilities.guild import AdventurersGuild
            guild = AdventurersGuild()
            guild.enter(self.current_party)
        except Exception as e:
            logger.error(f"冒険者ギルドエラー: {e}")
            logger.info("冒険者ギルドの詳細機能を利用")
    
    def _on_inn(self):
        """宿屋"""
        logger.info("宿屋が選択されました")
        try:
            from src.overworld.facilities.inn import Inn
            inn = Inn()
            inn.enter(self.current_party)
        except Exception as e:
            logger.error(f"宿屋エラー: {e}")
            # 基本的な回復処理をフォールバック
            if self.current_party:
                for character in self.current_party.get_living_characters():
                    character.derived_stats.current_hp = character.derived_stats.max_hp
                    character.derived_stats.current_mp = character.derived_stats.max_mp
                logger.info("パーティを回復しました（簡易版）")
    
    def _on_shop(self):
        """商店"""
        logger.info("商店が選択されました")
        try:
            from src.overworld.facilities.shop import Shop
            shop = Shop()
            shop.enter(self.current_party)
        except Exception as e:
            logger.error(f"商店エラー: {e}")
            logger.info("商店の詳細機能を利用")
    
    def _on_temple(self):
        """教会"""
        logger.info("教会が選択されました")
        try:
            from src.overworld.facilities.temple import Temple
            temple = Temple()
            temple.enter(self.current_party)
        except Exception as e:
            logger.error(f"教会エラー: {e}")
            logger.info("教会の詳細機能を利用")
    
    def _on_magic_guild(self):
        """魔術師ギルド"""
        logger.info("魔術師ギルドが選択されました")
        try:
            from src.overworld.facilities.magic_guild import MagicGuild
            magic_guild = MagicGuild()
            magic_guild.enter(self.current_party)
        except Exception as e:
            logger.error(f"魔術師ギルドエラー: {e}")
            logger.info("魔術師ギルドの詳細機能を利用")
    
    # === 設定画面ハンドラー ===
    
    def _on_party_status(self):
        """パーティ状況表示"""
        logger.info("パーティ状況が選択されました")
        if self.current_party:
            # 詳細なパーティ情報表示
            info_text = f"パーティ: {self.current_party.name}\\n"
            info_text += f"メンバー数: {len(self.current_party.get_living_characters())}人\\n"
            info_text += f"ゴールド: {self.current_party.gold}G"
            
            for i, character in enumerate(self.current_party.get_living_characters()):
                info_text += f"\\n{i+1}. {character.name} Lv.{character.level}"
            
            logger.info(f"パーティ詳細: {info_text}")
    
    def _on_save_game(self):
        """ゲームを保存"""
        logger.info("ゲーム保存が選択されました")
        # セーブ処理の実装
        success = self.save_overworld_state("quicksave")
        if success:
            logger.info("ゲームを保存しました")
        else:
            logger.error("ゲーム保存に失敗しました")
    
    def _on_load_game(self):
        """ゲームをロード"""
        logger.info("ゲームロードが選択されました")
        # ロード処理の実装
        success = self.load_overworld_state("quicksave")
        if success:
            logger.info("ゲームをロードしました")
        else:
            logger.error("ゲームロードに失敗しました")
    
    def _on_config(self):
        """設定"""
        logger.info("設定が選択されました")
        # ゲーム設定画面の表示
        logger.info("設定画面を表示（未実装）")
    
    def _on_back_to_overworld(self):
        """地上部に戻る"""
        logger.info("地上部に戻ります")
        self._hide_settings_menu()
        self._show_main_menu()
    
    def _on_exit_game(self):
        """ゲーム終了"""
        logger.info("ゲーム終了が選択されました")
        if self.exit_game_callback:
            self.exit_game_callback()
    
    # === 画面遷移メソッド ===
    
    def _show_settings_menu(self):
        """設定画面を表示"""
        if self.main_menu:
            self.main_menu.hide()
        if self.settings_menu:
            self.settings_menu.show()
        self.settings_active = True
        logger.info("設定画面を表示しました")
    
    def _hide_settings_menu(self):
        """設定画面を非表示"""
        if self.settings_menu:
            self.settings_menu.hide()
        self.settings_active = False
        logger.info("設定画面を非表示にしました")
    
    def _show_main_menu(self):
        """メインメニューを表示"""
        if self.main_menu:
            self.main_menu.show()
        logger.info("メインメニューを表示しました")
    
    def enter_overworld(self, party: Party, from_dungeon: bool = False) -> bool:
        """地上部に入場"""
        try:
            self.current_party = party
            self.is_active = True
            
            # UIマネージャーが設定されていない場合は後で設定
            if self.ui_manager and not self.main_menu:
                self._create_main_menu()
            
            # メインメニューを表示
            if self.main_menu:
                self.main_menu.show()
            
            if from_dungeon:
                logger.info("ダンジョンから地上部に帰還しました")
            else:
                logger.info("地上部に入場しました")
            
            return True
            
        except Exception as e:
            logger.error(f"地上部入場エラー: {e}")
            return False
    
    def exit_overworld(self):
        """地上部を退場"""
        self.is_active = False
        
        # メインメニューを隠す
        if self.main_menu:
            self.main_menu.hide()
        
        logger.info("地上部を退場しました")
    
    def render(self, screen: pygame.Surface):
        """地上部の描画"""
        if not self.is_active:
            return
        
        # 背景色（画面によって色を変える）
        if self.settings_active:
            screen.fill((50, 50, 80))  # 設定画面：濃い青
        else:
            screen.fill((100, 150, 100))  # 地上部：緑
        
        # 背景テキスト表示（日本語フォント使用）
        try:
            from src.ui.font_manager_pygame import font_manager
            font = font_manager.get_japanese_font(24)
            if not font:
                font = font_manager.get_default_font()
        except Exception as e:
            logger.warning(f"フォントマネージャーの取得に失敗: {e}")
            try:
                # システムフォントで日本語フォントを試す
                font = pygame.font.SysFont('notosanscjk,noto,ipagothic,takao,hiragino,meiryo,msgothic', 24)
            except:
                font = pygame.font.Font(None, 24)
        
        if font:
            if self.settings_active:
                # 設定画面のタイトル
                try:
                    title_text = font.render("設定画面", True, (255, 255, 255))
                    title_rect = title_text.get_rect(center=(screen.get_width()//2, 80))
                    screen.blit(title_text, title_rect)
                except:
                    # 英語フォールバック
                    title_text = font.render("Settings Menu", True, (255, 255, 255))
                    title_rect = title_text.get_rect(center=(screen.get_width()//2, 80))
                    screen.blit(title_text, title_rect)
                
                # ESCキーの案内
                try:
                    help_text = font.render("[ESC] 地上部に戻る", True, (200, 200, 200))
                    help_rect = help_text.get_rect(center=(screen.get_width()//2, 120))
                    screen.blit(help_text, help_rect)
                except:
                    # 英語フォールバック
                    help_text = font.render("[ESC] Return to Overworld", True, (200, 200, 200))
                    help_rect = help_text.get_rect(center=(screen.get_width()//2, 120))
                    screen.blit(help_text, help_rect)
            else:
                # 地上部のタイトル
                try:
                    title_text = font.render("地上マップ", True, (255, 255, 255))
                    title_rect = title_text.get_rect(center=(screen.get_width()//2, 80))
                    screen.blit(title_text, title_rect)
                except:
                    # 英語フォールバック
                    title_text = font.render("Overworld Map", True, (255, 255, 255))
                    title_rect = title_text.get_rect(center=(screen.get_width()//2, 80))
                    screen.blit(title_text, title_rect)
                
                # パーティ情報
                if self.current_party:
                    try:
                        party_info = f"パーティ: {self.current_party.name} | ゴールド: {self.current_party.gold}G"
                        info_text = font.render(party_info, True, (200, 200, 200))
                        info_rect = info_text.get_rect(center=(screen.get_width()//2, 120))
                        screen.blit(info_text, info_rect)
                    except:
                        # 英語フォールバック
                        party_info = f"Party: {self.current_party.name} | Gold: {self.current_party.gold}G"
                        info_text = font.render(party_info, True, (200, 200, 200))
                        info_rect = info_text.get_rect(center=(screen.get_width()//2, 120))
                        screen.blit(info_text, info_rect)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベント処理"""
        if not self.is_active:
            return False
        
        # ESCキーで設定画面の表示・非表示を切り替え
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.settings_active:
                    # 設定画面が表示中の場合は地上部に戻る
                    self._hide_settings_menu()
                    self._show_main_menu()
                else:
                    # 地上部が表示中の場合は設定画面を表示
                    self._show_settings_menu()
                return True
        
        return False
    
    def save_overworld_state(self, slot_id: str) -> bool:
        """地上部状態を保存"""
        try:
            # 簡易実装（実際の保存処理は後で実装）
            logger.info(f"地上部状態を保存しました: スロット{slot_id}")
            return True
        except Exception as e:
            logger.error(f"地上部状態保存エラー: {e}")
            return False
    
    def load_overworld_state(self, slot_id: str) -> bool:
        """地上部状態を読み込み"""
        try:
            # 簡易実装（実際の読み込み処理は後で実装）
            logger.info(f"地上部状態を読み込みました: スロット{slot_id}")
            return True
        except Exception as e:
            logger.error(f"地上部状態読み込みエラー: {e}")
            return False