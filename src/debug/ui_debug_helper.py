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
                all_elements = self.ui_manager.get_all_ui_elements()
                for element in all_elements:
                    elements.append(self._extract_element_info(element))
            except AttributeError:
                logger.warning("UIManager does not have get_all_ui_elements method")
        
        return elements
    
    def find_element_by_id(self, object_id: str) -> Optional[Dict[str, Any]]:
        """指定されたIDを持つUI要素を検索"""
        if not self.ui_manager:
            return None
        
        try:
            all_elements = self.ui_manager.get_all_ui_elements()
            for element in all_elements:
                element_ids = getattr(element, 'object_ids', [])
                if object_id in element_ids:
                    return self._extract_element_info(element)
        except AttributeError:
            logger.warning("UIManager does not have get_all_ui_elements method")
        
        return None
    
    def get_element_hierarchy(self) -> List[Dict[str, Any]]:
        """UI要素の親子関係を含む階層構造を取得"""
        if not self.ui_manager:
            return []
        
        # ルート要素を見つける
        root_elements = []
        all_elements = []
        
        try:
            raw_elements = self.ui_manager.get_all_ui_elements()
            
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
            all_elements = self.ui_manager.get_all_ui_elements()
            for element in all_elements:
                elements.append(self._extract_element_info(element))
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
        
        # ウィンドウをツリー表示
        for i, window in enumerate(windows):
            is_last_window = i == len(windows) - 1
            window_prefix = "└── " if is_last_window else "├── "
            window_status = "[visible]" if window.get('visible') else "[hidden]"
            lines.append(f"{window_prefix}{window['type']} ({window['id']}) {window_status}")
            
            # そのウィンドウに属するUI要素を表示
            for j, element in enumerate(ui_elements):
                is_last_element = j == len(ui_elements) - 1
                if is_last_window:
                    elem_prefix = "    └── " if is_last_element else "    ├── "
                else:
                    elem_prefix = "│   └── " if is_last_element else "│   ├── "
                elem_status = "[visible]" if element.get('visible') else "[hidden]"
                lines.append(f"{elem_prefix}{element['type']} ({element['object_id']}) {elem_status}")
        
        # ウィンドウがない場合は、UI要素のみを表示
        if not windows and ui_elements:
            for i, element in enumerate(ui_elements):
                is_last = i == len(ui_elements) - 1
                prefix = "└── " if is_last else "├── "
                status = "[visible]" if element.get('visible') else "[hidden]"
                lines.append(f"{prefix}{element['type']} ({element['object_id']}) {status}")
        
        return "\n".join(lines)
    
    def _clean_raw_references(self, elements: List[Dict[str, Any]]) -> None:
        """要素から生のオブジェクト参照を再帰的に削除"""
        for element in elements:
            if '_raw' in element:
                del element['_raw']
            if 'children' in element:
                self._clean_raw_references(element['children'])