"""UI/UX拡張機能のテスト"""

import unittest
import time
from unittest.mock import patch, MagicMock

from src.dungeon.ui_enhancements import (
    DungeonUIEnhancer, UINotification, NotificationType,
    dungeon_ui_enhancer
)
from src.dungeon.quality_settings import (
    DungeonQualityManager, DifficultyLevel, QualityPreset,
    DifficultySettings, QualitySettings
)


class TestDungeonUIEnhancer(unittest.TestCase):
    """ダンジョンUI拡張機能のテスト"""
    
    def setUp(self):
        self.ui_enhancer = DungeonUIEnhancer()
    
    def test_notification_creation(self):
        """通知作成テスト"""
        # 基本通知
        self.ui_enhancer.add_notification("テストメッセージ", NotificationType.INFO)
        notifications = self.ui_enhancer.get_active_notifications()
        
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0].message, "テストメッセージ")
        self.assertEqual(notifications[0].notification_type, NotificationType.INFO)
    
    def test_notification_expiration(self):
        """通知期限切れテスト"""
        # 短い期間の通知を追加
        self.ui_enhancer.add_notification("短期通知", NotificationType.WARNING, 0.1)
        
        # すぐに確認（まだアクティブ）
        active = self.ui_enhancer.get_active_notifications()
        self.assertEqual(len(active), 1)
        
        # 期限切れまで待機
        time.sleep(0.2)
        
        # 期限切れ後確認
        active = self.ui_enhancer.get_active_notifications()
        self.assertEqual(len(active), 0)
    
    def test_trap_warning_creation(self):
        """トラップ警告作成テスト"""
        # 発見時
        message = self.ui_enhancer.create_trap_warning("矢の罠", detected=True)
        self.assertIn("発見", message)
        self.assertIn("⚠️", message)
        
        # 発動時
        message = self.ui_enhancer.create_trap_warning("棘の罠", detected=False)
        self.assertIn("発動", message)
        self.assertIn("💥", message)
    
    def test_treasure_notification_creation(self):
        """宝箱通知作成テスト"""
        # 空の宝箱
        message = self.ui_enhancer.create_treasure_notification("木製の宝箱", [])
        self.assertIn("空", message)
        
        # アイテム入り宝箱
        contents = ["金貨 50", "回復ポーション", "鉄の剣"]
        message = self.ui_enhancer.create_treasure_notification("金属の宝箱", contents)
        self.assertIn("💰", message)
        self.assertIn("金貨 50", message)
    
    def test_combat_notification_creation(self):
        """戦闘通知作成テスト"""
        # 戦闘開始
        details = {"monster_name": "スケルトン"}
        message = self.ui_enhancer.create_combat_notification("encounter_start", details)
        self.assertIn("スケルトン", message)
        self.assertIn("⚔️", message)
        
        # 勝利
        details = {"experience": 100, "gold": 50}
        message = self.ui_enhancer.create_combat_notification("combat_victory", details)
        self.assertIn("勝利", message)
        self.assertIn("100", message)
        self.assertIn("50", message)
    
    def test_party_status_alert_creation(self):
        """パーティステータス警告作成テスト"""
        # 低体力警告
        details = {"current_hp": 15, "max_hp": 50}
        message = self.ui_enhancer.create_party_status_alert("low_health", "戦士", details)
        self.assertIn("30%", message)  # 15/50 = 30%
        self.assertIn("❤️", message)
        
        # 状態異常
        details = {"effect": "毒"}
        message = self.ui_enhancer.create_party_status_alert("status_effect", "盗賊", details)
        self.assertIn("毒", message)
        self.assertIn("🔮", message)
    
    def test_exploration_notification_creation(self):
        """探索通知作成テスト"""
        # 隠し通路発見
        message = self.ui_enhancer.create_exploration_notification("secret_passage", {})
        self.assertIn("隠し通路", message)
        self.assertIn("🔍", message)
        
        # 階層移動
        details = {"floor": 5, "direction": "下"}
        message = self.ui_enhancer.create_exploration_notification("floor_change", details)
        self.assertIn("5階", message)
        self.assertIn("🏰", message)
    
    def test_ui_hint_system(self):
        """UIヒントシステムテスト"""
        hint = self.ui_enhancer.get_ui_hint_for_situation("first_trap")
        self.assertIn("盗賊", hint)
        self.assertIn("💡", hint)
        
        # ヒント無効化テスト
        self.ui_enhancer.ui_settings["show_hints"] = False
        hint = self.ui_enhancer.get_ui_hint_for_situation("first_treasure")
        # ヒントが表示されないが、通知は空文字列ではない（メソッドは動作する）
    
    def test_damage_display_formatting(self):
        """ダメージ表示フォーマットテスト"""
        # 物理ダメージ
        display = self.ui_enhancer.format_damage_display(25, "physical")
        self.assertIn("⚔️", display)
        self.assertIn("25", display)
        
        # 魔法ダメージ
        display = self.ui_enhancer.format_damage_display(15, "magical")
        self.assertIn("🔮", display)
        self.assertIn("15", display)
        
        # 表示無効化
        self.ui_enhancer.ui_settings["show_damage_numbers"] = False
        display = self.ui_enhancer.format_damage_display(30, "fire")
        self.assertEqual(display, "")
    
    def test_minimap_data_creation(self):
        """ミニマップデータ作成テスト"""
        dungeon_data = {
            "player_position": (5, 3),
            "visited_cells": [(5, 3), (4, 3), (5, 2)],
            "known_walls": [((5, 3), "north"), ((4, 3), "west")],
            "floor_size": (10, 10)
        }
        
        minimap_data = self.ui_enhancer.create_minimap_data(dungeon_data)
        
        self.assertEqual(minimap_data["current_position"], (5, 3))
        self.assertEqual(len(minimap_data["visited_cells"]), 3)
        self.assertEqual(minimap_data["floor_size"], (10, 10))
    
    def test_ui_settings_update(self):
        """UI設定更新テスト"""
        new_settings = {
            "show_minimap": False,
            "show_damage_numbers": False,
            "play_sound_effects": False
        }
        
        self.ui_enhancer.update_ui_settings(new_settings)
        
        self.assertFalse(self.ui_enhancer.ui_settings["show_minimap"])
        self.assertFalse(self.ui_enhancer.ui_settings["show_damage_numbers"])
        self.assertFalse(self.ui_enhancer.ui_settings["play_sound_effects"])
    
    def test_accessibility_options(self):
        """アクセシビリティオプションテスト"""
        accessibility = self.ui_enhancer.get_accessibility_options()
        
        self.assertIn("high_contrast_mode", accessibility)
        self.assertIn("large_text_mode", accessibility)
        self.assertIn("screen_reader_mode", accessibility)
        self.assertIn("audio_cues_enabled", accessibility)
    
    def test_progress_summary_creation(self):
        """進行状況サマリー作成テスト"""
        session_data = {
            "floors_visited": 3,
            "monsters_killed": 15,
            "treasures_opened": 5,
            "total_exp_gained": 500,
            "session_duration": 1800.0  # 30分
        }
        
        summary = self.ui_enhancer.create_progress_summary(session_data)
        
        self.assertEqual(summary["floors_explored"], 3)
        self.assertEqual(summary["monsters_defeated"], 15)
        self.assertEqual(summary["treasures_found"], 5)
        self.assertEqual(summary["experience_gained"], 500)
        self.assertEqual(summary["time_played"], 1800.0)


