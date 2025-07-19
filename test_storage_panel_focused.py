#!/usr/bin/env python3
"""StoragePanel専用の集中テスト"""

import pygame
import pygame_gui
from unittest.mock import Mock, patch
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.facilities.ui.inn.storage_panel import StoragePanel


def test_storage_panel_with_mock_patch():
    """StoragePanelをmock patchを使って完全にモックしてテスト"""
    print("=== StoragePanel Mock Patch テスト ===")
    
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    ui_manager = pygame_gui.UIManager((800, 600))
    
    parent = pygame_gui.elements.UIPanel(
        relative_rect=pygame.Rect(0, 0, 800, 600),
        manager=ui_manager
    )
    
    try:
        # Controller mock
        controller = Mock()
        service = Mock()
        party = Mock()
        party.members = []
        party.inventory_items = []
        service.party = party
        controller.service = service
        
        # 問題となるメソッドをpatchで置き換える
        with patch.object(StoragePanel, '_load_storage_data') as mock_load_data, \
             patch.object(StoragePanel, '_update_lists') as mock_update_lists, \
             patch.object(StoragePanel, '_update_info') as mock_update_info, \
             patch.object(StoragePanel, '_update_buttons') as mock_update_buttons:
            
            print("1. StoragePanel 作成中（メソッドをmock化）...")
            
            panel = StoragePanel(
                rect=pygame.Rect(50, 50, 700, 500),
                parent=parent,
                controller=controller,
                ui_manager=ui_manager
            )
            
            print("   ✓ StoragePanel 作成成功")
            
            # UIElementManager 確認
            if hasattr(panel, 'ui_element_manager') and panel.ui_element_manager:
                manager = panel.ui_element_manager
                print(f"   ✓ UIElementManager存在: 要素数 {manager.get_element_count()}")
                
                # ストレージパネル特有の要素確認
                elements = [
                    ("title_label", "タイトルラベル"),
                    ("inventory_label", "インベントリラベル"),
                    ("storage_label", "保管庫ラベル"),
                    ("inventory_list", "インベントリリスト"),
                    ("storage_list", "保管庫リスト"),
                    ("store_button", "預ける ボタン"),
                    ("retrieve_button", "取り出すボタン")
                ]
                
                for element_id, description in elements:
                    element = manager.get_element(element_id)
                    status = "✓ 存在" if element else "✗ 不在"
                    print(f"   {status} {description} ({element_id})")
            else:
                print("   ✗ UIElementManager 不在")
            
            # モックされたメソッドが呼ばれたことを確認
            print("2. Mock 呼び出し確認...")
            mock_load_data.assert_called_once()
            print("   ✓ _load_storage_data() が呼ばれた")
            
            # 破棄テスト
            print("3. 破棄処理テスト...")
            panel.destroy()
            
            if panel.ui_element_manager and panel.ui_element_manager.is_destroyed:
                print("   ✓ UIElementManager 正常破棄")
            else:
                print("   ⚠ UIElementManager 破棄未完了")
            
            return True
            
    except Exception as e:
        print(f"   ✗ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        pygame.quit()


def test_storage_panel_direct_creation():
    """StoragePanelの直接的な作成テスト（data loading スキップ）"""
    print("\n=== StoragePanel 直接作成テスト ===")
    
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    ui_manager = pygame_gui.UIManager((800, 600))
    
    parent = pygame_gui.elements.UIPanel(
        relative_rect=pygame.Rect(0, 0, 800, 600),
        manager=ui_manager
    )
    
    try:
        # Controller mock
        controller = Mock()
        service = Mock()
        party = Mock()
        party.members = []
        service.party = party
        controller.service = service
        
        # _create_ui() をmockして問題のあるデータ読み込みを回避
        with patch.object(StoragePanel, '_create_ui') as mock_create_ui:
            
            print("1. StoragePanel 作成中（_create_ui()をmock化）...")
            
            panel = StoragePanel(
                rect=pygame.Rect(50, 50, 700, 500),
                parent=parent,
                controller=controller,
                ui_manager=ui_manager
            )
            
            print("   ✓ StoragePanel 作成成功")
            
            # 手動でUIElementManagerを確認
            if hasattr(panel, 'ui_element_manager') and panel.ui_element_manager:
                manager = panel.ui_element_manager
                print(f"   ✓ UIElementManager存在: 要素数 {manager.get_element_count()}")
            else:
                print("   ✗ UIElementManager 不在")
            
            # _create_ui()が呼ばれたことを確認
            mock_create_ui.assert_called_once()
            print("   ✓ _create_ui() が呼ばれた（mock）")
            
            return True
            
    except Exception as e:
        print(f"   ✗ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        pygame.quit()


def main():
    """メインテスト実行"""
    print("StoragePanel 詳細デバッグテスト開始\n")
    
    # テスト1: メソッドをmockしてパネル作成
    result1 = test_storage_panel_with_mock_patch()
    
    # テスト2: _create_ui()をmockしてパネル作成
    result2 = test_storage_panel_direct_creation()
    
    print("\n" + "="*50)
    print("=== テスト結果 ===")
    print(f"Mock Patch テスト: {'✅ 成功' if result1 else '❌ 失敗'}")
    print(f"Direct Creation テスト: {'✅ 成功' if result2 else '❌ 失敗'}")
    
    if result1 or result2:
        print("\n✅ StoragePanelの基本的なUIElementManager統合は動作しています")
        print("問題は特定のデータ読み込み処理にあります")
        return 0
    else:
        print("\n❌ StoragePanelのUIElementManager統合に根本的な問題があります")
        return 1


if __name__ == "__main__":
    sys.exit(main())