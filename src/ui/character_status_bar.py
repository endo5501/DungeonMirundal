"""キャラクターステータスバーUI"""

import pygame
from typing import Optional, List
from enum import Enum

from src.ui.base_ui_pygame import UIElement, UIState
from src.character.party import Party
from src.character.character import Character, CharacterStatus
from src.utils.logger import logger


class CharacterSlot:
    """キャラクタースロット（1つのキャラクターの表示領域）"""
    
    def __init__(self, x: int, y: int, width: int, height: int, slot_index: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.slot_index = slot_index
        self.character: Optional[Character] = None
        
        # レイアウト設定
        self.image_width = 48
        self.image_height = 48
        self.image_x = x + 10
        self.image_y = y + 10
        
        self.name_x = x + self.image_width + 20
        self.name_y = y + 10
        
        self.hp_x = x + self.image_width + 20
        self.hp_y = y + 35
        
        # 色設定
        self.bg_color = (40, 40, 40)  # 背景色（ダークグレー）
        self.border_color = (100, 100, 100)  # 枠線色
        self.text_color = (255, 255, 255)  # テキスト色
        self.hp_bar_bg_color = (60, 60, 60)  # HPバー背景色
        self.hp_bar_color = (0, 255, 0)  # HPバー色（緑）
        self.hp_bar_low_color = (255, 100, 0)  # HP低下色（オレンジ）
        self.hp_bar_critical_color = (255, 0, 0)  # HP危険色（赤）
        
    def set_character(self, character: Optional[Character]):
        """キャラクターを設定"""
        self.character = character
    
    def render(self, screen: pygame.Surface, font: pygame.font.Font):
        """スロットを描画"""
        # 背景と枠線
        bg_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(screen, self.bg_color, bg_rect)
        pygame.draw.rect(screen, self.border_color, bg_rect, 2)
        
        if not self.character:
            # 空スロットの場合（フォント安全チェック付き）
            try:
                if font:
                    empty_text = font.render("Empty", True, (128, 128, 128))
                    text_rect = empty_text.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))
                    screen.blit(empty_text, text_rect)
            except pygame.error:
                # フォントエラーの場合は何も表示しない（スロット枠のみ表示）
                pass
            return
        
        # キャラクター画像プレースホルダー
        image_rect = pygame.Rect(self.image_x, self.image_y, self.image_width, self.image_height)
        
        # キャラクターの状態に応じて画像枠の色を変更
        if self.character.status == CharacterStatus.DEAD:
            placeholder_color = (60, 60, 60)  # 死亡：暗いグレー
        elif self.character.status == CharacterStatus.UNCONSCIOUS:
            placeholder_color = (120, 60, 60)  # 意識不明：暗い赤
        elif self.character.status == CharacterStatus.INJURED:
            placeholder_color = (120, 120, 60)  # 負傷：黄色がかったグレー
        else:
            placeholder_color = (80, 80, 120)  # 良好：青がかったグレー
        
        pygame.draw.rect(screen, placeholder_color, image_rect)
        pygame.draw.rect(screen, self.border_color, image_rect, 1)
        
        # プレースホルダーテキスト（フォント安全チェック付き）
        try:
            if font:
                placeholder_text = font.render("IMG", True, self.text_color)
                placeholder_rect = placeholder_text.get_rect(center=image_rect.center)
                screen.blit(placeholder_text, placeholder_rect)
        except pygame.error:
            # フォントエラーの場合はプレースホルダーテキストを表示しない
            pass
        
        # キャラクター名（フォント安全チェック付き）
        try:
            if font:
                name_surface = font.render(self.character.name, True, self.text_color)
                screen.blit(name_surface, (self.name_x, self.name_y))
        except pygame.error:
            # フォントエラーの場合は名前を表示しない
            pass
        except Exception as e:
            logger.warning(f"キャラクター名表示エラー: {e}")
            try:
                if font:
                    name_surface = font.render("???", True, self.text_color)
                    screen.blit(name_surface, (self.name_x, self.name_y))
            except pygame.error:
                # フォントエラーの場合は何も表示しない
                pass
        
        # HP表示
        self._render_hp_bar(screen, font)
    
    def _render_hp_bar(self, screen: pygame.Surface, font: pygame.font.Font):
        """HPバーを描画"""
        if not self.character:
            return
        
        current_hp = self.character.derived_stats.current_hp
        max_hp = self.character.derived_stats.max_hp
        
        # HPテキスト - スラッシュ文字の問題を回避するため、個別にレンダリング（フォント安全チェック付き）
        try:
            if font:
                # 現在HPをレンダリング
                current_hp_text = str(current_hp)
                current_hp_surface = font.render(current_hp_text, True, self.text_color)
                screen.blit(current_hp_surface, (self.hp_x, self.hp_y))
                
                # スラッシュをレンダリング
                slash_x = self.hp_x + current_hp_surface.get_width()
                slash_surface = font.render("/", True, self.text_color)
                screen.blit(slash_surface, (slash_x, self.hp_y))
                
                # 最大HPをレンダリング
                max_hp_text = str(max_hp)
                max_hp_x = slash_x + slash_surface.get_width()
                max_hp_surface = font.render(max_hp_text, True, self.text_color)
                screen.blit(max_hp_surface, (max_hp_x, self.hp_y))
                
                # HPバーの位置計算用に全体の幅を保持
                total_width = current_hp_surface.get_width() + slash_surface.get_width() + max_hp_surface.get_width()
            else:
                total_width = 50  # フォントがない場合のフォールバック
            
        except Exception as e:
            logger.warning(f"HP表示エラー: {e}")
            # フォールバック：シンプルな表示（フォント安全チェック付き）
            try:
                if font:
                    fallback_text = f"{current_hp}-{max_hp}"
                    fallback_surface = font.render(fallback_text, True, self.text_color)
                    screen.blit(fallback_surface, (self.hp_x, self.hp_y))
                    total_width = fallback_surface.get_width()
                else:
                    total_width = 50
            except pygame.error:
                # フォントエラーの場合はテキストを表示しない
                total_width = 50
            except:
                # 最終フォールバック
                total_width = 50
        
        # HPバー
        bar_width = 80
        bar_height = 8
        bar_x = self.hp_x + total_width + 10
        bar_y = self.hp_y + 5
        
        # 背景バー
        bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(screen, self.hp_bar_bg_color, bg_rect)
        
        # HPバー（現在のHP比率）
        if max_hp > 0:
            hp_ratio = current_hp / max_hp
            filled_width = int(bar_width * hp_ratio)
            
            # HP比率に応じて色を変更
            if hp_ratio <= 0.2:
                bar_color = self.hp_bar_critical_color
            elif hp_ratio <= 0.5:
                bar_color = self.hp_bar_low_color
            else:
                bar_color = self.hp_bar_color
            
            if filled_width > 0:
                filled_rect = pygame.Rect(bar_x, bar_y, filled_width, bar_height)
                pygame.draw.rect(screen, bar_color, filled_rect)
        
        # バー枠線
        pygame.draw.rect(screen, self.border_color, bg_rect, 1)


