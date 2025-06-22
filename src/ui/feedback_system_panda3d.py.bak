"""UIフィードバック・通知システム"""

from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import time
from direct.gui.DirectGui import DirectFrame, DirectLabel
from panda3d.core import TextNode

from src.ui.base_ui import UIElement, UIDialog, ui_manager
from src.core.config_manager import config_manager
from src.utils.logger import logger


class NotificationType(Enum):
    """通知タイプ"""
    INFO = "info"           # 情報
    SUCCESS = "success"     # 成功
    WARNING = "warning"     # 警告  
    ERROR = "error"         # エラー
    ACHIEVEMENT = "achievement"  # 実績


class FeedbackLevel(Enum):
    """フィードバックレベル"""
    SILENT = "silent"       # 無音
    MINIMAL = "minimal"     # 最小限
    NORMAL = "normal"       # 通常
    VERBOSE = "verbose"     # 詳細


class Notification:
    """通知クラス"""
    
    def __init__(self, message: str, notification_type: NotificationType, 
                 duration: float = 3.0, persistent: bool = False):
        self.message = message
        self.type = notification_type
        self.duration = duration
        self.persistent = persistent
        self.created_at = time.time()
        self.ui_element: Optional[DirectLabel] = None
    
    def is_expired(self) -> bool:
        """通知の有効期限切れチェック"""
        if self.persistent:
            return False
        return time.time() - self.created_at > self.duration


