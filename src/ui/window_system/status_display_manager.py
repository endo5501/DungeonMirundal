"""ステータス効果表示管理クラス

Fowler Extract Classパターンにより、StatusEffectsWindowからステータス効果表示に関する責任を抽出。
単一責任の原則に従い、効果の表示フォーマット・レイアウト・UI生成を専門的に扱う。
"""

from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import pygame

from src.ui.window_system.status_effect_manager import EffectType, EffectCategory
from src.utils.logger import logger


class DisplayMode(Enum):
    """表示モード"""
    LIST = "list"
    GRID = "grid"
    DETAILED = "detailed"
    COMPACT = "compact"


class SortOrder(Enum):
    """ソート順"""
    NAME = "name"
    TYPE = "type"
    PRIORITY = "priority"
    REMAINING_TURNS = "remaining_turns"
    DURATION = "duration"


class StatusDisplayManager:
    """ステータス効果表示管理クラス
    
    ステータス効果の表示フォーマット・レイアウト・UI生成を担当。
    Extract Classパターンにより、StatusEffectsWindowから表示ロジックを分離。
    """
    
    def __init__(self):
        """ステータス効果表示マネージャー初期化"""
        # 表示設定
        self.default_font_size = 20
        self.title_font_size = 28
        self.header_font_size = 24
        self.max_line_width = 400
        self.line_spacing = 25
        self.item_spacing = 15
        
        # カラー設定
        self.colors = {
            'title': (255, 255, 255),
            'header': (200, 200, 255),
            'buff': (100, 255, 100),
            'debuff': (255, 100, 100),
            'neutral': (200, 200, 200),
            'removable': (255, 255, 100),
            'permanent': (150, 150, 150),
            'background': (40, 40, 40),
            'border': (100, 100, 100)
        }
        
        # アイコン設定
        self.effect_icons = {
            'poison': '☠',
            'paralysis': '⚡',
            'sleep': '💤',
            'confusion': '❓',
            'fear': '😨',
            'blindness': '👁',
            'silence': '🔇',
            'slow': '🐌',
            'regeneration': '💚',
            'haste': '⚡',
            'strength': '💪',
            'defense': '🛡',
            'blessing': '✨',
            'protection': '🛡️'
        }
        
        logger.debug("StatusDisplayManagerを初期化しました")
    
    def format_effect_list(self, effects: List[Dict[str, Any]], 
                          mode: DisplayMode = DisplayMode.LIST) -> List[Dict[str, Any]]:
        """効果リストをフォーマット
        
        Args:
            effects: 効果リスト
            mode: 表示モード
            
        Returns:
            List: フォーマット済み効果リスト
        """
        formatted_effects = []
        
        for effect in effects:
            if not isinstance(effect, dict):
                continue
            
            formatted_effect = self._format_single_effect(effect, mode)
            formatted_effects.append(formatted_effect)
        
        return formatted_effects
    
    def format_party_overview(self, party_summary: Dict[str, Any]) -> Dict[str, Any]:
        """パーティ概要をフォーマット
        
        Args:
            party_summary: パーティサマリー
            
        Returns:
            Dict: フォーマット済み概要
        """
        overview = {
            'title': 'パーティステータス効果',
            'total_effects': party_summary.get('total_effects', 0),
            'character_summaries': [],
            'type_distribution': self._format_type_distribution(party_summary.get('by_type', {})),
            'category_breakdown': self._format_category_breakdown(party_summary.get('by_category', {}))
        }
        
        # キャラクター別サマリー
        by_character = party_summary.get('by_character', {})
        for char_name, char_data in by_character.items():
            char_summary = {
                'name': char_name,
                'total': char_data.get('total', 0),
                'buffs': char_data.get('buffs', 0),
                'debuffs': char_data.get('debuffs', 0),
                'status_text': self._generate_character_status_text(char_data),
                'icon_summary': self._generate_character_icon_summary(char_data.get('effects', []))
            }
            overview['character_summaries'].append(char_summary)
        
        return overview
    
    def format_effect_details(self, effect: Dict[str, Any]) -> Dict[str, Any]:
        """効果詳細をフォーマット
        
        Args:
            effect: 効果データ
            
        Returns:
            Dict: フォーマット済み詳細
        """
        effect_name = effect.get('name', 'Unknown')
        
        details = {
            'name': effect_name,
            'display_name': effect.get('display_name', effect_name.title()),
            'icon': self.effect_icons.get(effect_name, '?'),
            'description': effect.get('description', ''),
            'type': effect.get('type', 'neutral'),
            'category': effect.get('category', 'condition'),
            'removable': effect.get('removable', False),
            'duration_info': self._format_duration_info(effect),
            'intensity_info': self._format_intensity_info(effect),
            'source_info': self._format_source_info(effect),
            'color': self._get_effect_color(effect)
        }
        
        return details
    
    def get_effect_menu_items(self, party) -> List[Dict[str, Any]]:
        """効果メニューアイテムを生成
        
        Args:
            party: パーティオブジェクト
            
        Returns:
            List: メニューアイテムリスト
        """
        menu_items = []
        
        if not party:
            return menu_items
        
        characters = getattr(party, 'characters', [])
        for character in characters:
            char_name = getattr(character, 'name', 'Unknown')
            char_effects = getattr(character, 'status_effects', [])
            
            # キャラクター全体のアイテム
            char_item = {
                'type': 'character',
                'name': char_name,
                'display_text': f"{char_name} ({len(char_effects)}個の効果)",
                'effect_count': len(char_effects),
                'has_debuffs': any(self._is_debuff(effect) for effect in char_effects),
                'has_removable': any(effect.get('removable', False) for effect in char_effects if isinstance(effect, dict)),
                'character': character
            }
            menu_items.append(char_item)
            
            # 個別効果のアイテム
            for effect in char_effects:
                if isinstance(effect, dict):
                    effect_name = effect.get('name', 'Unknown')
                    effect_item = {
                        'type': 'effect',
                        'name': effect_name,
                        'display_text': self._generate_effect_display_text(effect),
                        'icon': self.effect_icons.get(effect_name, '?'),
                        'removable': effect.get('removable', False),
                        'is_debuff': self._is_debuff(effect),
                        'character': character,
                        'effect': effect
                    }
                    menu_items.append(effect_item)
        
        return menu_items
    
    def generate_removal_menu_items(self, character, effects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """除去メニューアイテムを生成
        
        Args:
            character: キャラクターオブジェクト
            effects: 効果リスト
            
        Returns:
            List: 除去メニューアイテムリスト
        """
        menu_items = []
        
        for effect in effects:
            if not isinstance(effect, dict) or not effect.get('removable', False):
                continue
            
            effect_name = effect.get('name', 'Unknown')
            item = {
                'name': effect_name,
                'display_text': f"除去: {self._generate_effect_display_text(effect)}",
                'icon': self.effect_icons.get(effect_name, '?'),
                'confirm_text': f"【{effect_name}】を除去しますか？",
                'character': character,
                'effect': effect
            }
            menu_items.append(item)
        
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
            'header_rects': [],
            'content_rects': [],
            'action_rects': [],
            'scroll_info': {
                'total_height': 0,
                'visible_height': container_rect.height,
                'scroll_position': 0,
                'can_scroll': False
            }
        }
        
        current_y = container_rect.y + 15
        margin_x = 15
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
            current_y += title_height + 15
        
        # キャラクター別コンテンツレイアウト
        character_summaries = content.get('character_summaries', [])
        for char_summary in character_summaries:
            char_height = self._calculate_character_summary_height(char_summary)
            char_rect = pygame.Rect(
                container_rect.x + margin_x,
                current_y,
                content_width,
                char_height
            )
            layout['content_rects'].append(char_rect)
            current_y += char_height + self.item_spacing
        
        # アクションボタンレイアウト
        action_height = 40
        action_rect = pygame.Rect(
            container_rect.x + margin_x,
            current_y,
            content_width,
            action_height
        )
        layout['action_rects'].append(action_rect)
        current_y += action_height + 10
        
        # スクロール情報
        layout['scroll_info']['total_height'] = current_y - container_rect.y
        layout['scroll_info']['can_scroll'] = (
            layout['scroll_info']['total_height'] > layout['scroll_info']['visible_height']
        )
        
        return layout
    
    def _format_single_effect(self, effect: Dict[str, Any], mode: DisplayMode) -> Dict[str, Any]:
        """単一効果をフォーマット"""
        effect_name = effect.get('name', 'Unknown')
        
        formatted = {
            'name': effect_name,
            'display_name': effect.get('display_name', effect_name.title()),
            'icon': self.effect_icons.get(effect_name, '?'),
            'color': self._get_effect_color(effect),
            'removable': effect.get('removable', False)
        }
        
        if mode == DisplayMode.DETAILED:
            formatted.update({
                'description': effect.get('description', ''),
                'duration_text': self._format_duration_text(effect),
                'intensity_text': self._format_intensity_text(effect),
                'source_text': effect.get('source', '不明')
            })
        elif mode == DisplayMode.COMPACT:
            formatted['compact_text'] = self._generate_compact_text(effect)
        else:  # LIST mode
            formatted['display_text'] = self._generate_effect_display_text(effect)
        
        return formatted
    
    def _format_type_distribution(self, type_data: Dict[str, int]) -> Dict[str, Any]:
        """タイプ分布をフォーマット"""
        total = sum(type_data.values())
        
        return {
            'total': total,
            'buff_count': type_data.get('buff', 0),
            'debuff_count': type_data.get('debuff', 0),
            'neutral_count': type_data.get('neutral', 0),
            'buff_percentage': (type_data.get('buff', 0) / total * 100) if total > 0 else 0,
            'debuff_percentage': (type_data.get('debuff', 0) / total * 100) if total > 0 else 0
        }
    
    def _format_category_breakdown(self, category_data: Dict[str, int]) -> Dict[str, Any]:
        """カテゴリ分布をフォーマット"""
        return {
            'damage_over_time': category_data.get('damage_over_time', 0),
            'stat_modifier': category_data.get('stat_modifier', 0),
            'condition': category_data.get('condition', 0),
            'enhancement': category_data.get('enhancement', 0),
            'protection': category_data.get('protection', 0)
        }
    
    def _generate_character_status_text(self, char_data: Dict[str, Any]) -> str:
        """キャラクターステータステキストを生成"""
        total = char_data.get('total', 0)
        buffs = char_data.get('buffs', 0)
        debuffs = char_data.get('debuffs', 0)
        
        if total == 0:
            return "効果なし"
        
        parts = []
        if buffs > 0:
            parts.append(f"バフ{buffs}個")
        if debuffs > 0:
            parts.append(f"デバフ{debuffs}個")
        
        return "、".join(parts) if parts else f"効果{total}個"
    
    def _generate_character_icon_summary(self, effects: List[Dict[str, Any]]) -> str:
        """キャラクターアイコンサマリーを生成"""
        icons = []
        for effect in effects[:5]:  # 最大5個まで表示
            if isinstance(effect, dict):
                effect_name = effect.get('name', '')
                icon = self.effect_icons.get(effect_name, '?')
                icons.append(icon)
        
        if len(effects) > 5:
            icons.append('...')
        
        return ' '.join(icons)
    
    def _format_duration_info(self, effect: Dict[str, Any]) -> Dict[str, Any]:
        """持続時間情報をフォーマット"""
        turns_remaining = effect.get('turns_remaining', -1)
        
        return {
            'turns_remaining': turns_remaining,
            'is_permanent': turns_remaining < 0,
            'is_expiring_soon': 0 < turns_remaining <= 3,
            'duration_text': self._format_duration_text(effect)
        }
    
    def _format_duration_text(self, effect: Dict[str, Any]) -> str:
        """持続時間テキストをフォーマット"""
        turns_remaining = effect.get('turns_remaining', -1)
        
        if turns_remaining < 0:
            return "永続"
        elif turns_remaining == 0:
            return "まもなく終了"
        elif turns_remaining == 1:
            return "残り1ターン"
        else:
            return f"残り{turns_remaining}ターン"
    
    def _format_intensity_info(self, effect: Dict[str, Any]) -> Dict[str, Any]:
        """強度情報をフォーマット"""
        intensity = effect.get('intensity', 1)
        severity = effect.get('severity', 'medium')
        
        return {
            'intensity': intensity,
            'severity': severity,
            'intensity_text': self._format_intensity_text(effect)
        }
    
    def _format_intensity_text(self, effect: Dict[str, Any]) -> str:
        """強度テキストをフォーマット"""
        intensity = effect.get('intensity', 1)
        severity = effect.get('severity', 'medium')
        
        if intensity > 1:
            return f"強度 {intensity}"
        
        severity_text = {
            'low': '軽微',
            'medium': '中程度',
            'high': '重篤'
        }
        
        return severity_text.get(severity, '通常')
    
    def _format_source_info(self, effect: Dict[str, Any]) -> Dict[str, Any]:
        """発生源情報をフォーマット"""
        source = effect.get('source', '不明')
        source_type = effect.get('source_type', 'unknown')
        
        return {
            'source': source,
            'source_type': source_type,
            'source_text': f"発生源: {source}"
        }
    
    def _generate_effect_display_text(self, effect: Dict[str, Any]) -> str:
        """効果表示テキストを生成"""
        effect_name = effect.get('display_name', effect.get('name', 'Unknown'))
        icon = self.effect_icons.get(effect.get('name', ''), '?')
        duration_text = self._format_duration_text(effect)
        
        return f"{icon} {effect_name} ({duration_text})"
    
    def _generate_compact_text(self, effect: Dict[str, Any]) -> str:
        """コンパクトテキストを生成"""
        icon = self.effect_icons.get(effect.get('name', ''), '?')
        turns_remaining = effect.get('turns_remaining', -1)
        
        if turns_remaining > 0:
            return f"{icon}{turns_remaining}"
        else:
            return icon
    
    def _get_effect_color(self, effect: Dict[str, Any]) -> Tuple[int, int, int]:
        """効果カラーを取得"""
        if self._is_debuff(effect):
            return self.colors['debuff']
        elif self._is_buff(effect):
            return self.colors['buff']
        else:
            return self.colors['neutral']
    
    def _is_debuff(self, effect: Dict[str, Any]) -> bool:
        """デバフかどうか判定"""
        effect_type = effect.get('type', 'neutral')
        return effect_type == 'debuff'
    
    def _is_buff(self, effect: Dict[str, Any]) -> bool:
        """バフかどうか判定"""
        effect_type = effect.get('type', 'neutral')
        return effect_type == 'buff'
    
    def _calculate_character_summary_height(self, char_summary: Dict[str, Any]) -> int:
        """キャラクターサマリーの高さを計算"""
        base_height = self.header_font_size + 10
        effect_count = char_summary.get('total', 0)
        
        # 効果の個数に応じて高さを調整
        if effect_count > 0:
            base_height += min(effect_count, 3) * self.line_spacing
        
        return max(base_height, 60)  # 最小高さ