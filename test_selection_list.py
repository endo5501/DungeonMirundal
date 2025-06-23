#!/usr/bin/env python
"""UISelectionList の動作テスト"""

import pygame
import pygame_gui
import sys

# プロジェクトパスを追加
sys.path.append('/home/satorue/Dungeon')

from src.ui.selection_list_ui import ItemSelectionList, SelectionListData
from src.items.item import Item, ItemType, ItemRarity


class TestItem:
    """テスト用のアイテムクラス"""
    
    def __init__(self, name: str, price: int):
        self.name = name
        self.price = price
        self.item_type = ItemType.WEAPON
        self.description = f"{name}の説明"
    
    def get_name(self):
        return self.name


def main():
    """メイン関数"""
    # Pygame初期化
    pygame.init()
    
    # 画面設定
    screen_width = 800
    screen_height = 600
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("UISelectionList テスト")
    
    # pygame-gui マネージャー
    manager = pygame_gui.UIManager((screen_width, screen_height))
    
    # テスト用アイテム作成
    test_items = [
        TestItem("鉄の剣", 100),
        TestItem("鋼の剣", 200),
        TestItem("ミスリルの剣", 500),
        TestItem("皮の鎧", 80),
        TestItem("鉄の鎧", 150),
        TestItem("回復薬", 50),
        TestItem("魔法薬", 120),
    ]
    
    # アイテム選択リスト作成
    list_rect = pygame.Rect(100, 100, 600, 400)
    item_list = ItemSelectionList(
        relative_rect=list_rect,
        manager=manager,
        title="アイテム選択テスト"
    )
    
    # アイテムを追加
    for item in test_items:
        display_name = f"{item.get_name()} - {item.price}G"
        item_list.add_item_data(item, display_name)
    
    # コールバック設定
    def on_item_selected(item):
        print(f"選択されたアイテム: {item.get_name()} ({item.price}G)")
    
    def on_item_details(item):
        print(f"アイテム詳細: {item.get_name()} - {item.description}")
    
    item_list.on_item_selected = on_item_selected
    item_list.on_item_details = on_item_details
    
    # 表示
    item_list.show()
    
    # メインループ
    clock = pygame.time.Clock()
    running = True
    
    while running:
        time_delta = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # UIイベント処理
            manager.process_events(event)
            item_list.handle_event(event)
        
        # 更新
        manager.update(time_delta)
        
        # 描画
        screen.fill((30, 30, 30))
        manager.draw_ui(screen)
        
        pygame.display.flip()
    
    pygame.quit()


if __name__ == "__main__":
    main()