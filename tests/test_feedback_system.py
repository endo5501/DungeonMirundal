"""フィードバックシステムのテスト"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time

from src.ui.feedback_system import (
    FeedbackSystem, Notification, NotificationType, FeedbackLevel,
    show_info, show_success, show_warning, show_error, show_achievement
)


class TestNotification:
    """通知クラスのテスト"""
    
    def test_notification_initialization(self):
        """通知の初期化テスト"""
        message = "テストメッセージ"
        notification_type = NotificationType.INFO
        duration = 5.0
        
        notification = Notification(message, notification_type, duration)
        
        assert notification.message == message
        assert notification.type == notification_type
        assert notification.duration == duration
        assert notification.persistent == False
        assert notification.ui_element is None
        assert notification.created_at > 0
    
    def test_notification_persistent(self):
        """永続通知のテスト"""
        notification = Notification("永続メッセージ", NotificationType.ERROR, persistent=True)
        
        assert notification.persistent == True
        assert notification.is_expired() == False
    
    def test_notification_expiration(self):
        """通知の有効期限テスト"""
        notification = Notification("期限付きメッセージ", NotificationType.INFO, duration=0.1)
        
        # 作成直後は有効
        assert notification.is_expired() == False
        
        # 少し待つ
        time.sleep(0.15)
        
        # 期限切れになる
        assert notification.is_expired() == True


class TestFeedbackSystem:
    """フィードバックシステムのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        # モックを使用してPanda3D依存を回避
        with patch('src.ui.feedback_system.DirectFrame'), \
             patch('src.ui.feedback_system.DirectLabel'), \
             patch('src.ui.feedback_system.base'):
            self.feedback_system = FeedbackSystem()
    
    def test_feedback_system_initialization(self):
        """フィードバックシステムの初期化テスト"""
        assert self.feedback_system.feedback_level == FeedbackLevel.NORMAL
        assert self.feedback_system.show_achievements == True
        assert self.feedback_system.auto_dismiss == True
        assert self.feedback_system.max_notifications == 5
        assert len(self.feedback_system.active_notifications) == 0
        assert len(self.feedback_system.notification_queue) == 0
    
    def test_notification_type_colors(self):
        """通知タイプの色設定テスト"""
        colors = self.feedback_system.type_colors
        
        # 全ての通知タイプに色が定義されていることを確認
        for notification_type in NotificationType:
            assert notification_type in colors
            color = colors[notification_type]
            assert len(color) == 4  # RGBA
            assert all(0 <= component <= 1 for component in color)
    
    def test_type_icon_mapping(self):
        """通知タイプアイコンマッピングのテスト"""
        assert self.feedback_system._get_type_icon(NotificationType.INFO) == "ℹ"
        assert self.feedback_system._get_type_icon(NotificationType.SUCCESS) == "✓"
        assert self.feedback_system._get_type_icon(NotificationType.WARNING) == "⚠"
        assert self.feedback_system._get_type_icon(NotificationType.ERROR) == "✗"
        assert self.feedback_system._get_type_icon(NotificationType.ACHIEVEMENT) == "★"
    
    def test_feedback_level_filtering_silent(self):
        """サイレントレベルでのフィルタリングテスト"""
        self.feedback_system.set_feedback_level(FeedbackLevel.SILENT)
        
        # どの通知も表示されない
        assert not self.feedback_system._should_show_notification(
            Notification("info", NotificationType.INFO))
        assert not self.feedback_system._should_show_notification(
            Notification("error", NotificationType.ERROR))
        assert not self.feedback_system._should_show_notification(
            Notification("achievement", NotificationType.ACHIEVEMENT))
    
    def test_feedback_level_filtering_minimal(self):
        """最小限レベルでのフィルタリングテスト"""
        self.feedback_system.set_feedback_level(FeedbackLevel.MINIMAL)
        
        # エラーと実績のみ表示
        assert not self.feedback_system._should_show_notification(
            Notification("info", NotificationType.INFO))
        assert not self.feedback_system._should_show_notification(
            Notification("success", NotificationType.SUCCESS))
        assert not self.feedback_system._should_show_notification(
            Notification("warning", NotificationType.WARNING))
        assert self.feedback_system._should_show_notification(
            Notification("error", NotificationType.ERROR))
        assert self.feedback_system._should_show_notification(
            Notification("achievement", NotificationType.ACHIEVEMENT))
    
    def test_feedback_level_filtering_normal(self):
        """通常レベルでのフィルタリングテスト"""
        self.feedback_system.set_feedback_level(FeedbackLevel.NORMAL)
        
        # 情報以外は表示、永続情報は表示
        assert not self.feedback_system._should_show_notification(
            Notification("info", NotificationType.INFO))
        assert self.feedback_system._should_show_notification(
            Notification("info", NotificationType.INFO, persistent=True))
        assert self.feedback_system._should_show_notification(
            Notification("success", NotificationType.SUCCESS))
        assert self.feedback_system._should_show_notification(
            Notification("warning", NotificationType.WARNING))
        assert self.feedback_system._should_show_notification(
            Notification("error", NotificationType.ERROR))
        assert self.feedback_system._should_show_notification(
            Notification("achievement", NotificationType.ACHIEVEMENT))
    
    def test_feedback_level_filtering_verbose(self):
        """詳細レベルでのフィルタリングテスト"""
        self.feedback_system.set_feedback_level(FeedbackLevel.VERBOSE)
        
        # すべての通知が表示される
        assert self.feedback_system._should_show_notification(
            Notification("info", NotificationType.INFO))
        assert self.feedback_system._should_show_notification(
            Notification("success", NotificationType.SUCCESS))
        assert self.feedback_system._should_show_notification(
            Notification("warning", NotificationType.WARNING))
        assert self.feedback_system._should_show_notification(
            Notification("error", NotificationType.ERROR))
        assert self.feedback_system._should_show_notification(
            Notification("achievement", NotificationType.ACHIEVEMENT))
    
    def test_notification_queue_management(self):
        """通知キュー管理のテスト"""
        # 最大通知数を超えるとキューに追加される
        self.feedback_system.max_notifications = 2
        
        # アクティブ通知を最大数まで追加
        for i in range(2):
            notification = Notification(f"アクティブ{i}", NotificationType.INFO)
            self.feedback_system.active_notifications.append(notification)
        
        # 新しい通知はキューに追加される
        self.feedback_system.show_notification("キュー通知", NotificationType.INFO)
        assert len(self.feedback_system.notification_queue) == 1
    
    def test_notification_removal(self):
        """通知削除のテスト"""
        # テスト通知を追加
        notification = Notification("削除テスト", NotificationType.INFO)
        self.feedback_system.active_notifications.append(notification)
        
        # 削除
        self.feedback_system._remove_notification(notification)
        
        # 削除されていることを確認
        assert notification not in self.feedback_system.active_notifications
    
    def test_dismiss_all_notifications(self):
        """全通知削除のテスト"""
        # テスト通知を追加
        for i in range(3):
            notification = Notification(f"テスト{i}", NotificationType.INFO)
            self.feedback_system.active_notifications.append(notification)
        
        # キューにも追加
        self.feedback_system.notification_queue.append(
            Notification("キューテスト", NotificationType.INFO)
        )
        
        # 全削除
        self.feedback_system.dismiss_all_notifications()
        
        # すべて削除されていることを確認
        assert len(self.feedback_system.active_notifications) == 0
        assert len(self.feedback_system.notification_queue) == 0
    
    @patch('src.ui.feedback_system.ui_manager')
    def test_error_dialog(self, mock_ui_manager):
        """エラーダイアログのテスト"""
        title = "テストエラー"
        message = "エラーメッセージ"
        
        self.feedback_system.show_error_dialog(title, message)
        
        # ダイアログが表示されることを確認
        assert mock_ui_manager.register_element.called
        assert mock_ui_manager.show_element.called
    
    @patch('src.ui.feedback_system.ui_manager')
    def test_confirmation_dialog(self, mock_ui_manager):
        """確認ダイアログのテスト"""
        title = "確認"
        message = "実行しますか？"
        confirm_callback = Mock()
        cancel_callback = Mock()
        
        self.feedback_system.show_confirmation_dialog(
            title, message, confirm_callback, cancel_callback
        )
        
        # ダイアログが表示されることを確認
        assert mock_ui_manager.register_element.called
        assert mock_ui_manager.show_element.called
    
    def test_progress_notification(self):
        """進行状況通知のテスト"""
        message = "ロード中"
        progress = 0.5
        
        # 進行状況通知を表示
        self.feedback_system.show_progress_notification(message, progress)
        
        # 通知が作成されることを確認（UIマネージャーがモックなので詳細は確認できない）
        # ここでは例外が発生しないことを確認
        assert True
    
    def test_achievement_notification(self):
        """実績通知のテスト"""
        title = "初回クリア"
        description = "初めてダンジョンをクリアしました"
        
        # 実績通知を表示
        self.feedback_system.show_achievement(title, description)
        
        # 例外が発生しないことを確認
        assert True
        
        # 実績表示が無効の場合
        self.feedback_system.show_achievements = False
        self.feedback_system.show_achievement(title, description)
        
        # 例外が発生しないことを確認
        assert True
    
    def test_system_info_notification(self):
        """システム情報通知のテスト"""
        message = "セーブ完了"
        
        # システム情報を表示
        self.feedback_system.show_system_info(message)
        
        # 例外が発生しないことを確認
        assert True
    
    def test_user_tip_notification(self):
        """ユーザーヒント通知のテスト"""
        tip = "装備を確認しましょう"
        
        # ヒントを表示（VERBOSEレベルでのみ）
        self.feedback_system.set_feedback_level(FeedbackLevel.VERBOSE)
        self.feedback_system.show_user_tip(tip)
        
        # 例外が発生しないことを確認
        assert True


