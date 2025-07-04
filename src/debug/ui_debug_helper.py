"""
UI階層デバッグヘルパー

pygame-guiとWindowManagerのUI階層をダンプし、デバッグを支援する機能を提供。
"""

import json
import logging
from typing import Dict, List, Any, Optional, Union
import pygame
import pygame_gui

logger = logging.getLogger(__name__)


class UIDebugHelper:
    """UI階層のデバッグを支援するヘルパークラス"""
    
    def __init__(self, ui_manager: Optional[pygame_gui.UIManager] = None):
        """
        初期化
        
        Args:
            ui_manager: pygame-guiのUIManagerインスタンス
        """
        self.ui_manager = ui_manager
        self._window_manager = None
    
    @property
    def window_manager(self):
        """WindowManagerのインスタンスを取得"""
        if self._window_manager is None:
            try:
                from src.ui.window_system import WindowManager
                self._window_manager = WindowManager.get_instance()
            except ImportError:
                logger.warning("WindowManager not available")
        return self._window_manager
    
    def dump_ui_hierarchy(self, format: str = 'json') -> Union[Dict[str, Any], str]:
        """
        UI階層をダンプ
        
        Args:
            format: 出力形式 ('json' または 'tree')
            
        Returns:
            UI階層情報（辞書またはツリー形式の文字列）
        """
        hierarchy = {
            'windows': [],
            'ui_elements': [],
            'window_stack': []
        }
        
        try:
            # WindowManagerからウィンドウ情報を取得
            if self.window_manager:
                hierarchy['windows'] = self._get_windows_info()
                hierarchy['window_stack'] = list(self.window_manager.window_stack)
            
            # pygame-guiからUI要素情報を取得
            if self.ui_manager:
                hierarchy['ui_elements'] = self._get_ui_elements_info()
        
        except Exception as e:
            logger.error(f"Error dumping UI hierarchy: {e}")
            hierarchy['error'] = str(e)
        
        if format == 'tree':
            return self._format_as_tree(hierarchy)
        
        return hierarchy
    
    def get_active_windows(self) -> List[Dict[str, Any]]:
        """アクティブ（表示されている）ウィンドウのリストを取得"""
        windows = []
        
        if self.window_manager:
            for window_id, window in self.window_manager.windows.items():
                if hasattr(window, 'visible') and window.visible:
                    windows.append(self._extract_window_info(window_id, window))
        
        return windows
    
    def get_ui_elements(self) -> List[Dict[str, Any]]:
        """すべてのUI要素のリストを取得"""
        elements = []
        
        if self.ui_manager:
            try:
                # pygame-guiのスプライトグループから要素を取得
                sprite_group = self.ui_manager.get_sprite_group()
                # LayeredGUIGroupのspritesメソッドまたはプロパティを使用
                if hasattr(sprite_group, 'sprites'):
                    sprites = sprite_group.sprites()
                else:
                    sprites = list(sprite_group)
                    
                for sprite in sprites:
                    # UIElementのインスタンスのみを対象にする
                    if hasattr(sprite, 'object_ids'):
                        elements.append(self._extract_element_info(sprite))
            except Exception as e:
                logger.warning(f"Error getting UI elements: {e}")
        
        return elements
    
    def find_element_by_id(self, object_id: str) -> Optional[Dict[str, Any]]:
        """指定されたIDを持つUI要素を検索"""
        if not self.ui_manager:
            return None
        
        try:
            sprite_group = self.ui_manager.get_sprite_group()
            if hasattr(sprite_group, 'sprites'):
                sprites = sprite_group.sprites()
            else:
                sprites = list(sprite_group)
                
            for sprite in sprites:
                if hasattr(sprite, 'object_ids'):
                    element_ids = getattr(sprite, 'object_ids', [])
                    if object_id in element_ids:
                        return self._extract_element_info(sprite)
        except Exception as e:
            logger.warning(f"Error finding element by ID: {e}")
        
        return None
    
    def get_element_hierarchy(self) -> List[Dict[str, Any]]:
        """UI要素の親子関係を含む階層構造を取得"""
        if not self.ui_manager:
            return []
        
        # ルート要素を見つける
        root_elements = []
        all_elements = []
        
        try:
            sprite_group = self.ui_manager.get_sprite_group()
            if hasattr(sprite_group, 'sprites'):
                sprites = sprite_group.sprites()
            else:
                sprites = list(sprite_group)
            raw_elements = [sprite for sprite in sprites if hasattr(sprite, 'object_ids')]
            
            # 要素情報を抽出
            for element in raw_elements:
                element_info = self._extract_element_info(element)
                element_info['_raw'] = element  # 元のオブジェクトを保持
                all_elements.append(element_info)
            
            # 親子関係を構築
            for element_info in all_elements:
                element = element_info['_raw']
                parent = getattr(element, 'ui_container', None)
                
                if parent is None:
                    # ルート要素
                    element_info['children'] = []
                    root_elements.append(element_info)
                else:
                    # 親要素を探す
                    for parent_info in all_elements:
                        if parent_info['_raw'] == parent:
                            if 'children' not in parent_info:
                                parent_info['children'] = []
                            parent_info['children'].append(element_info)
                            break
            
            # 元のオブジェクト参照を削除
            self._clean_raw_references(root_elements)
            
        except Exception as e:
            logger.warning(f"Error getting element hierarchy: {e}")
            return []
        
        return root_elements
    
    def _get_windows_info(self) -> List[Dict[str, Any]]:
        """WindowManagerからウィンドウ情報を取得"""
        windows = []
        
        if self.window_manager and hasattr(self.window_manager, 'windows'):
            for window_id, window in self.window_manager.windows.items():
                windows.append(self._extract_window_info(window_id, window))
        
        return windows
    
    def _get_ui_elements_info(self) -> List[Dict[str, Any]]:
        """pygame-guiからUI要素情報を取得"""
        elements = []
        
        try:
            sprite_group = self.ui_manager.get_sprite_group()
            if hasattr(sprite_group, 'sprites'):
                sprites = sprite_group.sprites()
            else:
                sprites = list(sprite_group)
                
            for sprite in sprites:
                if hasattr(sprite, 'object_ids'):
                    elements.append(self._extract_element_info(sprite))
        except Exception as e:
            # エラーを再発生させて上位でキャッチ
            raise e
        
        return elements
    
    def _extract_window_info(self, window_id: str, window: Any) -> Dict[str, Any]:
        """ウィンドウオブジェクトから情報を抽出"""
        info = {
            'id': window_id,
            'type': window.__class__.__name__,
            'visible': getattr(window, 'visible', False)
        }
        
        # 位置とサイズ情報
        if hasattr(window, 'rect'):
            rect = window.rect
            info['position'] = {'x': rect.x, 'y': rect.y}
            info['size'] = {'width': rect.width, 'height': rect.height}
        
        return info
    
    def _extract_element_info(self, element: Any) -> Dict[str, Any]:
        """UI要素から情報を抽出"""
        info = {
            'type': element.__class__.__name__,
            'visible': bool(getattr(element, 'visible', 0))
        }
        
        # object_id情報
        if hasattr(element, 'object_ids'):
            ids = element.object_ids
            info['object_id'] = ids[0] if ids else 'unknown'
            info['object_ids'] = ids
        else:
            info['object_id'] = 'unknown'
            info['object_ids'] = []
        
        # 位置とサイズ情報
        if hasattr(element, 'rect'):
            rect = element.rect
            info['position'] = {'x': rect.x, 'y': rect.y}
            info['size'] = {'width': rect.width, 'height': rect.height}
        
        # 追加属性（verbose mode用）
        if hasattr(element, 'text'):
            info.setdefault('attributes', {})['text'] = str(element.text)
        if hasattr(element, 'enabled'):
            info.setdefault('attributes', {})['enabled'] = bool(element.enabled)
        if hasattr(element, 'tooltip_text'):
            info.setdefault('attributes', {})['tooltip'] = str(element.tooltip_text)
        
        return info
    
    def _format_as_tree(self, hierarchy: Dict[str, Any]) -> str:
        """階層情報をツリー形式の文字列に変換"""
        lines = ["UI Hierarchy Tree:"]
        
        windows = hierarchy.get('windows', [])
        ui_elements = hierarchy.get('ui_elements', [])
        window_stack = hierarchy.get('window_stack', [])
        
        # window_stackが存在する場合は、それを表示
        if window_stack:
            lines.append("├── Window Stack:")
            for i, window_str in enumerate(window_stack):
                is_last = i == len(window_stack) - 1
                prefix = "│   └── " if is_last else "│   ├── "
                lines.append(f"{prefix}{window_str}")
        
        # ウィンドウをツリー表示
        has_content_above = bool(window_stack)
        for i, window in enumerate(windows):
            is_last_window = i == len(windows) - 1 and not ui_elements
            if has_content_above:
                window_prefix = "├── " if not is_last_window or ui_elements else "└── "
            else:
                window_prefix = "└── " if is_last_window and not ui_elements else "├── "
            window_status = "[visible]" if window.get('visible') else "[hidden]"
            lines.append(f"{window_prefix}{window['type']} ({window['id']}) {window_status}")
            
            # そのウィンドウに属するUI要素を表示
            for j, element in enumerate(ui_elements):
                is_last_element = j == len(ui_elements) - 1
                if is_last_window and not has_content_above:
                    elem_prefix = "    └── " if is_last_element else "    ├── "
                else:
                    elem_prefix = "│   └── " if is_last_element else "│   ├── "
                elem_status = "[visible]" if element.get('visible') else "[hidden]"
                lines.append(f"{elem_prefix}{element['type']} ({element['object_id']}) {elem_status}")
        
        # ウィンドウがない場合は、UI要素のみを表示
        if not windows and ui_elements:
            ui_prefix = "├── " if window_stack else "└── "
            lines.append(f"{ui_prefix}UI Elements:")
            for i, element in enumerate(ui_elements):
                is_last = i == len(ui_elements) - 1
                if window_stack:
                    prefix = "│   └── " if is_last else "│   ├── "
                else:
                    prefix = "    └── " if is_last else "    ├── "
                status = "[visible]" if element.get('visible') else "[hidden]"
                lines.append(f"{prefix}{element['type']} ({element['object_id']}) {status}")
        
        # 何も表示する内容がない場合
        if not window_stack and not windows and not ui_elements:
            lines.append("└── (No UI information available)")
        
        return "\n".join(lines)
    
    def _clean_raw_references(self, elements: List[Dict[str, Any]]) -> None:
        """要素から生のオブジェクト参照を再帰的に削除"""
        for element in elements:
            if '_raw' in element:
                del element['_raw']
            if 'children' in element:
                self._clean_raw_references(element['children'])