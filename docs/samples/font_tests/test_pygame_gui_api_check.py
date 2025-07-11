#!/usr/bin/env python3
"""
pygame_gui 0.6.14のAPIを調べる
"""
import pygame
import pygame_gui

def check_pygame_gui_api():
    """pygame_guiのAPIを調べる"""
    pygame.init()
    
    # UIManager初期化
    manager = pygame_gui.UIManager((800, 600))
    
    print("pygame_gui UIManager利用可能メソッド:")
    methods = [method for method in dir(manager) if not method.startswith('_')]
    for method in sorted(methods):
        print(f"  - {method}")
    
    print("\npygame_gui UIManager.get_theme()利用可能メソッド:")
    theme = manager.get_theme()
    theme_methods = [method for method in dir(theme) if not method.startswith('_')]
    for method in sorted(theme_methods):
        print(f"  - {method}")
    
    # フォント辞書も調べる
    if hasattr(manager, 'font_dictionary'):
        print("\npygame_gui font_dictionary利用可能メソッド:")
        font_dict = manager.font_dictionary
        font_methods = [method for method in dir(font_dict) if not method.startswith('_')]
        for method in sorted(font_methods):
            print(f"  - {method}")
    elif hasattr(manager, 'get_font_dictionary'):
        print("\npygame_gui get_font_dictionary()利用可能メソッド:")
        font_dict = manager.get_font_dictionary()
        font_methods = [method for method in dir(font_dict) if not method.startswith('_')]
        for method in sorted(font_methods):
            print(f"  - {method}")
    
    pygame.quit()

if __name__ == "__main__":
    check_pygame_gui_api()