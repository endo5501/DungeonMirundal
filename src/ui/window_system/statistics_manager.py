"""
StatisticsManager クラス

システム統計情報の管理を行う
"""

from typing import Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SystemStatistics:
    """システム統計情報"""
    windows_created: int = 0
    windows_destroyed: int = 0
    events_processed: int = 0
    frames_rendered: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    
    def reset(self) -> None:
        """統計情報をリセット"""
        self.windows_created = 0
        self.windows_destroyed = 0
        self.events_processed = 0
        self.frames_rendered = 0
        self.start_time = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式で統計情報を取得"""
        uptime = datetime.now() - self.start_time
        return {
            'windows_created': self.windows_created,
            'windows_destroyed': self.windows_destroyed,
            'events_processed': self.events_processed,
            'frames_rendered': self.frames_rendered,
            'uptime_seconds': uptime.total_seconds(),
            'start_time': self.start_time.isoformat()
        }


class StatisticsManager:
    """
    統計情報管理クラス
    
    システム全体の統計情報を一元管理する
    """
    
    def __init__(self):
        """統計管理を初期化"""
        self.system_stats = SystemStatistics()
        self.custom_counters: Dict[str, int] = {}
        self.performance_metrics: Dict[str, float] = {}
    
    def increment_counter(self, counter_name: str, amount: int = 1) -> None:
        """カウンターを増加"""
        if hasattr(self.system_stats, counter_name):
            current_value = getattr(self.system_stats, counter_name)
            setattr(self.system_stats, counter_name, current_value + amount)
        else:
            self.custom_counters[counter_name] = self.custom_counters.get(counter_name, 0) + amount
    
    def set_metric(self, metric_name: str, value: float) -> None:
        """パフォーマンスメトリクスを設定"""
        self.performance_metrics[metric_name] = value
    
    def get_counter(self, counter_name: str) -> int:
        """カウンター値を取得"""
        if hasattr(self.system_stats, counter_name):
            return getattr(self.system_stats, counter_name)
        return self.custom_counters.get(counter_name, 0)
    
    def get_metric(self, metric_name: str) -> float:
        """メトリクス値を取得"""
        return self.performance_metrics.get(metric_name, 0.0)
    
    def get_all_statistics(self) -> Dict[str, Any]:
        """全統計情報を取得"""
        stats = self.system_stats.to_dict()
        stats.update({
            'custom_counters': self.custom_counters.copy(),
            'performance_metrics': self.performance_metrics.copy()
        })
        return stats
    
    def reset_all(self) -> None:
        """全統計情報をリセット"""
        self.system_stats.reset()
        self.custom_counters.clear()
        self.performance_metrics.clear()
    
    def get_summary_report(self) -> str:
        """サマリーレポートを取得"""
        stats = self.get_all_statistics()
        uptime_minutes = stats['uptime_seconds'] / 60
        
        lines = [
            "=== System Statistics Summary ===",
            f"Uptime: {uptime_minutes:.1f} minutes",
            f"Windows Created: {stats['windows_created']}",
            f"Windows Destroyed: {stats['windows_destroyed']}",
            f"Active Windows: {stats['windows_created'] - stats['windows_destroyed']}",
            f"Events Processed: {stats['events_processed']}",
            f"Frames Rendered: {stats['frames_rendered']}"
        ]
        
        if stats['frames_rendered'] > 0 and uptime_minutes > 0:
            fps = stats['frames_rendered'] / (uptime_minutes * 60)
            lines.append(f"Average FPS: {fps:.1f}")
        
        if stats['custom_counters']:
            lines.append("\nCustom Counters:")
            for name, value in stats['custom_counters'].items():
                lines.append(f"  {name}: {value}")
        
        if stats['performance_metrics']:
            lines.append("\nPerformance Metrics:")
            for name, value in stats['performance_metrics'].items():
                lines.append(f"  {name}: {value:.3f}")
        
        return "\n".join(lines)
    
    def __str__(self) -> str:
        return f"StatisticsManager(windows: {self.get_counter('windows_created')}, events: {self.get_counter('events_processed')})"