#!/usr/bin/env python3
"""
簡単なテスト：施設内で1番キーを押した時の挙動を確認
"""

import time
from src.debug.game_debug_client import GameDebugClient
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def simple_test():
    """簡単なテスト"""
    client = GameDebugClient()
    
    # APIが利用可能になるまで待機
    if not client.wait_for_api(max_wait=10.0):
        logger.error("APIサーバーが利用できません")
        return False
    
    logger.info("ゲームスタート...")
    client.press_space()
    time.sleep(2)
    
    logger.info("1. 冒険者ギルドに入る")
    client.press_number_key(1)
    time.sleep(1.5)
    
    # UI階層確認
    hierarchy = client.get_ui_hierarchy()
    if hierarchy:
        logger.info(f"現在のウィンドウ: {hierarchy.get('window_stack', [])}")
    
    logger.info("2. 施設内で1番キーを押す")
    client.press_number_key(1)
    time.sleep(1.5)
    
    # UI階層確認
    hierarchy = client.get_ui_hierarchy()
    if hierarchy:
        logger.info(f"1番キー後のウィンドウ: {hierarchy.get('window_stack', [])}")
    
    logger.info("テスト完了")

if __name__ == "__main__":
    simple_test()