class FeedbackSystem:
    """UIフィードバック・通知システム"""
    
    def __init__(self):
        # 設定
        self.feedback_level = FeedbackLevel.NORMAL
        self.show_achievements = True
        self.auto_dismiss = True
        self.max_notifications = 5
        
        # 通知管理
        self.active_notifications: List[Notification] = []
        self.notification_queue: List[Notification] = []
        
        # UI要素
        self.notification_container: Optional[DirectFrame] = None
        
        # 色設定
        self.type_colors = {
            NotificationType.INFO: (0.3, 0.6, 1.0, 0.9),      # 青
            NotificationType.SUCCESS: (0.2, 0.8, 0.3, 0.9),   # 緑
            NotificationType.WARNING: (1.0, 0.8, 0.2, 0.9),   # 黄
            NotificationType.ERROR: (1.0, 0.3, 0.3, 0.9),     # 赤
            NotificationType.ACHIEVEMENT: (0.8, 0.4, 1.0, 0.9) # 紫
        }
        
        self._setup_notification_container()
        self._start_update_task()
        
        logger.info("フィードバックシステムを初期化しました")
    
    def _setup_notification_container(self):
        """通知コンテナを設定"""
        self.notification_container = DirectFrame(
            frameColor=(0, 0, 0, 0),  # 透明
            frameSize=(0.5, 1.9, -1.0, -0.2),
            pos=(0, 0, 0)
        )
        self.notification_container.hide()
    
    def _start_update_task(self):
        """更新タスクを開始"""
        from direct.task import Task
        try:
            base.taskMgr.add(self._update_notifications, "update_notifications")
        except:
            # baseが利用できない場合は警告のみ
            logger.warning("通知更新タスクを開始できませんでした")
    
    def show_notification(self, message: str, notification_type: NotificationType = NotificationType.INFO,
                         duration: float = 3.0, persistent: bool = False):
        """通知を表示"""
        if self.feedback_level == FeedbackLevel.SILENT:
            return
        
        notification = Notification(message, notification_type, duration, persistent)
        
        # レベルによるフィルタリング
        if self._should_show_notification(notification):
            if len(self.active_notifications) >= self.max_notifications:
                self.notification_queue.append(notification)
            else:
                self._display_notification(notification)
    
    def _should_show_notification(self, notification: Notification) -> bool:
        """通知を表示すべきかチェック"""
        if self.feedback_level == FeedbackLevel.SILENT:
            return False
        elif self.feedback_level == FeedbackLevel.MINIMAL:
            return notification.type in [NotificationType.ERROR, NotificationType.ACHIEVEMENT]
        elif self.feedback_level == FeedbackLevel.NORMAL:
            return notification.type != NotificationType.INFO or notification.persistent
        else:  # VERBOSE
            return True
    
    def _display_notification(self, notification: Notification):
        """通知を実際に表示"""
        y_offset = 0.1 * len(self.active_notifications)
        color = self.type_colors.get(notification.type, (1, 1, 1, 0.9))
        
        # アイコン付きメッセージ
        icon = self._get_type_icon(notification.type)
        display_text = f"{icon} {notification.message}"
        
        notification.ui_element = DirectLabel(
            text=display_text,
            text_scale=0.05,
            text_fg=color,
            text_align=TextNode.ALeft,
            frameColor=(0, 0, 0, 0.7),
            frameSize=(-0.1, 1.4, -0.03, 0.03),
            pos=(0.5, 0, -0.2 - y_offset),
            parent=self.notification_container
        )
        
        self.active_notifications.append(notification)
        self.notification_container.show()
        
        logger.debug(f"通知を表示: {notification.message}")
    
    def _get_type_icon(self, notification_type: NotificationType) -> str:
        """通知タイプのアイコンを取得"""
        icons = {
            NotificationType.INFO: "ℹ",
            NotificationType.SUCCESS: "✓",
            NotificationType.WARNING: "⚠",
            NotificationType.ERROR: "✗",
            NotificationType.ACHIEVEMENT: "★"
        }
        return icons.get(notification_type, "•")
    
    def _update_notifications(self, task):
        """通知の更新処理"""
        try:
            # 期限切れ通知の削除
            expired = [n for n in self.active_notifications if n.is_expired()]
            for notification in expired:
                self._remove_notification(notification)
            
            # キューからの通知表示
            while (len(self.active_notifications) < self.max_notifications and 
                   self.notification_queue):
                next_notification = self.notification_queue.pop(0)
                self._display_notification(next_notification)
            
            # コンテナの表示状態管理
            if not self.active_notifications:
                self.notification_container.hide()
            
            return task.cont
        except Exception as e:
            logger.error(f"通知更新エラー: {e}")
            return task.cont
    
    def _remove_notification(self, notification: Notification):
        """通知を削除"""
        if notification in self.active_notifications:
            self.active_notifications.remove(notification)
            if notification.ui_element:
                notification.ui_element.destroy()
            
            # 残りの通知の位置を調整
            self._reposition_notifications()
    
    def _reposition_notifications(self):
        """通知の位置を再調整"""
        for i, notification in enumerate(self.active_notifications):
            if notification.ui_element:
                y_offset = 0.1 * i
                notification.ui_element.setPos(0.5, 0, -0.2 - y_offset)
    
    def dismiss_notification(self, index: int = 0):
        """指定した通知を削除"""
        if 0 <= index < len(self.active_notifications):
            notification = self.active_notifications[index]
            self._remove_notification(notification)
    
    def dismiss_all_notifications(self):
        """すべての通知を削除"""
        for notification in self.active_notifications[:]:
            self._remove_notification(notification)
        self.notification_queue.clear()
    
    def show_error_dialog(self, title: str, message: str, 
                         callback: Optional[Callable] = None):
        """エラーダイアログを表示"""
        error_text = f"【エラー】\\n\\n{message}\\n\\n"
        error_text += "この問題が継続する場合は、以下を試してください:\\n"
        error_text += "• ゲームを再起動\\n"
        error_text += "• セーブデータの確認\\n"
        error_text += "• 設定の初期化\\n"
        error_text += "• ログファイルの確認"
        
        buttons = [{"text": "OK", "command": callback or self._close_dialog}]
        
        dialog = UIDialog(
            "error_dialog",
            title,
            error_text,
            buttons=buttons
        )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)
        
        # 同時に通知も表示
        self.show_notification(f"エラー: {title}", NotificationType.ERROR, persistent=True)
    
    def show_confirmation_dialog(self, title: str, message: str,
                                on_confirm: Callable, on_cancel: Optional[Callable] = None):
        """確認ダイアログを表示"""
        buttons = [
            {"text": "はい", "command": on_confirm},
            {"text": "いいえ", "command": on_cancel or self._close_dialog}
        ]
        
        dialog = UIDialog(
            "confirmation_dialog",
            title,
            message,
            buttons=buttons
        )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)
    
    def show_progress_notification(self, message: str, progress: float):
        """進行状況通知を表示"""
        progress_text = f"{message} ({int(progress * 100)}%)"
        
        # 既存の進行状況通知を更新または新規作成
        existing = None
        for notification in self.active_notifications:
            if notification.type == NotificationType.INFO and "%" in notification.message:
                existing = notification
                break
        
        if existing and existing.ui_element:
            existing.message = progress_text
            icon = self._get_type_icon(NotificationType.INFO)
            existing.ui_element.setText(f"{icon} {progress_text}")
        else:
            self.show_notification(progress_text, NotificationType.INFO, persistent=True)
    
    def show_achievement(self, title: str, description: str):
        """実績通知を表示"""
        if not self.show_achievements:
            return
        
        achievement_text = f"実績解除: {title}\\n{description}"
        self.show_notification(achievement_text, NotificationType.ACHIEVEMENT, duration=5.0)
    
    def show_system_info(self, message: str):
        """システム情報を表示"""
        if self.feedback_level in [FeedbackLevel.NORMAL, FeedbackLevel.VERBOSE]:
            self.show_notification(message, NotificationType.INFO, duration=2.0)
    
    def show_user_tip(self, tip: str):
        """ユーザーヒントを表示"""
        if self.feedback_level == FeedbackLevel.VERBOSE:
            tip_text = f"💡 ヒント: {tip}"
            self.show_notification(tip_text, NotificationType.INFO, duration=4.0)
    
    def set_feedback_level(self, level: FeedbackLevel):
        """フィードバックレベルを設定"""
        old_level = self.feedback_level
        self.feedback_level = level
        logger.info(f"フィードバックレベル変更: {old_level.value} -> {level.value}")
        
        # レベルが下がった場合、不要な通知を削除
        if level.value < old_level.value:
            to_remove = []
            for notification in self.active_notifications:
                if not self._should_show_notification(notification):
                    to_remove.append(notification)
            
            for notification in to_remove:
                self._remove_notification(notification)
    
    def _close_dialog(self):
        """ダイアログを閉じる"""
        ui_manager.hide_all_elements()
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        self.dismiss_all_notifications()
        if self.notification_container:
            self.notification_container.destroy()
        
        try:
            base.taskMgr.remove("update_notifications")
        except:
            pass
        
        logger.info("フィードバックシステムをクリーンアップしました")


# グローバルインスタンス
feedback_system = FeedbackSystem()


# 便利関数
def show_info(message: str, duration: float = 3.0):
    """情報通知を表示"""
    feedback_system.show_notification(message, NotificationType.INFO, duration)

def show_success(message: str, duration: float = 3.0):
    """成功通知を表示"""
    feedback_system.show_notification(message, NotificationType.SUCCESS, duration)

def show_warning(message: str, duration: float = 4.0):
    """警告通知を表示"""
    feedback_system.show_notification(message, NotificationType.WARNING, duration)

def show_error(message: str, persistent: bool = False):
    """エラー通知を表示"""
    duration = float('inf') if persistent else 5.0
    feedback_system.show_notification(message, NotificationType.ERROR, duration, persistent)

def show_achievement(title: str, description: str):
    """実績通知を表示"""
    feedback_system.show_achievement(title, description)