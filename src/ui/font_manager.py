"""フォント管理システム"""

import os
from typing import Optional, Dict, Any
from panda3d.core import TextNode

from src.utils.logger import logger

class FontManager:
    """フォント管理クラス"""
    
    def __init__(self):
        self.fonts: Dict[str, Any] = {}
        self.default_font = None
        self._initialize_fonts()
    
    def _initialize_fonts(self):
        """フォントの初期化"""
        try:
            from panda3d.core import DynamicTextFont
            
            # 日本語フォントのパスを探す
            font_paths = [
                # Noto Sans CJK (推奨)
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
                # IPA Font
                "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
                "/usr/share/fonts/opentype/ipafont-mincho/ipam.ttf",
                # Takao Font
                "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
                "/usr/share/fonts/truetype/fonts-japanese-mincho.ttf",
            ]
            
            # 利用可能なフォントを探す
            japanese_font_path = None
            for path in font_paths:
                if os.path.exists(path):
                    japanese_font_path = path
                    logger.info(f"日本語フォントを発見: {path}")
                    break
            
            if japanese_font_path:
                # 日本語フォントをロード
                try:
                    font = base.loader.loadFont(japanese_font_path)
                    if font:
                        self.fonts['japanese'] = font
                        self.default_font = font
                        logger.info(f"日本語フォントをロードしました: {japanese_font_path}")
                        
                        # フォントの設定
                        font.setPixelsPerUnit(60)
                        try:
                            from panda3d.core import Texture
                            font.setMinfilter(Texture.FTNearest)
                            font.setMagfilter(Texture.FTNearest)
                        except:
                            pass  # フィルター設定はオプション
                    else:
                        logger.warning(f"フォントのロードに失敗: {japanese_font_path}")
                except Exception as e:
                    logger.error(f"フォントロードエラー: {e}")
            else:
                logger.warning("日本語フォントが見つかりませんでした")
                
        except Exception as e:
            logger.error(f"フォント初期化エラー: {e}")
    
    def get_font(self, font_name: str = 'japanese') -> Optional[Any]:
        """フォントを取得"""
        return self.fonts.get(font_name, self.default_font)
    
    def get_default_font(self) -> Optional[Any]:
        """デフォルトフォントを取得"""
        return self.default_font
    
    def apply_font_to_text_node(self, text_node: TextNode, font_name: str = 'japanese'):
        """TextNodeにフォントを適用"""
        font = self.get_font(font_name)
        if font:
            text_node.setFont(font)
            logger.debug(f"フォントを適用: {font_name}")
        else:
            logger.warning(f"フォントが見つかりません: {font_name}")

# グローバルインスタンス
font_manager = FontManager()