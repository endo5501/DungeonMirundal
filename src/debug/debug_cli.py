"""
デバッグコマンドラインインターフェース

UI階層のダンプやデバッグ機能を提供するCLIツール。
"""

import click
import json
import sys
import logging
from pathlib import Path
from typing import Optional

from src.debug.game_debug_client import GameDebugClient
from src.debug.ui_debug_helper import UIDebugHelper

logger = logging.getLogger(__name__)


@click.group()
def debug_cli():
    """ゲームデバッグコマンド"""
    pass


@debug_cli.command(name='ui-dump')
@click.option('--save', '-s', type=click.Path(), help='保存先ファイルパス')
@click.option('--format', '-f', type=click.Choice(['json', 'tree']), default='json', help='出力形式')
@click.option('--filter', '-t', help='特定のタイプのみ表示（例：UIButton）')
@click.option('--verbose', '-v', is_flag=True, help='詳細情報を表示')
def ui_dump(save: Optional[str], format: str, filter: Optional[str], verbose: bool):
    """現在のUI階層をダンプ"""
    client = GameDebugClient()
    
    # APIが利用可能か確認
    if not client.wait_for_api():
        click.echo("Error: Game API is not available", err=True)
        sys.exit(1)
    
    try:
        # API経由でUI階層を取得
        hierarchy = client.get_ui_hierarchy()
        
        if hierarchy is None:
            click.echo("Error: Failed to get UI hierarchy from game", err=True)
            sys.exit(1)
        
        # formatがtreeの場合は、UIDebugHelperでツリー形式に変換
        if format == 'tree':
            ui_helper = UIDebugHelper()
            hierarchy = ui_helper._format_as_tree(hierarchy)
        
        # フィルタリング
        if filter and format == 'json':
            filtered_hierarchy = {
                'windows': [w for w in hierarchy.get('windows', []) if filter in w.get('type', '')],
                'ui_elements': [e for e in hierarchy.get('ui_elements', []) if filter in e.get('type', '')],
                'window_stack': hierarchy.get('window_stack', [])
            }
            hierarchy = filtered_hierarchy
        
        # 出力形式に応じて表示
        if format == 'json':
            output = json.dumps(hierarchy, indent=2, ensure_ascii=False)
        else:
            output = hierarchy
        
        # 詳細モードの処理
        if verbose and format == 'json':
            # 属性情報を含む完全な出力
            click.echo(output)
        elif format == 'json':
            # 詳細情報を含む改良された出力
            enhanced_hierarchy = _enhance_hierarchy_for_json(hierarchy)
            output = json.dumps(enhanced_hierarchy, indent=2, ensure_ascii=False)
            click.echo(output)
        else:
            click.echo(output)
        
        # ファイルに保存
        if save:
            save_path = Path(save)
            with open(save_path, 'w', encoding='utf-8') as f:
                if format == 'json':
                    json.dump(hierarchy, f, indent=2, ensure_ascii=False)
                else:
                    f.write(str(hierarchy))
            click.echo(f"UI hierarchy saved to {save_path}")
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@debug_cli.command(name='ui-find')
@click.argument('object_id')
def ui_find(object_id: str):
    """指定されたIDのUI要素を検索"""
    client = GameDebugClient()
    
    if not client.wait_for_api():
        click.echo("Error: Game API is not available", err=True)
        sys.exit(1)
    
    try:
        # API経由でUI階層を取得
        hierarchy = client.get_ui_hierarchy()
        
        if hierarchy is None:
            click.echo("Error: Failed to get UI hierarchy from game", err=True)
            sys.exit(1)
        
        # UI要素を検索
        found_element = None
        for element in hierarchy.get('ui_elements', []):
            if element.get('object_id') == object_id or object_id in element.get('object_ids', []):
                found_element = element
                break
        
        if found_element:
            click.echo(f"Found UI element '{object_id}':")
            click.echo(json.dumps(found_element, indent=2, ensure_ascii=False))
        else:
            click.echo(f"UI element '{object_id}' not found")
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@debug_cli.command(name='ui-tree')
def ui_tree():
    """UI要素の階層構造をツリー形式で表示"""
    client = GameDebugClient()
    
    if not client.wait_for_api():
        click.echo("Error: Game API is not available", err=True)
        sys.exit(1)
    
    try:
        # API経由でUI階層を取得
        hierarchy = client.get_ui_hierarchy()
        
        if hierarchy is None:
            click.echo("Error: Failed to get UI hierarchy from game", err=True)
            sys.exit(1)
        
        # UIDebugHelperを使ってツリー形式に変換
        ui_helper = UIDebugHelper()
        tree_output = ui_helper._format_as_tree(hierarchy)
        
        click.echo(tree_output)
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _enhance_hierarchy_for_json(hierarchy: dict) -> dict:
    """JSON出力用に階層情報を拡張（詳細情報と階層構造を保持）"""
    enhanced = {
        'windows': [],
        'ui_elements': [],
        'window_stack': hierarchy.get('window_stack', []),
        'metadata': {
            'format': 'enhanced_json',
            'includes_shortcuts': True,
            'includes_hierarchy': True
        }
    }
    
    # ウィンドウ情報の詳細化
    for window in hierarchy.get('windows', []):
        enhanced_win = {
            'id': window.get('id'),
            'type': window.get('type'),
            'visible': window.get('visible')
        }
        # 全ての利用可能な属性を保持
        for key in ['state', 'modal', 'position', 'size', 'has_ui_manager']:
            if key in window:
                enhanced_win[key] = window[key]
        enhanced['windows'].append(enhanced_win)
    
    # UI要素情報の拡張（階層構造を保持）
    enhanced['ui_elements'] = _process_ui_elements_hierarchy(hierarchy.get('ui_elements', []))
    
    return enhanced