class TestFeedbackFunctions:
    """フィードバック便利関数のテスト"""
    
    @patch('src.ui.feedback_system.feedback_system')
    def test_show_info_function(self, mock_feedback):
        """情報表示関数のテスト"""
        message = "情報メッセージ"
        duration = 2.0
        
        show_info(message, duration)
        
        mock_feedback.show_notification.assert_called_once_with(
            message, NotificationType.INFO, duration
        )
    
    @patch('src.ui.feedback_system.feedback_system')
    def test_show_success_function(self, mock_feedback):
        """成功表示関数のテスト"""
        message = "成功メッセージ"
        duration = 3.0
        
        show_success(message, duration)
        
        mock_feedback.show_notification.assert_called_once_with(
            message, NotificationType.SUCCESS, duration
        )
    
    @patch('src.ui.feedback_system.feedback_system')
    def test_show_warning_function(self, mock_feedback):
        """警告表示関数のテスト"""
        message = "警告メッセージ"
        duration = 4.0
        
        show_warning(message, duration)
        
        mock_feedback.show_notification.assert_called_once_with(
            message, NotificationType.WARNING, duration
        )
    
    @patch('src.ui.feedback_system.feedback_system')
    def test_show_error_function(self, mock_feedback):
        """エラー表示関数のテスト"""
        message = "エラーメッセージ"
        
        # 通常のエラー
        show_error(message)
        mock_feedback.show_notification.assert_called_with(
            message, NotificationType.ERROR, 5.0, False
        )
        
        # 永続エラー
        mock_feedback.reset_mock()
        show_error(message, persistent=True)
        mock_feedback.show_notification.assert_called_with(
            message, NotificationType.ERROR, float('inf'), True
        )
    
    @patch('src.ui.feedback_system.feedback_system')
    def test_show_achievement_function(self, mock_feedback):
        """実績表示関数のテスト"""
        title = "テスト実績"
        description = "テスト説明"
        
        show_achievement(title, description)
        
        mock_feedback.show_achievement.assert_called_once_with(title, description)


