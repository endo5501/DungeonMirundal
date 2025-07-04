"""Dungeon RPG メインエントリーポイント"""

import sys
import os

# プロジェクトルートをPythonパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.core.game_manager import create_game
from src.core.config_manager import config_manager
from src.utils.logger import logger

# グローバル変数（デバッグAPI用）
game_manager = None

def main():
    """メイン関数"""
    global game_manager
    try:
        logger.info(config_manager.get_text("app_log.startup"))
        
        # ゲームインスタンスの作成と実行
        game_manager = create_game()
        game_manager.run_game()
        
    except KeyboardInterrupt:
        logger.info(config_manager.get_text("app_log.user_interrupt"))
    except Exception as e:
        logger.error(f"{config_manager.get_text('app_log.error_occurred')}: {e}")
        raise
    finally:
        logger.info(config_manager.get_text("app_log.shutdown"))


if __name__ == "__main__":
    main()