def _process_ui_elements_hierarchy(elements: list) -> list:
    """UI要素を階層構造で処理し、ショートカットキー情報を含める"""
    processed = []
    
    for element in elements:
        enhanced_elem = {
            'object_id': element.get('object_id', 'unknown'),
            'type': element.get('type', 'Unknown'),
            'visible': element.get('visible', False)
        }
        
        # 位置とサイズ情報
        if 'position' in element:
            enhanced_elem['position'] = element['position']
        if 'size' in element:
            enhanced_elem['size'] = element['size']
        
        # 詳細情報を拡張
        if 'details' in element:
            details = element['details']
            enhanced_elem['details'] = details.copy()
            
            # ショートカットキー情報を明示的に追加
            if 'shortcut_key' in details:
                enhanced_elem['shortcut_key'] = details['shortcut_key']
            elif 'auto_shortcut' in details:
                enhanced_elem['shortcut_key'] = details['auto_shortcut']
            
            # メニューアイテム情報
            if 'menu_item_data' in details:
                menu_data = details['menu_item_data']
                if isinstance(menu_data, dict):
                    enhanced_elem['menu'] = {
                        'label': menu_data.get('label'),
                        'id': menu_data.get('id'),
                        'enabled': menu_data.get('enabled', True)
                    }
            
            # テキストと状態
            if 'text' in details:
                enhanced_elem['text'] = details['text']
            if 'enabled' in details:
                enhanced_elem['enabled'] = details['enabled']
        
        # 子要素を再帰的に処理
        if 'children' in element:
            enhanced_elem['children'] = _process_ui_elements_hierarchy(element['children'])
        
        processed.append(enhanced_elem)
    
    return processed

def _simplify_hierarchy(hierarchy: dict) -> dict:
    """階層情報を簡略化（基本情報のみ）- 後方互換性のために保持"""
    return _enhance_hierarchy_for_json(hierarchy)


def _print_element_tree(element: dict, depth: int) -> None:
    """要素をツリー形式で出力"""
    indent = "  " * depth
    prefix = "└── " if depth > 0 else ""
    
    object_id = element.get('object_id', 'unknown')
    element_type = element.get('type', 'Unknown')
    visible = "[visible]" if element.get('visible') else "[hidden]"
    
    click.echo(f"{indent}{prefix}{element_type} ({object_id}) {visible}")
    
    # 子要素を再帰的に表示
    for child in element.get('children', []):
        _print_element_tree(child, depth + 1)


def main():
    """メインエントリーポイント"""
    debug_cli()


if __name__ == '__main__':
    main()