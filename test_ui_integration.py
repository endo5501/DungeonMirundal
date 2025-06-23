#!/usr/bin/env python
"""UISelectionList の統合テスト"""

import pygame
import sys

# プロジェクトパスを追加
sys.path.append('/home/satorue/Dungeon')

from src.ui.base_ui_pygame import initialize_ui_manager
from src.overworld.facilities.shop import Shop
from src.character.party import Party
from src.character.character import Character


def test_shop_integration():
    """商店システムとUISelectionListの統合テスト"""
    
    # Pygame初期化
    pygame.init()
    
    # 画面設定
    screen_width = 800
    screen_height = 600
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Shop UISelectionList 統合テスト")
    
    # UIマネージャー初期化
    ui_manager = initialize_ui_manager(screen)
    
    # グローバルui_managerを設定
    import src.ui.base_ui_pygame
    src.ui.base_ui_pygame.ui_manager = ui_manager
    
    # テスト用パーティ作成
    test_party = Party("テストパーティ")
    test_character = Character(
        character_id="test_char_1",
        name="テストキャラ1",
        character_class="戦士",
        race="人間"
    )
    test_party.add_character(test_character)
    test_party.gold = 1000
    
    # 商店作成
    shop = Shop()
    shop.current_party = test_party
    
    # UIマネージャーをFacilityManagerに設定
    from src.overworld.base_facility import facility_manager
    facility_manager.set_ui_manager(ui_manager)
    
    # Shopのメニューシステムを初期化
    shop.initialize_menu_system(ui_manager)
    
    # 商店に入る
    try:
        shop.enter(test_party)
        print("✓ 商店への入場が正常に実行されました")
    except Exception as e:
        print(f"✗ 商店入場エラー: {e}")
        assert False, f"商店入場エラー: {e}"
    
    # 購入メニューを表示（UISelectionList使用）
    try:
        # 一時的にshop内のui_managerを直接設定してテスト
        import src.overworld.facilities.shop as shop_module
        shop_module.ui_manager = ui_manager
        
        shop._show_buy_menu()
        print("✓ 購入メニュー（UISelectionList）が正常に作成されました")
    except Exception as e:
        print(f"✗ 購入メニュー作成エラー: {e}")
        assert False, f"購入メニュー作成エラー: {e}"
    
    # 簡単な描画テスト
    clock = pygame.time.Clock()
    for i in range(60):  # 1秒間テスト
        time_delta = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                break
            ui_manager.handle_event(event)
        
        ui_manager.update(time_delta)
        
        screen.fill((30, 30, 30))
        ui_manager.render()
        
        pygame.display.flip()
    
    print("✓ 描画テストが正常に完了しました")
    
    # クリーンアップ
    shop._cleanup_all_ui()
    pygame.quit()
    
    # テスト成功
    assert True


def main():
    """メイン関数"""
    print("=== Shop UISelectionList 統合テスト ===")
    
    success = test_shop_integration()
    
    if success:
        print("\n✅ 全てのテストが成功しました")
        return 0
    else:
        print("\n❌ テストが失敗しました")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)