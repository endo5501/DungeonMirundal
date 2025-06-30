#!/usr/bin/env python3
"""
CharacterStatusBar WindowSystem統合テスト

実際のゲーム環境に近い状況でCharacterStatusBarがWindowSystemで
正しく表示されるかをテストします。
"""

import pygame
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.character.character import Character
from src.character.party import Party
from src.ui.character_status_bar import CharacterStatusBar
from src.overworld.overworld_manager_pygame import OverworldManager
from src.ui.window_system.window_manager import WindowManager
from src.utils.logger import logger


def create_test_character(name: str, char_id: str) -> Character:
    """テスト用キャラクターを作成"""
    character = Character()
    character.name = name
    character.character_id = char_id
    character.derived_stats.current_hp = 75
    character.derived_stats.max_hp = 100
    return character


def create_test_party() -> Party:
    """テスト用パーティを作成"""
    party = Party()
    party.name = "統合テストパーティ"
    
    # 3人のキャラクターを追加
    char1 = create_test_character("勇者", "hero_1")
    char2 = create_test_character("賢者", "sage_1")
    char3 = create_test_character("戦士", "warrior_1")
    
    party.add_character(char1)
    party.add_character(char2)
    party.add_character(char3)
    
    return party


def test_character_status_bar_windowsystem_integration():
    """CharacterStatusBarとWindowSystemの統合テスト"""
    logger.info("=== CharacterStatusBar WindowSystem統合テスト開始 ===")
    
    try:
        # Pygame初期化
        pygame.init()
        pygame.font.init()
        screen = pygame.display.set_mode((1024, 768))
        pygame.display.set_caption("CharacterStatusBar WindowSystem Integration Test")
        clock = pygame.time.Clock()
        
        # テストパーティ作成
        test_party = create_test_party()
        logger.info(f"テストパーティ作成: {test_party.name}, メンバー数: {len(test_party.characters)}")
        
        # UIManagerのモック
        class TestUIManager:
            def __init__(self):
                self.persistent_elements = {}
                self.default_font = pygame.font.Font(None, 24)
                
            def add_persistent_element(self, element):
                element_id = f"element_{len(self.persistent_elements)}"
                self.persistent_elements[element_id] = element
                logger.info(f"永続要素追加: {type(element).__name__}")
                
        mock_ui_manager = TestUIManager()
        
        # OverworldManager初期化
        overworld_manager = OverworldManager()
        overworld_manager.set_ui_manager(mock_ui_manager)
        
        # WindowManager初期化
        window_manager = WindowManager.get_instance()
        window_manager.initialize_pygame(screen, clock)
        
        logger.info("システム初期化完了")
        logger.info(f"OverworldManager character_status_bar: {overworld_manager.character_status_bar}")
        logger.info(f"UIManager永続要素数: {len(mock_ui_manager.persistent_elements)}")
        
        # パーティ設定
        logger.info("パーティ設定...")
        overworld_manager.set_party(test_party)
        
        # CharacterStatusBarの状態確認
        if overworld_manager.character_status_bar:
            status_bar = overworld_manager.character_status_bar
            logger.info("CharacterStatusBar状態:")
            logger.info(f"  - party: {status_bar.party is not None}")
            logger.info(f"  - party名: {status_bar.party.name if status_bar.party else 'None'}")
            logger.info(f"  - キャラクター数: {len(status_bar.party.characters) if status_bar.party else 0}")
        
        # GameManagerをモック（WindowManagerの永続要素描画のため）
        class MockGameManager:
            def __init__(self, ui_manager):
                self.ui_manager = ui_manager
                
            @classmethod
            def get_instance(cls):
                return test_game_manager
        
        test_game_manager = MockGameManager(mock_ui_manager)
        
        # GameManagerをモック
        import src.ui.window_system.window_manager as wm_module
        original_import = wm_module.GameManager
        wm_module.GameManager = MockGameManager
        
        try:
            # 10秒間の描画テスト
            logger.info("\n10秒間の描画テストを開始します。")
            logger.info("CharacterStatusBarが画面下部に表示されることを確認してください。")
            logger.info("表示される情報:")
            for char_id, char in test_party.characters.items():
                logger.info(f"  - {char.name}: HP {char.derived_stats.current_hp}/{char.derived_stats.max_hp}")
            
            start_time = pygame.time.get_ticks()
            
            while pygame.time.get_ticks() - start_time < 10000:  # 10秒間
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return
                
                # 画面クリア
                screen.fill((50, 50, 50))  # ダークグレー背景
                
                # テスト情報表示
                font = pygame.font.Font(None, 36)
                text_lines = [
                    "CharacterStatusBar WindowSystem統合テスト",
                    "",
                    "下部にキャラクターステータスバーが表示されているかご確認ください",
                    "",
                    f"パーティ: {test_party.name}",
                    f"メンバー数: {len(test_party.characters)}人"
                ]
                
                for i, line in enumerate(text_lines):
                    if line:  # 空行でない場合のみ描画
                        text_surface = font.render(line, True, (255, 255, 255))
                        screen.blit(text_surface, (50, 50 + i * 40))
                
                # WindowManagerで描画（この中でCharacterStatusBarも描画される）
                try:
                    window_manager.draw(screen)
                    logger.debug("WindowManager描画成功")
                except Exception as e:
                    logger.error(f"WindowManager描画エラー: {e}")
                
                # 画面更新
                pygame.display.flip()
                clock.tick(60)
            
            logger.info("描画テスト完了")
            
        finally:
            # GameManagerを元に戻す
            wm_module.GameManager = original_import
        
    except Exception as e:
        logger.error(f"統合テスト実行中エラー: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # WindowManagerクリーンアップ
        if WindowManager._instance:
            WindowManager._instance.shutdown()
        pygame.quit()
        logger.info("=== 統合テスト終了 ===")


if __name__ == "__main__":
    test_character_status_bar_windowsystem_integration()