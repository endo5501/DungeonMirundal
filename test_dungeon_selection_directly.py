#!/usr/bin/env python3
"""ダンジョン選択UIを直接テストするスクリプト"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame
from src.ui.dungeon_selection_ui import DungeonSelectionUI
from src.character.party import Party
from src.character.character import Character
from src.character.classes import CharacterClass
from src.character.races import CharacterRace
import time

def create_test_party():
    """テスト用のパーティを作成"""
    # テスト用キャラクターを作成
    char = Character(
        name="テストキャラ",
        race=CharacterRace.HUMAN,
        character_class=CharacterClass.FIGHTER
    )
    
    # テスト用パーティを作成
    party = Party("テストパーティ")
    party.add_character(char)
    
    return party

def test_dungeon_selection_ui():
    """ダンジョン選択UIの直接テスト"""
    # Pygame初期化
    pygame.init()
    screen = pygame.display.set_mode((1024, 768))
    pygame.display.set_caption("ダンジョン選択UIテスト")
    clock = pygame.time.Clock()
    
    # UI初期化
    ui_manager = pygame_gui.UIManager((1024, 768))
    
    # ダンジョン選択UI作成
    dungeon_ui = DungeonSelectionUI()
    test_party = create_test_party()
    
    # コールバック関数
    def on_dungeon_selected(dungeon_id):
        print(f"ダンジョンが選択されました: {dungeon_id}")
        
    def on_cancelled():
        print("ダンジョン選択がキャンセルされました")
    
    print("ダンジョン選択UIを表示します...")
    dungeon_ui.show_dungeon_selection(test_party, on_dungeon_selected, on_cancelled)
    
    # メインループ
    running = True
    test_duration = 30  # 30秒間テスト
    start_time = time.time()
    
    print("テスト開始：")
    print("1. [新規作成]ボタンをクリックしてダンジョンを作成")
    print("2. 複数回[新規作成]ボタンをクリック")
    print("3. [選択]ボタンと[削除]ボタンが有効になるか確認")
    print("4. ESCキーまたは[街に戻る]ボタンで終了")
    
    while running:
        time_delta = clock.tick(60) / 1000.0
        
        # 時間制限チェック
        if time.time() - start_time > test_duration:
            print(f"テスト時間制限（{test_duration}秒）に達しました")
            break
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            
            # ダンジョン選択UIのイベント処理
            handled = dungeon_ui.handle_event(event)
            if not handled:
                ui_manager.process_events(event)
        
        # UI更新
        ui_manager.update(time_delta)
        
        # 描画
        screen.fill((0, 0, 0))
        ui_manager.draw_ui(screen)
        pygame.display.flip()
    
    # 結果レポート
    print("\\nテスト結果：")
    print(f"作成されたダンジョン数: {len(dungeon_ui.dungeons)}")
    for i, dungeon in enumerate(dungeon_ui.dungeons):
        print(f"  {i+1}. ハッシュ={dungeon.hash_value[:8]}..., 難易度={dungeon.difficulty}, 階数={dungeon.floors}")
    
    pygame.quit()

if __name__ == "__main__":
    # pygame_guiをインポート
    try:
        import pygame_gui
        test_dungeon_selection_ui()
    except ImportError:
        print("pygame_guiがインストールされていません")
        print("uv add pygame_gui でインストールしてください")