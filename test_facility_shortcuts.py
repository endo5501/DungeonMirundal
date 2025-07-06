#!/usr/bin/env python3
"""
施設内ショートカットキーの動作確認テスト
"""

import time
from src.debug.game_debug_client import GameDebugClient
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_facility_shortcuts():
    """施設内ショートカットキーの動作を確認"""
    client = GameDebugClient()
    
    # APIが利用可能になるまで待機
    logger.info("APIサーバーが利用可能になるまで待機中...")
    if not client.wait_for_api(max_wait=10.0):
        logger.error("APIサーバーが利用できません")
        return False
    
    logger.info("APIサーバーが利用可能になりました")
    
    # 1. 初期状態の確認（タイトル画面からゲームに入る）
    logger.info("\n=== 1. 初期状態の確認 ===")
    client.screenshot("01_initial.jpg")
    hierarchy = client.get_ui_hierarchy()
    if hierarchy:
        logger.info(f"現在のウィンドウ: {hierarchy.get('window_stack', [])}")
    
    # スペースキーでゲーム開始
    logger.info("スペースキーでゲーム開始...")
    client.press_space()
    time.sleep(2)
    
    # 2. 地上画面の確認
    logger.info("\n=== 2. 地上画面の確認 ===")
    client.screenshot("02_overworld.jpg")
    hierarchy = client.get_ui_hierarchy()
    if hierarchy:
        logger.info(f"現在のウィンドウ: {hierarchy.get('window_stack', [])}")
    
    # 3. 冒険者ギルドに入る（1番キー）
    logger.info("\n=== 3. 冒険者ギルドに入る ===")
    logger.info("1番キーを押して冒険者ギルドに入る...")
    client.press_number_key(1)
    time.sleep(1.5)
    
    client.screenshot("03_guild_main.jpg")
    hierarchy = client.get_ui_hierarchy()
    if hierarchy:
        current_windows = hierarchy.get('window_stack', [])
        logger.info(f"現在のウィンドウ: {current_windows}")
        
        # ギルドに入ったか確認
        in_guild = any('guild' in w.lower() for w in current_windows)
        logger.info(f"ギルド内にいる: {in_guild}")
    
    # 4. 施設内でのショートカットキーテスト
    logger.info("\n=== 4. 施設内ショートカットキーのテスト ===")
    
    # 4-1. 1番：キャラクター作成
    logger.info("\n--- 1番キー: キャラクター作成 ---")
    client.press_number_key(1)
    time.sleep(1.5)
    
    client.screenshot("04_character_creation.jpg")
    hierarchy = client.get_ui_hierarchy()
    if hierarchy:
        current_windows = hierarchy.get('window_stack', [])
        logger.info(f"現在のウィンドウ: {current_windows}")
        
        # キャラクター作成画面に移動したか確認
        in_creation = any('character_creation' in w.lower() or 'creation' in w.lower() for w in current_windows)
        logger.info(f"キャラクター作成画面: {in_creation}")
        
        # 地上画面に戻っていないか確認
        on_overworld = any('overworld' in w.lower() and 'main' in w.lower() for w in current_windows)
        if on_overworld:
            logger.error("❌ エラー: 地上画面に戻ってしまいました！")
        else:
            logger.info("✅ OK: 地上画面には戻っていません")
    
    # ESCで戻る
    logger.info("ESCキーで戻る...")
    client.press_escape()
    time.sleep(1)
    
    # 4-2. 2番：パーティ編成
    logger.info("\n--- 2番キー: パーティ編成 ---")
    client.press_number_key(2)
    time.sleep(1.5)
    
    client.screenshot("05_party_edit.jpg")
    hierarchy = client.get_ui_hierarchy()
    if hierarchy:
        current_windows = hierarchy.get('window_stack', [])
        logger.info(f"現在のウィンドウ: {current_windows}")
        
        # パーティ編成画面に移動したか確認
        in_party = any('party' in w.lower() for w in current_windows)
        logger.info(f"パーティ編成画面: {in_party}")
        
        # 地上画面に戻っていないか確認
        on_overworld = any('overworld' in w.lower() and 'main' in w.lower() for w in current_windows)
        if on_overworld:
            logger.error("❌ エラー: 地上画面に戻ってしまいました！")
        else:
            logger.info("✅ OK: 地上画面には戻っていません")
    
    # ESCで戻る
    logger.info("ESCキーで戻る...")
    client.press_escape()
    time.sleep(1)
    
    # 4-3. 3番：クラス変更
    logger.info("\n--- 3番キー: クラス変更 ---")
    client.press_number_key(3)
    time.sleep(1.5)
    
    client.screenshot("06_class_change.jpg")
    hierarchy = client.get_ui_hierarchy()
    if hierarchy:
        current_windows = hierarchy.get('window_stack', [])
        logger.info(f"現在のウィンドウ: {current_windows}")
        
        # クラス変更画面に移動したか確認
        in_class = any('class' in w.lower() for w in current_windows)
        logger.info(f"クラス変更画面: {in_class}")
        
        # 地上画面に戻っていないか確認
        on_overworld = any('overworld' in w.lower() and 'main' in w.lower() for w in current_windows)
        if on_overworld:
            logger.error("❌ エラー: 地上画面に戻ってしまいました！")
        else:
            logger.info("✅ OK: 地上画面には戻っていません")
    
    # ESCで戻る
    logger.info("ESCキーで戻る...")
    client.press_escape()
    time.sleep(1)
    
    # 4-4. 4番：冒険者一覧
    logger.info("\n--- 4番キー: 冒険者一覧 ---")
    client.press_number_key(4)
    time.sleep(1.5)
    
    client.screenshot("07_adventurer_list.jpg")
    hierarchy = client.get_ui_hierarchy()
    if hierarchy:
        current_windows = hierarchy.get('window_stack', [])
        logger.info(f"現在のウィンドウ: {current_windows}")
        
        # 冒険者一覧画面に移動したか確認
        in_list = any('list' in w.lower() or 'adventurer' in w.lower() for w in current_windows)
        logger.info(f"冒険者一覧画面: {in_list}")
        
        # 地上画面に戻っていないか確認
        on_overworld = any('overworld' in w.lower() and 'main' in w.lower() for w in current_windows)
        if on_overworld:
            logger.error("❌ エラー: 地上画面に戻ってしまいました！")
        else:
            logger.info("✅ OK: 地上画面には戻っていません")
    
    # ESCで戻る
    logger.info("ESCキーで戻る...")
    client.press_escape()
    time.sleep(1)
    
    # 5. ESCキーで退出できることを確認
    logger.info("\n=== 5. ESCキーで退出確認 ===")
    client.screenshot("08_back_to_guild.jpg")
    
    logger.info("ESCキーでギルドから退出...")
    client.press_escape()
    time.sleep(1.5)
    
    client.screenshot("09_back_to_overworld.jpg")
    hierarchy = client.get_ui_hierarchy()
    if hierarchy:
        current_windows = hierarchy.get('window_stack', [])
        logger.info(f"現在のウィンドウ: {current_windows}")
        
        # 地上画面に戻ったか確認
        on_overworld = any('overworld' in w.lower() and 'main' in w.lower() for w in current_windows)
        if on_overworld:
            logger.info("✅ OK: 地上画面に戻りました")
        else:
            logger.error("❌ エラー: 地上画面に戻れませんでした")
    
    logger.info("\n=== テスト完了 ===")
    return True

if __name__ == "__main__":
    test_facility_shortcuts()