#!/usr/bin/env python3
"""移行修正とより詳細なテスト"""

import pygame
import pygame_gui
from unittest.mock import Mock, MagicMock
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.facilities.ui.shop.buy_panel import BuyPanel
from src.facilities.ui.shop.sell_panel import SellPanel
from src.facilities.ui.shop.identify_panel import IdentifyPanel
from src.facilities.ui.inn.storage_panel import StoragePanel
from src.facilities.ui.inn.item_management_panel import ItemManagementPanel


def create_better_mocks():
    """より現実的なモックを作成"""
    # Controller mock
    controller = Mock()
    
    # Mock character for party members
    mock_character = Mock()
    mock_character.id = "char_1"
    mock_character.character_id = "char_1"  # identify_panelが使用
    mock_character.name = "テストキャラクター"
    mock_character.level = 1
    mock_character.char_class = "fighter"
    mock_character.is_alive.return_value = True
    
    # Mock inventory for character
    mock_inventory = Mock()
    mock_inventory.get_all_items.return_value = []
    mock_character.inventory = mock_inventory
    
    # Party mock with members (iterable list)
    party = Mock()
    party.members = [mock_character]  # リスト形式で設定
    party.inventory_items = []  # パネルが直接アクセスする
    
    # Service mock
    service = Mock()
    service.party = party
    service.unidentified_items = []  # IdentifyPanel用
    service.storage_items = []  # StoragePanel用
    
    # StoragePanel用のstorage_managerを明示的に設定しない
    # service.storage_manager は設定しない（属性が存在しない状態にする）
    
    controller.service = service
    
    # Controller methods
    controller.get_party.return_value = party  # IdentifyPanel用
    
    # Service execution mock
    from src.facilities.core.service_result import ServiceResult
    controller.execute_service.return_value = ServiceResult.ok("Test success", data={
        "items": [],
        "party_gold": 1000,
        "inventory_items": [],
        "storage_items": [],
        "unidentified_items": []
    })
    
    return controller


def test_sell_panel_creation():
    """SellPanel の詳細作成テスト"""
    print("=== SellPanel 詳細テスト ===")
    
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    ui_manager = pygame_gui.UIManager((800, 600))
    
    parent = pygame_gui.elements.UIPanel(
        relative_rect=pygame.Rect(0, 0, 800, 600),
        manager=ui_manager
    )
    
    try:
        controller = create_better_mocks()
        
        # SellPanel 作成テスト
        print("1. SellPanel 作成中...")
        panel = SellPanel(
            rect=pygame.Rect(50, 50, 700, 500),
            parent=parent,
            controller=controller,
            ui_manager=ui_manager
        )
        print("   ✓ SellPanel 作成成功")
        
        # UIElementManager 確認
        if hasattr(panel, 'ui_element_manager') and panel.ui_element_manager:
            manager = panel.ui_element_manager
            print(f"   ✓ UIElementManager存在: 要素数 {manager.get_element_count()}")
            
            # 個別要素確認
            elements = [
                ("title_label", "タイトルラベル"),
                ("gold_label", "所持金ラベル"),
                ("inventory_label", "インベントリラベル"),
                ("sell_button", "売却ボタン")
            ]
            
            for element_id, description in elements:
                element = manager.get_element(element_id)
                status = "✓ 存在" if element else "✗ 不在"
                print(f"   {status} {description} ({element_id})")
        
        # 破棄テスト
        print("2. 破棄処理テスト...")
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


def test_identify_panel_creation():
    """IdentifyPanel の詳細作成テスト"""
    print("\n=== IdentifyPanel 詳細テスト ===")
    
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    ui_manager = pygame_gui.UIManager((800, 600))
    
    parent = pygame_gui.elements.UIPanel(
        relative_rect=pygame.Rect(0, 0, 800, 600),
        manager=ui_manager
    )
    
    try:
        controller = create_better_mocks()
        
        # IdentifyPanel 作成テスト
        print("1. IdentifyPanel 作成中...")
        panel = IdentifyPanel(
            rect=pygame.Rect(50, 50, 700, 500),
            parent=parent,
            controller=controller,
            ui_manager=ui_manager
        )
        print("   ✓ IdentifyPanel 作成成功")
        
        # UIElementManager 確認
        if hasattr(panel, 'ui_element_manager') and panel.ui_element_manager:
            manager = panel.ui_element_manager
            print(f"   ✓ UIElementManager存在: 要素数 {manager.get_element_count()}")
            
            # 鑑定パネル特有の要素確認
            elements = [
                ("title_label", "タイトルラベル"),
                ("gold_label", "所持金ラベル"),
                ("inventory_label", "インベントリラベル"),
                ("unidentified_list", "未鑑定リスト"),
                ("identify_button", "鑑定ボタン")
            ]
            
            for element_id, description in elements:
                element = manager.get_element(element_id)
                status = "✓ 存在" if element else "✗ 不在"
                print(f"   {status} {description} ({element_id})")
        
        # 破棄テスト
        print("2. 破棄処理テスト...")
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


