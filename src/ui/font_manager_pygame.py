"""フォント管理システム（Pygame版）"""

import os
import sys
from typing import Optional, Dict
import pygame

from src.utils.logger import logger
from src.core.config_manager import config_manager

class FontManager:
    """フォント管理クラス（Pygame版）"""
    
    def __init__(self):
        self.fonts: Dict[str, pygame.font.Font] = {}
        self.default_font = None
        self._cross_platform_font_path = None
        self._initialize_fonts()
    
    def _initialize_fonts(self):
        """フォントの初期化"""
        try:
            # OSごとの日本語フォントパスを設定
            if sys.platform == 'darwin':  # macOS
                font_paths = [
                    # macOS用TTF/OTFフォント（TTCより互換性が高い）
                    "/System/Library/Fonts/Supplemental/NotoSansGothic-Regular.ttf",
                    "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
                    # フォールバック用TTCフォント
                    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
                    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
                    "/System/Library/Fonts/AquaKana.ttc",
                    # 追加フォント（存在する場合）
                    "/Library/Fonts/ヒラギノ角ゴ Pro W3.otf",
                    "/Library/Fonts/YuGothic-Medium.otf",
                    # ユーザーフォント
                    os.path.expanduser("~/Library/Fonts/NotoSansCJK-Regular.ttc"),
                    os.path.expanduser("~/Library/Fonts/NotoSansJP-Regular.otf"),
                ]
            elif sys.platform == 'win32':  # Windows
                font_paths = [
                    # Windows標準日本語フォント
                    "C:/Windows/Fonts/msgothic.ttc",
                    "C:/Windows/Fonts/YuGothM.ttc",
                    "C:/Windows/Fonts/YuGothR.ttc",
                    "C:/Windows/Fonts/YuGothB.ttc",
                    "C:/Windows/Fonts/meiryo.ttc",
                    "C:/Windows/Fonts/meiryob.ttc",
                    # 追加フォント
                    "C:/Windows/Fonts/NotoSansCJK-Regular.ttc",
                    "C:/Windows/Fonts/NotoSansJP-Regular.otf",
                ]
            else:  # Linux/Unix
                font_paths = [
                    # Noto Sans CJK (推奨)
                    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
                    # IPA Font
                    "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
                    "/usr/share/fonts/opentype/ipafont-mincho/ipam.ttf",
                    # Takao Font
                    "/usr/share/fonts/truetype/takao-gothic/TakaoGothic.ttf",
                    "/usr/share/fonts/truetype/takao-mincho/TakaoMincho.ttf",
                    # DejaVu (ラテン文字用フォールバック)
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                ]
            
            # 利用可能な日本語フォントを探す
            japanese_font_path = None
            for path in font_paths:
                if os.path.exists(path):
                    japanese_font_path = path
                    logger.info(config_manager.get_text("font_manager.font_found").format(path=path))
                    break
            
            if japanese_font_path:
                try:
                    # 複数サイズのフォントをロード
                    sizes = [16, 18, 20, 24, 28, 32, 36, 48]
                    for size in sizes:
                        font_key = f"japanese_{size}"
                        font = pygame.font.Font(japanese_font_path, size)
                        self.fonts[font_key] = font
                        
                        # デフォルトフォント設定（24px）
                        if size == 24:
                            self.default_font = font
                            self.fonts['default'] = font
                    
                    logger.info(config_manager.get_text("font_manager.japanese_font_loaded").format(path=japanese_font_path))
                    
                except Exception as e:
                    logger.warning(config_manager.get_text("font_manager.japanese_font_load_failed").format(error=e))
                    self._load_fallback_fonts()
            else:
                logger.warning(config_manager.get_text("font_manager.japanese_font_not_found"))
                self._load_fallback_fonts()
                
            # システムフォントも追加
            self._load_system_fonts()
            
        except Exception as e:
            logger.error(config_manager.get_text("font_manager.font_init_error").format(error=e))
            self._load_fallback_fonts()
    
    def _load_fallback_fonts(self):
        """フォールバックフォントのロード"""
        try:
            # Pygameのデフォルトフォントを使用
            sizes = [16, 18, 20, 24, 28, 32, 36, 48]
            for size in sizes:
                font_key = f"default_{size}"
                font = pygame.font.Font(None, size)
                self.fonts[font_key] = font
                
                if size == 24:
                    self.default_font = font
                    self.fonts['default'] = font
            
            logger.info(config_manager.get_text("font_manager.fallback_font_loaded"))
            
        except Exception as e:
            logger.error(f"フォールバックフォントのロードに失敗: {e}")
    
    def _load_system_fonts(self):
        """システムフォントのロード"""
        try:
            # 利用可能なシステムフォントを取得
            system_fonts = pygame.font.get_fonts()
            
            # よく使われるフォントをロード
            preferred_fonts = [
                'arial', 'helvetica', 'times', 'courier',
                'verdana', 'tahoma', 'calibri', 'segoeui'
            ]
            
            for font_name in preferred_fonts:
                if font_name in system_fonts:
                    try:
                        font = pygame.font.SysFont(font_name, 24)
                        self.fonts[f'system_{font_name}'] = font
                        logger.debug(f"システムフォントをロード: {font_name}")
                    except:
                        continue
                        
        except Exception as e:
            logger.warning(f"システムフォントのロードに失敗: {e}")
    
    def get_font(self, font_name: str = 'default', size: int = 24) -> Optional[pygame.font.Font]:
        """フォントを取得"""
        # サイズ指定のフォント
        font_key = f"{font_name}_{size}"
        if font_key in self.fonts:
            return self.fonts[font_key]
        
        # 基本フォント名
        if font_name in self.fonts:
            return self.fonts[font_name]
        
        # デフォルトフォント
        if self.default_font:
            return self.default_font
        
        # 最後の手段：Pygameデフォルト
        try:
            return pygame.font.Font(None, size)
        except:
            return None
    
    def get_default_font(self) -> Optional[pygame.font.Font]:
        """デフォルトフォントを取得"""
        return self.default_font
    
    def get_japanese_font(self, size: int = 24) -> Optional[pygame.font.Font]:
        """日本語フォントを取得"""
        return self.get_font('japanese', size)
    
    def render_text(self, text: str, font_name: str = 'default', size: int = 24, 
                   color: tuple = (255, 255, 255), antialias: bool = True) -> Optional[pygame.Surface]:
        """テキストをレンダリング"""
        font = self.get_font(font_name, size)
        if font:
            try:
                return font.render(text, antialias, color)
            except Exception as e:
                logger.warning(f"テキストレンダリングエラー: {e}")
        return None
    
    def get_text_size(self, text: str, font_name: str = 'default', size: int = 24) -> tuple:
        """テキストのサイズを取得"""
        font = self.get_font(font_name, size)
        if font:
            try:
                return font.size(text)
            except:
                pass
        return (0, 0)
    
    def get_available_fonts(self) -> list:
        """利用可能なフォントリストを取得"""
        return list(self.fonts.keys())
    
    def get_cross_platform_font_path(self) -> Optional[str]:
        """クロスプラットフォーム対応日本語フォントパスを取得"""
        if self._cross_platform_font_path:
            return self._cross_platform_font_path
        
        # まず同梱フォントを優先
        local_fonts = [
            "assets/fonts/NotoSansCJKJP-Regular.otf",
            "assets/fonts/NotoSansJP-Regular.otf", 
            "assets/fonts/ipag.ttf"
        ]
        for f in local_fonts:
            if os.path.exists(f):
                self._cross_platform_font_path = os.path.abspath(f)
                logger.debug(f"FontManager: 同梱フォントを発見: {self._cross_platform_font_path}")
                return self._cross_platform_font_path

        # 次にシステムフォント候補
        system_font_candidates = [
            "Hiragino Sans", "YuGothic", "Apple SD Gothic Neo",  # macOS
            "Yu Gothic UI", "Meiryo UI", "MS Gothic",  # Windows
            "Noto Sans CJK JP", "IPAGothic", "Takao Gothic"  # Linux
        ]
        
        for name in system_font_candidates:
            path = pygame.font.match_font(name)
            if path:
                self._cross_platform_font_path = path
                logger.debug(f"FontManager: システムフォントを発見: {name} -> {path}")
                return self._cross_platform_font_path

        logger.warning("FontManager: 日本語対応フォントが見つかりませんでした")
        return None
    
    def initialize_pygame_gui_fonts(self, ui_manager):
        """pygame_guiに日本語フォントを統合（WindowManagerの処理を統合）"""
        try:
            font_path = self.get_cross_platform_font_path()
            if not font_path:
                logger.warning("FontManager: pygame_gui統合用フォントが見つかりません")
                return False
            
            # エイリアス "jp_font" として登録
            ui_manager.add_font_paths("jp_font", font_path)
            logger.debug(f"FontManager: pygame_guiフォント登録成功: jp_font -> {font_path}")
            
            # システムフォント（fira_code）も登録してdefaultの代替とする
            try:
                # pygameのデフォルトフォントパスを確認
                import pygame
                default_font_path = pygame.font.get_default_font()
                
                # デフォルトフォントが存在しない場合は日本語フォントを代替使用
                if not os.path.exists(default_font_path):
                    logger.debug(f"FontManager: デフォルトフォント見つからず: {default_font_path}, 日本語フォントで代替")
                    default_font_path = font_path  # 日本語フォントを使用
                    logger.debug(f"FontManager: fira_code代替パス: {default_font_path}")
                
                ui_manager.add_font_paths("fira_code", default_font_path)
                logger.debug(f"FontManager: システムフォント登録成功: fira_code -> {default_font_path}")
                
                # 登録が成功した場合、プリロードも実行
                ui_manager.preload_fonts([
                    {"name": "fira_code", "style": "regular", "point_size": 14},
                    {"name": "fira_code", "style": "regular", "point_size": 16},
                    {"name": "fira_code", "style": "regular", "point_size": 18},
                ])
                logger.debug("FontManager: fira_codeプリロード成功")
                
            except Exception as e:
                logger.debug(f"FontManager: システムフォント登録失敗: {e}")
                # 最終フォールバック：日本語フォントをfira_codeとしても登録
                try:
                    ui_manager.add_font_paths("fira_code", font_path)
                    logger.debug(f"FontManager: 最終フォールバック成功: fira_code -> {font_path}")
                    # プリロードも実行
                    ui_manager.preload_fonts([
                        {"name": "fira_code", "style": "regular", "point_size": 14},
                        {"name": "fira_code", "style": "regular", "point_size": 16},
                        {"name": "fira_code", "style": "regular", "point_size": 18},
                    ])
                    logger.debug("FontManager: 最終フォールバックプリロード成功")
                except Exception as fallback_e:
                    logger.debug(f"FontManager: 最終フォールバック失敗: {fallback_e}")
            
            # 必要なサイズでプリロード（日本語フォント）
            ui_manager.preload_fonts([
                {"name": "jp_font", "style": "regular", "point_size": 14},
                {"name": "jp_font", "style": "regular", "point_size": 16},
                {"name": "jp_font", "style": "regular", "point_size": 18},
                {"name": "jp_font", "style": "regular", "point_size": 20},
                {"name": "jp_font", "style": "regular", "point_size": 24}
            ])
            
            logger.debug("FontManager: pygame_guiフォントプリロード完了")
            
            # テーマ設定で階層を考慮した設定
            theme_data = {
                "defaults": {
                    "font": {"name": "jp_font", "size": "16", "style": "regular"}
                },
                "button": {
                    "font": {"name": "jp_font", "size": "16", "style": "regular"}
                },
                "label": {
                    "font": {"name": "jp_font", "size": "16", "style": "regular"}
                }
            }
            
            ui_manager.get_theme().load_theme(theme_data)
            logger.debug("FontManager: pygame_gui動的テーマ読み込み成功（日本語フォント対応）")
            return True
            
        except Exception as e:
            logger.error(f"FontManager: pygame_gui統合処理でエラー: {e}")
            return False
    
    def get_font_for_ui_component(self, component_type: str = "default", size: int = 16) -> Optional[pygame.font.Font]:
        """UIコンポーネント用フォントを取得（統一API）"""
        try:
            # Pygameフォントモジュールが初期化されているか確認
            if not pygame.font.get_init():
                pygame.font.init()
            
            # クロスプラットフォーム対応フォントを優先使用
            font_path = self.get_cross_platform_font_path()
            if font_path:
                font = pygame.font.Font(font_path, size)
                logger.debug(f"FontManager: UIコンポーネント用フォント作成 - {component_type}({size}px): {font_path}")
                return font
            
            # フォールバック：既存のfont_managerから取得
            return self.get_japanese_font(size)
            
        except Exception as e:
            logger.warning(f"FontManager: UIコンポーネント用フォント取得エラー: {e}")
            return self.get_font('default', size)
    
    def create_multiline_text(self, text: str, font_name: str = 'default', size: int = 24, 
                             color: tuple = (255, 255, 255), max_width: int = 400) -> list:
        """複数行テキストの作成"""
        font = self.get_font(font_name, size)
        if not font:
            return []
        
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            text_width, _ = font.size(test_line)
            
            if text_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # 単語が長すぎる場合は強制的に分割
                    lines.append(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Surface のリストを返す
        surfaces = []
        for line in lines:
            surface = font.render(line, True, color)
            surfaces.append(surface)
        
        return surfaces


# グローバルインスタンス
font_manager = FontManager()

def get_font_manager() -> FontManager:
    """フォントマネージャーのインスタンスを取得"""
    return font_manager