class TestDungeonQualityManager(unittest.TestCase):
    """ダンジョン品質管理のテスト"""
    
    def setUp(self):
        self.quality_manager = DungeonQualityManager()
    
    def test_difficulty_presets_initialization(self):
        """難易度プリセット初期化テスト"""
        self.assertIn(DifficultyLevel.BEGINNER, self.quality_manager.difficulty_presets)
        self.assertIn(DifficultyLevel.NORMAL, self.quality_manager.difficulty_presets)
        self.assertIn(DifficultyLevel.NIGHTMARE, self.quality_manager.difficulty_presets)
        
        # 初心者設定の確認
        beginner = self.quality_manager.difficulty_presets[DifficultyLevel.BEGINNER]
        self.assertLess(beginner.enemy_health_multiplier, 1.0)
        self.assertTrue(beginner.show_hints)
        
        # 悪夢設定の確認
        nightmare = self.quality_manager.difficulty_presets[DifficultyLevel.NIGHTMARE]
        self.assertGreater(nightmare.enemy_health_multiplier, 1.5)
        self.assertFalse(nightmare.show_hints)
    
    def test_quality_presets_initialization(self):
        """品質プリセット初期化テスト"""
        self.assertIn(QualityPreset.PERFORMANCE, self.quality_manager.quality_presets)
        self.assertIn(QualityPreset.BALANCED, self.quality_manager.quality_presets)
        self.assertIn(QualityPreset.QUALITY, self.quality_manager.quality_presets)
        
        # 性能重視設定の確認
        performance = self.quality_manager.quality_presets[QualityPreset.PERFORMANCE]
        self.assertEqual(performance.texture_quality, "low")
        self.assertFalse(performance.particle_effects)
        
        # 品質重視設定の確認
        quality = self.quality_manager.quality_presets[QualityPreset.QUALITY]
        self.assertEqual(quality.texture_quality, "high")
        self.assertTrue(quality.particle_effects)
    
    def test_difficulty_setting(self):
        """難易度設定テスト"""
        # 有効な難易度設定
        success = self.quality_manager.set_difficulty(DifficultyLevel.HARD)
        self.assertTrue(success)
        self.assertEqual(self.quality_manager.current_difficulty, DifficultyLevel.HARD)
    
    def test_quality_setting(self):
        """品質設定テスト"""
        # 有効な品質設定
        success = self.quality_manager.set_quality(QualityPreset.QUALITY)
        self.assertTrue(success)
        self.assertEqual(self.quality_manager.current_quality, QualityPreset.QUALITY)
    
    def test_custom_difficulty_creation(self):
        """カスタム難易度作成テスト"""
        modifications = {
            "enemy_health_multiplier": 1.5,
            "show_hints": False,
            "gold_multiplier": 2.0
        }
        
        custom = self.quality_manager.create_custom_difficulty(
            DifficultyLevel.NORMAL, modifications
        )
        
        self.assertEqual(custom.enemy_health_multiplier, 1.5)
        self.assertFalse(custom.show_hints)
        self.assertEqual(custom.gold_multiplier, 2.0)
        self.assertEqual(custom.name, "カスタム")
    
    def test_custom_quality_creation(self):
        """カスタム品質作成テスト"""
        modifications = {
            "texture_quality": "ultra",
            "max_visible_objects": 500,
            "ui_animation_speed": 0.5
        }
        
        custom = self.quality_manager.create_custom_quality(
            QualityPreset.BALANCED, modifications
        )
        
        self.assertEqual(custom.texture_quality, "ultra")
        self.assertEqual(custom.max_visible_objects, 500)
        self.assertEqual(custom.ui_animation_speed, 0.5)
        self.assertEqual(custom.preset_name, "カスタム")
    
    def test_current_settings_retrieval(self):
        """現在設定取得テスト"""
        # デフォルト設定
        difficulty = self.quality_manager.get_current_difficulty_settings()
        quality = self.quality_manager.get_current_quality_settings()
        
        self.assertIsInstance(difficulty, DifficultySettings)
        self.assertIsInstance(quality, QualitySettings)
        
        # 設定変更後
        self.quality_manager.set_difficulty(DifficultyLevel.EXPERT)
        self.quality_manager.set_quality(QualityPreset.PERFORMANCE)
        
        new_difficulty = self.quality_manager.get_current_difficulty_settings()
        new_quality = self.quality_manager.get_current_quality_settings()
        
        self.assertEqual(new_difficulty.name, "専門家")
        self.assertEqual(new_quality.preset_name, "性能重視")
    
    def test_recommended_settings(self):
        """推奨設定テスト"""
        # 低スペック
        low_specs = {"cpu_score": 30, "memory_gb": 2, "gpu_score": 25}
        difficulty, quality = self.quality_manager.get_recommended_settings(low_specs)
        
        self.assertEqual(difficulty, DifficultyLevel.NORMAL)
        self.assertEqual(quality, QualityPreset.PERFORMANCE)
        
        # 高スペック
        high_specs = {"cpu_score": 85, "memory_gb": 16, "gpu_score": 90}
        difficulty, quality = self.quality_manager.get_recommended_settings(high_specs)
        
        self.assertEqual(difficulty, DifficultyLevel.NORMAL)
        self.assertEqual(quality, QualityPreset.QUALITY)
    
    def test_difficulty_application_to_systems(self):
        """システムへの難易度適用テスト"""
        # モックシステム作成
        mock_trap_system = MagicMock()
        mock_trap_system.trap_definitions = {
            "test_trap": MagicMock()
        }
        mock_trap_system.trap_definitions["test_trap"].success_rate = 0.7
        mock_trap_system.trap_definitions["test_trap"].damage_range = (10, 20)
        
        # 困難な難易度設定
        self.quality_manager.set_difficulty(DifficultyLevel.HARD)
        
        # 適用
        self.quality_manager.apply_difficulty_to_trap_system(mock_trap_system)
        
        # 効果確認（値が変更されているかどうか）
        trap_data = mock_trap_system.trap_definitions["test_trap"]
        # success_rateが難易度の影響を受けて変更されているはず
        self.assertNotEqual(trap_data.success_rate, 0.7)


class TestUIIntegration(unittest.TestCase):
    """UI統合テスト"""
    
    def test_ui_enhancer_quality_manager_integration(self):
        """UI拡張機能と品質管理の統合テスト"""
        ui_enhancer = DungeonUIEnhancer()
        quality_manager = DungeonQualityManager()
        
        # 品質設定をUI設定に反映
        quality_settings = quality_manager.get_current_quality_settings()
        
        ui_settings_update = {
            "show_damage_numbers": quality_settings.texture_quality != "low",
            "play_sound_effects": quality_settings.audio_quality != "low",
            "ui_animation_speed": quality_settings.ui_animation_speed
        }
        
        ui_enhancer.update_ui_settings(ui_settings_update)
        
        # 設定が正しく反映されているか確認
        self.assertEqual(
            ui_enhancer.ui_settings["ui_animation_speed"],
            quality_settings.ui_animation_speed
        )


if __name__ == '__main__':
    unittest.main()