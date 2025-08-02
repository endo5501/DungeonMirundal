"""
インターフェース定義モジュール

このモジュールでは、型安全性を向上させるためのProtocolベースの
インターフェース定義を提供します。
"""

from .core_protocols import (
    Cleanupable,
    MessageSender,
    MessageReceiver,
    Renderable,
    Updatable,
)

__all__ = [
    "Cleanupable",
    "MessageSender", 
    "MessageReceiver",
    "Renderable",
    "Updatable",
]