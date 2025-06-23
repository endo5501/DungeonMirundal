#!/usr/bin/env python
"""UISelectionList修正確認テスト"""

import pygame
import sys

# プロジェクトパスを追加
sys.path.append('/home/satorue/Dungeon')

from src.ui.base_ui_pygame import initialize_ui_manager
from src.overworld.overworld_manager_pygame import OverworldManager
from src.character.party import Party
from src.character.character import Character


def test_dungeon_selection():
    """ダンジョン選択画面のテスト"""
    
    # Pygame初期化
    pygame.init()
    
    # 画面設定
    screen_width = 800
    screen_height = 600
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("ダンジョン選択 修正テスト")
    
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
    
    # OverworldManager作成
    overworld_manager = OverworldManager()
    overworld_manager.set_ui_manager(ui_manager)
    overworld_manager.current_party = test_party
    overworld_manager.is_active = True
    
    # ダンジョン選択画面を表示
    try:
        overworld_manager._show_dungeon_selection_menu()
        print("✓ ダンジョン選択画面が正常に作成されました")
    except Exception as e:
        print(f"✗ ダンジョン選択画面作成エラー: {e}")
        assert False, f"ダンジョン選択画面作成エラー: {e}"
    
    # 描画・イベント処理テスト
    clock = pygame.time.Clock()
    for i in range(180):  # 3秒間テスト
        time_delta = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                break
            
            # イベント処理
            ui_manager.handle_event(event)
            overworld_manager.handle_event(event)
        
        # 更新
        ui_manager.update(time_delta)
        
        # 描画
        screen.fill((30, 30, 30))
        ui_manager.render()
        
        pygame.display.flip()
    
    print("✓ 描画・イベント処理テストが正常に完了しました")
    
    # クリーンアップ
    if overworld_manager.dungeon_selection_list:
        overworld_manager.dungeon_selection_list.kill()
    pygame.quit()
    
    # テスト成功
    assert True


def main():
    """メイン関数"""
    print("=== UISelectionList修正確認テスト ===")
    
    success = test_dungeon_selection()
    
    if success:
        print("\n✅ 全てのテストが成功しました")
        return 0
    else:
        print("\n❌ テストが失敗しました")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)