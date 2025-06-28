"""ヘルプ表示管理クラス

Fowler Extract Classパターンにより、HelpWindowからヘルプ表示に関する責任を抽出。
単一責任の原則に従い、ヘルプコンテンツの表示フォーマット・レイアウト・UI生成を専門的に扱う。
"""

from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import pygame

from src.ui.window_system.help_enums import HelpCategory, HelpContext
from src.utils.logger import logger


class DisplayFormat(Enum):
    """表示フォーマット"""
    SIMPLE = "simple"
    DETAILED = "detailed"
    COMPACT = "compact"
    FORMATTED = "formatted"


class HelpDisplayManager:
    """ヘルプ表示管理クラス
    
    ヘルプコンテンツの表示フォーマット・レイアウト・UI生成を担当。
    Extract Classパターンにより、HelpWindowから表示ロジックを分離。
    """
    
    def __init__(self):
        """ヘルプ表示マネージャー初期化"""
        # 表示設定
        self.default_font_size = 24
        self.title_font_size = 32
        self.section_font_size = 28
        self.max_line_width = 500
        self.line_spacing = 30
        
        # カラー設定
        self.colors = {
            'title': (255, 255, 255),
            'section': (200, 200, 255),
            'content': (180, 180, 180),
            'highlight': (255, 255, 100),
            'background': (50, 50, 50)
        }
        
        logger.debug("HelpDisplayManagerを初期化しました")
    
    def format_category_help(self, category_data: Dict[str, Any], 
                           format_type: DisplayFormat = DisplayFormat.DETAILED) -> Dict[str, Any]:
        """カテゴリヘルプの表示フォーマット
        
        Args:
            category_data: カテゴリデータ
            format_type: 表示フォーマット
            
        Returns:
            Dict: フォーマット済み表示データ
        """
        if not category_data:
            return {}
        
        formatted_data = {
            'title': category_data.get('title', ''),
            'sections': [],
            'format': format_type.value
        }
        
        sections = category_data.get('sections', [])
        for section in sections:
            formatted_section = self._format_section(section, format_type)
            formatted_data['sections'].append(formatted_section)
        
        return formatted_data
    
    def format_context_help(self, context_data: Dict[str, Any],
                          format_type: DisplayFormat = DisplayFormat.COMPACT) -> Dict[str, Any]:
        """コンテキストヘルプの表示フォーマット
        
        Args:
            context_data: コンテキストデータ
            format_type: 表示フォーマット
            
        Returns:
            Dict: フォーマット済み表示データ
        """
        if not context_data:
            return {}
        
        formatted_data = {
            'title': context_data.get('title', ''),
            'content': context_data.get('content', ''),
            'tips': context_data.get('tips', []),
            'format': format_type.value
        }
        
        if format_type == DisplayFormat.DETAILED:
            formatted_data['display_tips'] = self._format_tips_list(formatted_data['tips'])
        else:
            formatted_data['display_tips'] = []
        
        return formatted_data
    
    def format_quick_reference(self, reference_data: Dict[str, Any]) -> Dict[str, Any]:
        """クイックリファレンスの表示フォーマット
        
        Args:
            reference_data: リファレンスデータ
            
        Returns:
            Dict: フォーマット済み表示データ
        """
        if not reference_data:
            return {}
        
        formatted_data = {
            'title': reference_data.get('title', ''),
            'sections': [],
            'format': DisplayFormat.COMPACT.value
        }
        
        sections = reference_data.get('sections', {})
        for section_key, section_data in sections.items():
            formatted_section = {
                'key': section_key,
                'title': section_data.get('title', ''),
                'items': section_data.get('items', []),
                'display_items': self._format_reference_items(section_data.get('items', []))
            }
            formatted_data['sections'].append(formatted_section)
        
        return formatted_data
    
    def format_controls_guide(self, guide_data: Dict[str, Any]) -> Dict[str, Any]:
        """操作ガイドの表示フォーマット
        
        Args:
            guide_data: ガイドデータ
            
        Returns:
            Dict: フォーマット済み表示データ
        """
        if not guide_data:
            return {}
        
        formatted_data = {
            'title': guide_data.get('title', ''),
            'sections': [],
            'format': DisplayFormat.DETAILED.value
        }
        
        sections = guide_data.get('sections', {})
        for section_key, section_data in sections.items():
            formatted_section = {
                'key': section_key,
                'title': section_data.get('title', ''),
                'items': section_data.get('items', []),
                'display_items': self._format_guide_items(section_data.get('items', []))
            }
            formatted_data['sections'].append(formatted_section)
        
        return formatted_data
    
    def format_first_time_help(self, help_data: Dict[str, Any]) -> Dict[str, Any]:
        """初回起動時ヘルプの表示フォーマット
        
        Args:
            help_data: ヘルプデータ
            
        Returns:
            Dict: フォーマット済み表示データ
        """
        if not help_data:
            return {}
        
        formatted_data = {
            'title': help_data.get('title', ''),
            'intro': help_data.get('intro', ''),
            'basic_flow': self._format_basic_flow(help_data.get('basic_flow', {})),
            'controls': self._format_controls_section(help_data.get('controls', {})),
            'footer': help_data.get('footer', ''),
            'format': DisplayFormat.FORMATTED.value
        }
        
        return formatted_data
    
    def generate_menu_items(self, categories: List[HelpCategory]) -> List[Dict[str, Any]]:
        """メニューアイテムを生成
        
        Args:
            categories: ヘルプカテゴリリスト
            
        Returns:
            List[Dict]: メニューアイテムリスト
        """
        menu_items = []
        
        category_names = {
            HelpCategory.BASIC_CONTROLS: "基本操作",
            HelpCategory.DUNGEON_EXPLORATION: "ダンジョン探索", 
            HelpCategory.COMBAT_SYSTEM: "戦闘システム",
            HelpCategory.MAGIC_SYSTEM: "魔法システム",
            HelpCategory.EQUIPMENT_SYSTEM: "装備システム",
            HelpCategory.INVENTORY_MANAGEMENT: "インベントリ管理",
            HelpCategory.CHARACTER_DEVELOPMENT: "キャラクター育成",
            HelpCategory.OVERWORLD_NAVIGATION: "地上部ナビゲーション"
        }
        
        for category in categories:
            name = category_names.get(category, category.value)
            menu_items.append({
                'category': category,
                'name': name,
                'display_text': name,
                'description': f"{name}に関するヘルプを表示"
            })
        
        return menu_items
    
    def calculate_layout(self, content: Dict[str, Any], 
                        container_rect: pygame.Rect) -> Dict[str, Any]:
        """レイアウトを計算
        
        Args:
            content: 表示コンテンツ
            container_rect: コンテナ矩形
            
        Returns:
            Dict: レイアウト情報
        """
        layout = {
            'container': container_rect,
            'title_rect': None,
            'content_rects': [],
            'scroll_info': {
                'total_height': 0,
                'visible_height': container_rect.height,
                'scroll_position': 0,
                'can_scroll': False
            }
        }
        
        current_y = container_rect.y + 20
        margin_x = 20
        content_width = container_rect.width - (margin_x * 2)
        
        # タイトルレイアウト
        if content.get('title'):
            title_height = self.title_font_size + 10
            layout['title_rect'] = pygame.Rect(
                container_rect.x + margin_x,
                current_y,
                content_width,
                title_height
            )
            current_y += title_height + 20
        
        # コンテンツレイアウト
        sections = content.get('sections', [])
        for section in sections:
            section_height = self._calculate_section_height(section)
            section_rect = pygame.Rect(
                container_rect.x + margin_x,
                current_y,
                content_width,
                section_height
            )
            layout['content_rects'].append(section_rect)
            current_y += section_height + 15
        
        # スクロール情報
        layout['scroll_info']['total_height'] = current_y - container_rect.y
        layout['scroll_info']['can_scroll'] = (
            layout['scroll_info']['total_height'] > layout['scroll_info']['visible_height']
        )
        
        return layout
    
    def _format_section(self, section: Dict[str, Any], 
                       format_type: DisplayFormat) -> Dict[str, Any]:
        """セクションをフォーマット"""
        formatted = {
            'title': section.get('title', ''),
            'content': [],
            'keyboard_controls': [],
            'gamepad_controls': []
        }
        
        # コンテンツ
        if 'content' in section:
            formatted['content'] = section['content']
        
        # キーボード操作
        if 'keyboard' in section:
            formatted['keyboard_controls'] = section['keyboard']
        
        # ゲームパッド操作
        if 'gamepad' in section:
            formatted['gamepad_controls'] = section['gamepad']
        
        return formatted
    
    def _format_tips_list(self, tips: List[str]) -> List[Dict[str, Any]]:
        """ヒントリストをフォーマット"""
        formatted_tips = []
        for tip in tips:
            formatted_tips.append({
                'text': tip,
                'icon': '💡',
                'display_text': f"💡 {tip}"
            })
        return formatted_tips
    
    def _format_reference_items(self, items: List[str]) -> List[Dict[str, Any]]:
        """リファレンスアイテムをフォーマット"""
        formatted_items = []
        for item in items:
            # "キー : 説明" 形式を分析
            if ' : ' in item:
                key, description = item.split(' : ', 1)
                formatted_items.append({
                    'key': key.strip(),
                    'description': description.strip(),
                    'display_text': item
                })
            else:
                formatted_items.append({
                    'key': '',
                    'description': item,
                    'display_text': item
                })
        return formatted_items
    
    def _format_guide_items(self, items: List[str]) -> List[Dict[str, Any]]:
        """ガイドアイテムをフォーマット"""
        formatted_items = []
        for item in items:
            formatted_items.append({
                'text': item,
                'bullet': '•' if item.startswith('•') else '',
                'display_text': item
            })
        return formatted_items
    
    def _format_basic_flow(self, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """基本フローをフォーマット"""
        return {
            'title': flow_data.get('title', ''),
            'steps': flow_data.get('steps', []),
            'display_steps': [
                {'number': i+1, 'text': step, 'display_text': step}
                for i, step in enumerate(flow_data.get('steps', []))
            ]
        }
    
    def _format_controls_section(self, controls_data: Dict[str, Any]) -> Dict[str, Any]:
        """操作セクションをフォーマット"""
        return {
            'title': controls_data.get('title', ''),
            'items': controls_data.get('items', []),
            'display_items': [
                {'text': item, 'display_text': item}
                for item in controls_data.get('items', [])
            ]
        }
    
    def _calculate_section_height(self, section: Dict[str, Any]) -> int:
        """セクションの高さを計算"""
        height = 0
        
        # タイトル
        if section.get('title'):
            height += self.section_font_size + 10
        
        # コンテンツ
        content_items = (
            section.get('content', []) + 
            section.get('keyboard_controls', []) + 
            section.get('gamepad_controls', []) +
            section.get('items', [])
        )
        
        height += len(content_items) * self.line_spacing
        
        return max(height, 50)  # 最小高さ
    
    def get_color(self, color_type: str) -> Tuple[int, int, int]:
        """カラーを取得
        
        Args:
            color_type: カラータイプ
            
        Returns:
            Tuple: RGB値
        """
        return self.colors.get(color_type, (255, 255, 255))