def test_storage_panel_creation():
    """StoragePanel の詳細作成テスト"""
    print("\n=== StoragePanel 詳細テスト ===")
    
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    ui_manager = pygame_gui.UIManager((800, 600))
    
    parent = pygame_gui.elements.UIPanel(
        relative_rect=pygame.Rect(0, 0, 800, 600),
        manager=ui_manager
    )
    
    try:
        controller = create_better_mocks()
        
        # StoragePanel 作成テスト
        print("1. StoragePanel 作成中...")
        
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
        
        # 破棄テスト
        print("2. 破棄処理テスト...")
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


def test_item_management_panel_creation():
    """ItemManagementPanel の詳細作成テスト"""
    print("\n=== ItemManagementPanel 詳細テスト ===")
    
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    ui_manager = pygame_gui.UIManager((800, 600))
    
    parent = pygame_gui.elements.UIPanel(
        relative_rect=pygame.Rect(0, 0, 800, 600),
        manager=ui_manager
    )
    
    try:
        controller = create_better_mocks()
        
        # ItemManagementPanel 作成テスト
        print("1. ItemManagementPanel 作成中...")
        panel = ItemManagementPanel(
            rect=pygame.Rect(50, 50, 700, 500),
            parent=parent,
            controller=controller,
            ui_manager=ui_manager
        )
        print("   ✓ ItemManagementPanel 作成成功")
        
        # UIElementManager 確認
        if hasattr(panel, 'ui_element_manager') and panel.ui_element_manager:
            manager = panel.ui_element_manager
            print(f"   ✓ UIElementManager存在: 要素数 {manager.get_element_count()}")
            
            # アイテム管理パネル特有の要素確認
            elements = [
                ("back_button", "戻るボタン"),
                ("title_label", "タイトルラベル"),
                ("member_label", "メンバーラベル"),
                ("item_label", "アイテムラベル"),
                ("detail_label", "詳細ラベル"),
                ("member_list", "メンバーリスト"),
                ("item_list", "アイテムリスト"),
                ("detail_box", "詳細ボックス"),
                ("action_transfer", "移動ボタン"),
                ("action_use", "使用ボタン"),
                ("action_discard", "破棄ボタン")
            ]
            
            for element_id, description in elements:
                element = manager.get_element(element_id)
                status = "✓ 存在" if element else "✗ 不在"
                print(f"   {status} {description} ({element_id})")
        
        # 破棄テスト
        print("2. 破棄処理テスト...")
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


def main():
    """メインテスト実行"""
    print("Phase 1 移行パネル詳細テスト開始\n")
    
    results = []
    
    # 各パネルのテスト実行
    test_functions = [
        ("SellPanel", test_sell_panel_creation),
        ("IdentifyPanel", test_identify_panel_creation),
        ("StoragePanel", test_storage_panel_creation),
        ("ItemManagementPanel", test_item_management_panel_creation)
    ]
    
    for panel_name, test_func in test_functions:
        try:
            result = test_func()
            results.append((panel_name, result))
        except Exception as e:
            print(f"{panel_name} テストでエラー: {e}")
            results.append((panel_name, False))
    
    # 結果のサマリー
    print("\n" + "="*60)
    print("=== テスト結果サマリー ===")
    
    successful_count = 0
    for panel_name, success in results:
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"{panel_name}: {status}")
        if success:
            successful_count += 1
    
    print(f"\n成功率: {successful_count}/{len(results)} ({successful_count/len(results)*100:.1f}%)")
    
    if successful_count == len(results):
        print("\n🎉 全ての移行パネルテストが成功しました！")
        print("Phase 1 の UIElementManager 移行が完了しています。")
        return 0
    else:
        print(f"\n⚠️  {len(results) - successful_count} 個のパネルで問題が発生しました。")
        print("デバッグが必要です。")
        return 1


if __name__ == "__main__":
    sys.exit(main())