class CharacterStatusBar(UIElement):
    """キャラクターステータスバーUI（画面下部）"""
    
    def __init__(self, x: int = 0, y: int = 668, width: int = 1024, height: int = 100):
        super().__init__("character_status_bar", x, y, width, height)
        
        self.party: Optional[Party] = None
        self.slots: List[CharacterSlot] = []
        
        # 6つのキャラクタースロットを作成
        slot_width = width // 6
        for i in range(6):
            slot_x = x + (i * slot_width)
            slot = CharacterSlot(slot_x, y, slot_width, height, i)
            self.slots.append(slot)
        
        # フォント
        self.font = None
        self._initialize_font()
        
        # 自動的に表示状態にする
        self.show()
        
        logger.info("CharacterStatusBarを初期化しました")
    
    def _initialize_font(self):
        """フォントを初期化"""
        try:
            # Pygameフォントモジュールが初期化されているか確認
            if not pygame.font.get_init():
                pygame.font.init()
            
            # まず日本語フォントマネージャーから取得を試行
            from src.ui.font_manager_pygame import font_manager
            self.font = font_manager.get_japanese_font(16)
            if self.font:
                # フォントをキャッシュして再初期化を防ぐ
                self._cached_font = self.font
                return
        except Exception as e:
            logger.warning(f"フォントマネージャーの取得に失敗: {e}")
        
        try:
            # Pygameフォントモジュールが初期化されているか再確認
            if not pygame.font.get_init():
                pygame.font.init()
                
            # フォールバック：デフォルトフォント（安定性優先）
            self.font = pygame.font.Font(None, 16)
            self._cached_font = self.font
        except Exception as e:
            logger.error(f"デフォルトフォントの取得に失敗: {e}")
            self.font = None
            self._cached_font = None
    
    def set_party(self, party: Optional[Party]):
        """パーティを設定してキャラクター情報を更新"""
        self.party = party
        self.update_character_display()
    
    def update_character_display(self):
        """キャラクター表示を更新"""
        # 全スロットをクリア
        for slot in self.slots:
            slot.set_character(None)
        
        if not self.party:
            return
        
        # パーティのキャラクターをスロットに配置
        characters = list(self.party.characters.values())
        for i, character in enumerate(characters):
            if i < len(self.slots):
                self.slots[i].set_character(character)
    
    def render(self, screen: pygame.Surface, font: Optional[pygame.font.Font] = None):
        """ステータスバーを描画"""
        if self.state != UIState.VISIBLE:
            return
        
        # フォントを決定（安定性のためキャッシュを優先）
        if hasattr(self, '_cached_font') and self._cached_font:
            use_font = self._cached_font
        else:
            use_font = font if font else self.font
            
        if not use_font:
            # フォントがない場合は再初期化を試みる
            self._initialize_font()
            use_font = self.font
            if not use_font:
                return
        
        # フォントが有効かチェック（pygame.font.quit()対策）
        try:
            # テストレンダリングでフォントの有効性を確認
            test_surface = use_font.render("", True, (255, 255, 255))
        except pygame.error:
            # フォントが無効の場合、再初期化を試行
            logger.warning("フォントが無効になっているため再初期化します")
            self._initialize_font()
            use_font = self.font
            if not use_font:
                return
        
        # 各スロットを描画
        for slot in self.slots:
            slot.render(screen, use_font)
    
    def update(self):
        """ステータスバーを更新（HP変化等を反映）"""
        # パーティが設定されている場合、キャラクター表示を更新
        if self.party:
            self.update_character_display()


def create_character_status_bar(screen_width: int = 1024, screen_height: int = 768) -> CharacterStatusBar:
    """キャラクターステータスバーを作成"""
    # 画面下部に配置
    y_position = screen_height - 100
    return CharacterStatusBar(x=0, y=y_position, width=screen_width, height=100)