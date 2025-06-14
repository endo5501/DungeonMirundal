"""Dungeon RPG メインエントリーポイント"""

import sys
import os

# プロジェクトルートをPythonパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.core.game_manager import create_game
from src.utils.logger import logger


def main():
    """メイン関数"""
    try:
        logger.info("=== Dungeon RPG 起動 ===")
        
        # ゲームインスタンスの作成と実行
        game = create_game()
        game.run_game()
        
    except KeyboardInterrupt:
        logger.info("ユーザーによってゲームが中断されました")
    except Exception as e:
        logger.error(f"ゲーム実行中にエラーが発生しました: {e}")
        raise
    finally:
        logger.info("=== Dungeon RPG 終了 ===")


if __name__ == "__main__":
    main()
