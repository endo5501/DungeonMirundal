#!/usr/bin/env python3
"""
段階的3D描画復旧テストスクリプト

このスクリプトはDungeonRendererの段階的復旧機能をテストします。
"""

import sys
import time
from unittest.mock import Mock, MagicMock

# Panda3Dモジュールをモック化（テスト環境用）
sys.modules['direct.showbase.ShowBase'] = Mock()
sys.modules['direct.actor.Actor'] = Mock()
sys.modules['panda3d.core'] = Mock()
sys.modules['direct.gui.OnscreenText'] = Mock()
sys.modules['direct.task'] = Mock()
sys.modules['direct.gui.DirectGui'] = Mock()

# 必要なモジュールをインポート
from src.rendering.dungeon_renderer import DungeonRenderer
from src.utils.logger import logger

def create_mock_showbase():
    """テスト用のShowBaseモックを作成"""
    mock_showbase = Mock()
    
    # 基本属性
    mock_showbase.render = Mock()
    mock_showbase.camera = Mock()
    mock_showbase.cam = Mock()
    mock_showbase.win = Mock()
    mock_showbase.taskMgr = Mock()
    mock_showbase.loader = Mock()
    mock_showbase.setBackgroundColor = Mock()
    mock_showbase.graphicsEngine = Mock()
    
    # カメラの詳細設定
    mock_showbase.camera.setPos = Mock()
    mock_showbase.camera.setHpr = Mock()
    mock_showbase.camera.getPos = Mock(return_value=Mock(x=0, y=0, z=1.7))
    mock_showbase.camera.getHpr = Mock(return_value=Mock(x=0, y=0, z=0))
    
    # レンズの設定
    mock_lens = Mock()
    mock_lens.setFov = Mock()
    mock_lens.setNear = Mock()
    mock_lens.setFar = Mock()
    mock_lens.getNear = Mock(return_value=0.1)
    mock_lens.getFar = Mock(return_value=20)
    
    mock_cam_node = Mock()
    mock_cam_node.getLens = Mock(return_value=mock_lens)
    mock_cam_node.setCameraMask = Mock()
    mock_showbase.cam.node = Mock(return_value=mock_cam_node)
    
    return mock_showbase

def test_stage_advancement():
    """段階的3D描画復旧のテスト"""
    print("=== 段階的3D描画復旧テスト開始 ===")
    
    # ShowBaseモックを作成
    mock_showbase = create_mock_showbase()
    
    # DungeonRendererを初期化
    print("\\n1. DungeonRenderer初期化...")
    renderer = DungeonRenderer(show_base_instance=mock_showbase)
    
    # 初期状態を確認
    initial_info = renderer.get_stage_info()
    print(f"初期段階: {initial_info['current_stage']}")
    print(f"有効機能: {initial_info['enabled_features']}")
    print(f"エラー: {initial_info['has_errors']}")
    
    if initial_info['has_errors']:
        print(f"初期化エラー: {initial_info['errors']}")
        return False
    
    # Stage 1-Aに進行
    print("\\n2. Stage 1-A (最小限Panda3D接続テスト) への進行...")
    success = renderer.advance_to_stage("stage1a")
    
    if success:
        print("✓ Stage 1-A進行成功")
        stage1a_info = renderer.get_stage_info()
        print(f"現在段階: {stage1a_info['current_stage']}")
        print(f"有効機能: {stage1a_info['enabled_features']}")
    else:
        print("✗ Stage 1-A進行失敗")
        return False
    
    # Stage 1-Bに進行
    print("\\n3. Stage 1-B (単一床面描画) への進行...")
    success = renderer.advance_to_stage("stage1b")
    
    if success:
        print("✓ Stage 1-B進行成功")
        stage1b_info = renderer.get_stage_info()
        print(f"現在段階: {stage1b_info['current_stage']}")
        print(f"有効機能: {stage1b_info['enabled_features']}")
        print(f"ノード数: {stage1b_info['node_counts']}")
    else:
        print("✗ Stage 1-B進行失敗")
        return False
    
    # Stage 2-Aに進行
    print("\\n4. Stage 2-A (壁面描画) への進行...")
    success = renderer.advance_to_stage("stage2a")
    
    if success:
        print("✓ Stage 2-A進行成功")
        stage2a_info = renderer.get_stage_info()
        print(f"現在段階: {stage2a_info['current_stage']}")
        print(f"有効機能: {stage2a_info['enabled_features']}")
        print(f"ノード数: {stage2a_info['node_counts']}")
    else:
        print("✗ Stage 2-A進行失敗")
        return False
    
    # Stage 2-Bに進行
    print("\\n5. Stage 2-B (ライティングと天井) への進行...")
    success = renderer.advance_to_stage("stage2b")
    
    if success:
        print("✓ Stage 2-B進行成功")
        stage2b_info = renderer.get_stage_info()
        print(f"現在段階: {stage2b_info['current_stage']}")
        print(f"有効機能: {stage2b_info['enabled_features']}")
        print(f"ノード数: {stage2b_info['node_counts']}")
    else:
        print("✗ Stage 2-B進行失敗")
        return False
    
    # Stage 3（完全復旧）に進行
    print("\\n6. Stage 3 (完全機能復旧) への進行...")
    success = renderer.advance_to_stage("stage3")
    
    if success:
        print("✓ Stage 3進行成功")
        stage3_info = renderer.get_stage_info()
        print(f"現在段階: {stage3_info['current_stage']}")
        print(f"有効機能: {stage3_info['enabled_features']}")
        print(f"enabledフラグ: {stage3_info['enabled_flag']}")
        print(f"ノード数: {stage3_info['node_counts']}")
    else:
        print("✗ Stage 3進行失敗")
        return False
    
    print("\\n=== 全段階テスト完了 ===")
    return True

def test_rollback_functionality():
    """ロールバック機能のテスト"""
    print("\\n=== ロールバック機能テスト ===")
    
    mock_showbase = create_mock_showbase()
    renderer = DungeonRenderer(show_base_instance=mock_showbase)
    
    # Stage 1-Bまで進行
    renderer.advance_to_stage("stage1a")
    renderer.advance_to_stage("stage1b")
    
    print(f"Stage 1-B進行後ノード数: {len(renderer.floor_nodes)}")
    
    # 緊急無効化をテスト
    print("緊急無効化を実行...")
    renderer.emergency_disable()
    
    final_info = renderer.get_stage_info()
    print(f"緊急無効化後段階: {final_info['current_stage']}")
    print(f"ノード数: {final_info['node_counts']}")
    
    if final_info['current_stage'] == 'disabled' and sum(final_info['node_counts'].values()) == 0:
        print("✓ 緊急無効化成功")
        return True
    else:
        print("✗ 緊急無効化失敗")
        return False

if __name__ == "__main__":
    print("段階的3D描画復旧システムテスト")
    print("================================")
    
    try:
        # 基本的な段階進行テスト
        success1 = test_stage_advancement()
        
        # ロールバック機能テスト
        success2 = test_rollback_functionality()
        
        if success1 and success2:
            print("\\n🎉 すべてのテストが成功しました！")
            print("段階的3D描画復旧システムは正常に動作しています。")
        else:
            print("\\n❌ 一部のテストが失敗しました。")
            
    except Exception as e:
        print(f"\\n💥 テスト中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()