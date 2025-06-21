#!/usr/bin/env python3
"""ダンジョン遷移と疑似3D描画のテスト"""

import pygame
import sys
from src.utils.logger import logger
from src.core.game_manager import create_game

def test_dungeon_transition():
    """ダンジョン遷移と疑似3D描画のテスト"""
    logger.info("ダンジョン遷移テスト開始")
    
    try:
        # ゲームインスタンスを作成
        game = create_game()
        
        # テスト用パーティを確実に作成
        if not game.current_party:
            game._create_test_party()
        
        # 地上部に遷移
        game.transition_to_overworld()
        
        # ダンジョンに遷移
        logger.info("ダンジョンへの遷移をテストします")
        try:
            game.transition_to_dungeon("main_dungeon")
            logger.info("ダンジョン遷移成功")
            
            # 簡単な描画テスト
            if game.dungeon_renderer and game.dungeon_manager.current_dungeon:
                logger.info("疑似3D描画をテストします")
                
                # 画面を作成
                test_screen = pygame.Surface((800, 600))
                
                # ダンジョンビューを描画
                player_pos = game.dungeon_manager.current_dungeon.player_position
                dungeon_level = game.dungeon_manager.current_dungeon.level
                
                game.dungeon_renderer.render_dungeon_view(player_pos, dungeon_level)
                logger.info("疑似3D描画テスト成功")
                
                # 移動テスト
                logger.info("移動テストを実行")
                original_x = player_pos.x
                original_y = player_pos.y
                
                # 前進テスト
                game.dungeon_renderer._move_forward()
                new_pos = game.dungeon_manager.current_dungeon.player_position
                logger.info(f"前進テスト: ({original_x}, {original_y}) -> ({new_pos.x}, {new_pos.y})")
                
                # 回転テスト
                original_direction = new_pos.direction
                game.dungeon_renderer._turn_right()
                new_direction = game.dungeon_manager.current_dungeon.player_position.direction
                logger.info(f"回転テスト: {original_direction} -> {new_direction}")
                
            else:
                logger.warning("ダンジョンレンダラーまたはダンジョンが初期化されていません")
            
        except Exception as e:
            logger.error(f"ダンジョン遷移エラー: {e}")
            return False
        
        # 地上部に戻る
        logger.info("地上部への遷移をテストします")
        try:
            game.transition_to_overworld()
            logger.info("地上部遷移成功")
        except Exception as e:
            logger.error(f"地上部遷移エラー: {e}")
            return False
        
        # クリーンアップ
        game.cleanup()
        pygame.quit()
        
        logger.info("ダンジョン遷移テスト完了")
        return True
        
    except Exception as e:
        logger.error(f"テスト中にエラーが発生: {e}")
        return False

if __name__ == "__main__":
    success = test_dungeon_transition()
    if success:
        print("✅ ダンジョン遷移テスト成功")
    else:
        print("❌ ダンジョン遷移テスト失敗")