class TestFeedbackSystemIntegration:
    """フィードバックシステム統合テスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        with patch('src.ui.feedback_system.DirectFrame'), \
             patch('src.ui.feedback_system.DirectLabel'), \
             patch('src.ui.feedback_system.base'):
            self.feedback_system = FeedbackSystem()
    
    def test_feedback_system_full_workflow(self):
        """フィードバックシステム完全ワークフローのテスト"""
        # 1. 初期状態確認
        assert len(self.feedback_system.active_notifications) == 0
        assert len(self.feedback_system.notification_queue) == 0
        
        # 2. 様々なタイプの通知をテスト
        test_notifications = [
            ("情報", NotificationType.INFO),
            ("成功", NotificationType.SUCCESS),
            ("警告", NotificationType.WARNING),
            ("エラー", NotificationType.ERROR),
            ("実績", NotificationType.ACHIEVEMENT)
        ]
        
        for message, ntype in test_notifications:
            # 例外が発生しないことを確認
            try:
                self.feedback_system.show_notification(message, ntype)
            except Exception as e:
                # UIマネージャー関連のエラーは許容
                if "ui_manager" not in str(e).lower() and "DirectLabel" not in str(e):
                    raise
        
        # 3. フィードバックレベル変更のテスト
        for level in FeedbackLevel:
            self.feedback_system.set_feedback_level(level)
            assert self.feedback_system.feedback_level == level
        
        # 4. クリーンアップ
        self.feedback_system.cleanup()
    
    def test_notification_lifecycle(self):
        """通知のライフサイクルテスト"""
        # 通知作成
        notification = Notification("ライフサイクルテスト", NotificationType.INFO, duration=1.0)
        
        # 期限切れでない状態
        assert not notification.is_expired()
        
        # 通知をシステムに追加（モック環境では表示はスキップ）
        self.feedback_system.active_notifications.append(notification)
        assert len(self.feedback_system.active_notifications) == 1
        
        # 削除
        self.feedback_system._remove_notification(notification)
        assert len(self.feedback_system.active_notifications) == 0