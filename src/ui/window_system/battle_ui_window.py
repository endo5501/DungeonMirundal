"""
BattleUIWindow クラス

戦闘UI管理ウィンドウ
"""

import pygame
import pygame_gui
from typing import Dict, List, Any, Optional, Tuple

from .window import Window
from .battle_types import (
    BattlePhase, BattleActionType, BattleConfig, CharacterStatus, EnemyStatus,
    BattleAction, BattleLayout, BattleUIState, BattleLogEntry, TargetType,
    StatusEffect, KeyboardShortcut, ActionMenuEntry, TargetInfo
)
from src.utils.logger import logger


class BattleUIWindow(Window):
    """
    戦闘UIウィンドウクラス
    
    戦闘の表示、アクション選択、ターゲット選択を行うウィンドウ
    """
    
    def __init__(self, window_id: str, battle_config: Dict[str, Any], 
                 parent: Optional[Window] = None, modal: bool = False):
        """
        戦闘UIウィンドウを初期化
        
        Args:
            window_id: ウィンドウID
            battle_config: 戦闘設定辞書
            parent: 親ウィンドウ
            modal: モーダルウィンドウかどうか
        """
        super().__init__(window_id, parent, modal)
        
        # 設定の検証と変換
        self.battle_config = self._validate_and_convert_config(battle_config)
        
        # 戦闘情報
        self.battle_manager = self.battle_config.battle_manager
        self.party = self.battle_config.party
        self.enemies = self.battle_config.enemies
        
        # 戦闘状態
        self.current_phase = BattlePhase.PLAYER_ACTION
        self.selected_action: Optional[BattleActionType] = None
        self.selected_target: Optional[Any] = None
        
        # レイアウト
        self.layout = self.battle_config.layout
        
        # UI要素
        self.main_container: Optional[pygame_gui.core.UIElement] = None
        self.party_status_panel: Optional[pygame_gui.elements.UIPanel] = None
        self.enemy_status_panel: Optional[pygame_gui.elements.UIPanel] = None
        self.action_menu_panel: Optional[pygame_gui.elements.UIPanel] = None
        self.battle_log_panel: Optional[pygame_gui.elements.UIPanel] = None
        self.magic_menu_panel: Optional[pygame_gui.elements.UIPanel] = None
        self.item_menu_panel: Optional[pygame_gui.elements.UIPanel] = None
        self.status_effects_panel: Optional[pygame_gui.elements.UIPanel] = None
        
        # UI要素リスト
        self.character_status_displays: List[pygame_gui.core.UIElement] = []
        self.enemy_status_displays: List[pygame_gui.core.UIElement] = []
        self.action_buttons: List[pygame_gui.elements.UIButton] = []
        self.magic_buttons: List[pygame_gui.elements.UIButton] = []
        self.item_buttons: List[pygame_gui.elements.UIButton] = []
        
        # 戦闘ログ
        self.battle_log_display: Optional[pygame_gui.elements.UITextBox] = None
        
        # キーボードショートカット
        self.keyboard_shortcuts = self._setup_keyboard_shortcuts()
        
        logger.debug(f"BattleUIWindowを初期化: {window_id}")
    
    def _validate_and_convert_config(self, config: Dict[str, Any]) -> BattleConfig:
        """設定を検証してBattleConfigに変換"""
        if 'battle_manager' not in config:
            raise ValueError("Battle config must contain 'battle_manager'")
        if 'party' not in config:
            raise ValueError("Battle config must contain 'party'")
        
        battle_config = BattleConfig(
            battle_manager=config['battle_manager'],
            party=config['party'],
            enemies=config['enemies'],
            show_battle_log=config.get('show_battle_log', True),
            show_status_effects=config.get('show_status_effects', True),
            enable_keyboard_shortcuts=config.get('enable_keyboard_shortcuts', True),
            enable_animations=config.get('enable_animations', True),
            auto_advance_log=config.get('auto_advance_log', False),
            log_max_entries=config.get('log_max_entries', 100)
        )
        
        battle_config.validate()
        return battle_config
    
    def _setup_keyboard_shortcuts(self) -> Dict[int, BattleActionType]:
        """キーボードショートカットを設定"""
        if not self.battle_config.enable_keyboard_shortcuts:
            return {}
        
        return {
            pygame.K_a: BattleActionType.ATTACK,
            pygame.K_m: BattleActionType.MAGIC,
            pygame.K_i: BattleActionType.ITEM,
            pygame.K_d: BattleActionType.DEFEND,
            pygame.K_e: BattleActionType.ESCAPE
        }
    
    def create(self) -> None:
        """UI要素を作成"""
        if not self.ui_manager:
            self._initialize_ui_manager()
            self._calculate_layout()
            self._create_main_container()
            self._create_party_status_panel()
            self._create_enemy_status_panel()
            self._create_action_menu_panel()
            if self.battle_config.show_battle_log:
                self._create_battle_log_panel()
            if self.battle_config.show_status_effects:
                self._create_status_effects_panel()
        
        logger.debug(f"BattleUIWindow UI要素を作成: {self.window_id}")
    
    def _initialize_ui_manager(self) -> None:
        """UIManagerを初期化"""
        screen_width = 1024
        screen_height = 768
        self.ui_manager = pygame_gui.UIManager((screen_width, screen_height))
    
    def _calculate_layout(self) -> None:
        """レイアウトを計算"""
        # ウィンドウサイズを計算
        window_width = self.layout.window_min_width
        window_height = self.layout.window_min_height
        
        # フルスクリーンレイアウト
        self.rect = pygame.Rect(0, 0, window_width, window_height)
    
    def _create_main_container(self) -> None:
        """メインコンテナを作成"""
        self.main_container = pygame_gui.elements.UIPanel(
            relative_rect=self.rect,
            manager=self.ui_manager
        )
    
    def _create_party_status_panel(self) -> None:
        """パーティステータスパネルを作成"""
        party_rect = pygame.Rect(
            self.layout.panel_padding,
            self.layout.panel_padding,
            self.layout.party_status_width,
            self.layout.party_status_height
        )
        
        self.party_status_panel = pygame_gui.elements.UIPanel(
            relative_rect=party_rect,
            manager=self.ui_manager,
            container=self.main_container
        )
        
        self._create_character_status_displays()
    
    def _create_character_status_displays(self) -> None:
        """キャラクターステータス表示を作成"""
        self.character_status_displays = []
        
        if hasattr(self.party, 'get_alive_members'):
            alive_members = self.party.get_alive_members()
            
            # alive_membersがiterableである場合のみ処理
            if hasattr(alive_members, '__iter__'):
                for i, character in enumerate(alive_members):
                    status_rect = pygame.Rect(
                        10,
                        10 + i * (self.layout.status_bar_height + 5),
                        self.layout.party_status_width - 20,
                        self.layout.status_bar_height
                    )
                    
                    status_text = f"{character.name}: HP {character.hp}/{character.max_hp}"
                    if hasattr(character, 'mp'):
                        status_text += f" MP {character.mp}/{character.max_mp}"
                    
                    status_label = pygame_gui.elements.UILabel(
                        relative_rect=status_rect,
                        text=status_text,
                        manager=self.ui_manager,
                        container=self.party_status_panel
                    )
                    
                    self.character_status_displays.append(status_label)
    
    def _create_enemy_status_panel(self) -> None:
        """敵ステータスパネルを作成"""
        enemy_rect = pygame.Rect(
            self.rect.width - self.layout.enemy_status_width - self.layout.panel_padding,
            self.layout.panel_padding,
            self.layout.enemy_status_width,
            self.layout.enemy_status_height
        )
        
        self.enemy_status_panel = pygame_gui.elements.UIPanel(
            relative_rect=enemy_rect,
            manager=self.ui_manager,
            container=self.main_container
        )
        
        self._create_enemy_status_displays()
    
    def _create_enemy_status_displays(self) -> None:
        """敵ステータス表示を作成"""
        self.enemy_status_displays = []
        
        if hasattr(self.enemies, 'get_all_enemies'):
            all_enemies = self.enemies.get_all_enemies()
            
            # all_enemiesがiterableである場合のみ処理
            if hasattr(all_enemies, '__iter__'):
                for i, enemy in enumerate(all_enemies):
                    status_rect = pygame.Rect(
                        10,
                        10 + i * (self.layout.status_bar_height + 5),
                        self.layout.enemy_status_width - 20,
                        self.layout.status_bar_height
                    )
                    
                    # 敵の生存状態に応じて表示を変更
                    if hasattr(enemy, 'is_alive') and enemy.is_alive():
                        status_text = f"{enemy.name}: HP {enemy.hp}/{enemy.max_hp}"
                    else:
                        status_text = f"{enemy.name}: 倒された"
                    
                    status_label = pygame_gui.elements.UILabel(
                        relative_rect=status_rect,
                        text=status_text,
                        manager=self.ui_manager,
                        container=self.enemy_status_panel
                    )
                    
                    self.enemy_status_displays.append(status_label)
    
    def _create_action_menu_panel(self) -> None:
        """アクションメニューパネルを作成"""
        action_rect = pygame.Rect(
            self.layout.panel_padding,
            self.rect.height - self.layout.action_menu_height - self.layout.panel_padding,
            self.layout.action_menu_width,
            self.layout.action_menu_height
        )
        
        self.action_menu_panel = pygame_gui.elements.UIPanel(
            relative_rect=action_rect,
            manager=self.ui_manager,
            container=self.main_container
        )
    
    def _create_battle_log_panel(self) -> None:
        """戦闘ログパネルを作成"""
        log_rect = pygame.Rect(
            self.layout.action_menu_width + self.layout.panel_padding * 2,
            self.rect.height - self.layout.battle_log_height - self.layout.panel_padding,
            self.layout.battle_log_width,
            self.layout.battle_log_height
        )
        
        self.battle_log_panel = pygame_gui.elements.UIPanel(
            relative_rect=log_rect,
            manager=self.ui_manager,
            container=self.main_container
        )
    
    def _create_status_effects_panel(self) -> None:
        """ステータス効果パネルを作成"""
        effects_rect = pygame.Rect(
            self.layout.party_status_width + self.layout.panel_padding * 2,
            self.layout.panel_padding,
            300,
            100
        )
        
        self.status_effects_panel = pygame_gui.elements.UIPanel(
            relative_rect=effects_rect,
            manager=self.ui_manager,
            container=self.main_container
        )
    
    def update_battle_phase(self, new_phase: BattlePhase) -> None:
        """戦闘フェーズを更新"""
        self.current_phase = new_phase
        
        if new_phase == BattlePhase.PLAYER_ACTION:
            self._show_action_menu()
        elif new_phase == BattlePhase.TARGET_SELECTION:
            self._show_target_selection()
        
        logger.debug(f"戦闘フェーズ更新: {new_phase}")
    
    def _show_action_menu(self) -> None:
        """アクションメニューを表示"""
        self.action_buttons = []
        
        if hasattr(self.battle_manager, 'get_available_actions'):
            actions = self.battle_manager.get_available_actions()
            
            for i, action in enumerate(actions):
                button_rect = pygame.Rect(
                    10,
                    10 + i * (self.layout.button_height + 5),
                    self.layout.action_menu_width - 20,
                    self.layout.button_height
                )
                
                action_button = pygame_gui.elements.UIButton(
                    relative_rect=button_rect,
                    text=action['name'],
                    manager=self.ui_manager,
                    container=self.action_menu_panel
                )
                
                if not action.get('enabled', True):
                    action_button.disable()
                
                self.action_buttons.append(action_button)
    
    def _show_target_selection(self) -> None:
        """ターゲット選択を表示"""
        # ターゲット選択UI（実装省略）
        pass
    
    def select_action(self, action_type: BattleActionType) -> bool:
        """アクションを選択"""
        if self.current_phase != BattlePhase.PLAYER_ACTION:
            return False
        
        if hasattr(self.battle_manager, 'can_perform_action'):
            if not self.battle_manager.can_perform_action(action_type):
                return False
        
        self.selected_action = action_type
        
        # アクション選択メッセージを送信
        current_character = None
        if hasattr(self.battle_manager, 'get_current_character'):
            current_character = self.battle_manager.get_current_character()
        
        self.send_message('battle_action_selected', {
            'action_type': action_type,
            'character': current_character
        })
        
        logger.debug(f"アクション選択: {action_type}")
        return True
    
    def select_target(self, target: Any) -> bool:
        """ターゲットを選択"""
        if self.current_phase != BattlePhase.TARGET_SELECTION:
            return False
        
        self.selected_target = target
        
        self.send_message('battle_target_selected', {
            'target': target
        })
        
        logger.debug(f"ターゲット選択: {target}")
        return True
    
    def update_battle_log(self) -> None:
        """戦闘ログを更新"""
        if not self.battle_log_panel:
            return
        
        if hasattr(self.battle_manager, 'get_battle_log'):
            log_entries = self.battle_manager.get_battle_log()
            log_text = "<br>".join(log_entries[-10:])  # 最新10件
            
            if not self.battle_log_display:
                self.battle_log_display = pygame_gui.elements.UITextBox(
                    relative_rect=pygame.Rect(10, 10, 
                                             self.layout.battle_log_width - 20,
                                             self.layout.battle_log_height - 20),
                    html_text=log_text,
                    manager=self.ui_manager,
                    container=self.battle_log_panel
                )
            else:
                self.battle_log_display.set_text(log_text)
    
    def show_magic_menu(self) -> bool:
        """魔法メニューを表示"""
        if not hasattr(self.battle_manager, 'get_current_character'):
            return False
        
        current_character = self.battle_manager.get_current_character()
        if not hasattr(current_character, 'get_available_spells'):
            return False
        
        # 魔法メニューパネルを作成
        if not self.magic_menu_panel:
            magic_rect = pygame.Rect(
                self.layout.action_menu_width + self.layout.panel_padding * 2,
                self.rect.height - self.layout.action_menu_height - self.layout.panel_padding,
                self.layout.action_menu_width,
                self.layout.action_menu_height
            )
            
            self.magic_menu_panel = pygame_gui.elements.UIPanel(
                relative_rect=magic_rect,
                manager=self.ui_manager,
                container=self.main_container
            )
        
        # 魔法ボタンを作成
        self.magic_buttons = []
        spells = current_character.get_available_spells()
        
        for i, spell in enumerate(spells):
            button_rect = pygame.Rect(
                10,
                10 + i * (self.layout.button_height + 5),
                self.layout.action_menu_width - 20,
                self.layout.button_height
            )
            
            button_text = f"{spell.name} (MP {spell.mp_cost})"
            magic_button = pygame_gui.elements.UIButton(
                relative_rect=button_rect,
                text=button_text,
                manager=self.ui_manager,
                container=self.magic_menu_panel
            )
            
            if not spell.can_cast():
                magic_button.disable()
            
            self.magic_buttons.append(magic_button)
        
        logger.debug("魔法メニュー表示")
        return True
    
    def show_item_menu(self) -> bool:
        """アイテムメニューを表示"""
        if not hasattr(self.party, 'get_usable_items'):
            return False
        
        # アイテムメニューパネルを作成
        if not self.item_menu_panel:
            item_rect = pygame.Rect(
                self.layout.action_menu_width + self.layout.panel_padding * 2,
                self.rect.height - self.layout.action_menu_height - self.layout.panel_padding,
                self.layout.action_menu_width,
                self.layout.action_menu_height
            )
            
            self.item_menu_panel = pygame_gui.elements.UIPanel(
                relative_rect=item_rect,
                manager=self.ui_manager,
                container=self.main_container
            )
        
        # アイテムボタンを作成
        self.item_buttons = []
        items = self.party.get_usable_items()
        
        for i, item in enumerate(items):
            button_rect = pygame.Rect(
                10,
                10 + i * (self.layout.button_height + 5),
                self.layout.action_menu_width - 20,
                self.layout.button_height
            )
            
            button_text = f"{item.name} x{item.quantity}"
            item_button = pygame_gui.elements.UIButton(
                relative_rect=button_rect,
                text=button_text,
                manager=self.ui_manager,
                container=self.item_menu_panel
            )
            
            if not item.is_usable_in_battle():
                item_button.disable()
            
            self.item_buttons.append(item_button)
        
        logger.debug("アイテムメニュー表示")
        return True
    
    def advance_turn(self) -> bool:
        """ターンを進行"""
        if hasattr(self.battle_manager, 'advance_turn'):
            if self.battle_manager.advance_turn():
                new_phase = BattlePhase.ENEMY_TURN
                if hasattr(self.battle_manager, 'get_current_phase'):
                    new_phase = self.battle_manager.get_current_phase()
                
                self.send_message('battle_turn_advanced', {
                    'new_phase': new_phase
                })
                
                logger.debug("ターン進行")
                return True
        
        return False
    
    def update_status_effects(self) -> None:
        """ステータス効果を更新"""
        if not self.status_effects_panel:
            return
        
        # ステータス効果の表示更新（実装省略）
        logger.debug("ステータス効果更新")
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベントを処理"""
        if not self.ui_manager:
            return False
        
        # pygame-guiにイベントを渡す
        self.ui_manager.process_events(event)
        
        # キーボードイベント
        if event.type == pygame.KEYDOWN:
            return self._handle_keyboard_event(event)
        
        # ボタンクリック処理
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            return self._handle_button_click(event)
        
        return False
    
    def _handle_keyboard_event(self, event) -> bool:
        """キーボードイベントを処理"""
        if event.key in self.keyboard_shortcuts:
            action_type = self.keyboard_shortcuts[event.key]
            return self.select_action(action_type)
        
        return False
    
    def _handle_button_click(self, event) -> bool:
        """ボタンクリックを処理"""
        # アクションボタンのクリック
        for i, button in enumerate(self.action_buttons):
            if event.ui_element == button:
                # ボタンインデックスからアクションタイプを決定
                action_types = [BattleActionType.ATTACK, BattleActionType.MAGIC, 
                               BattleActionType.ITEM, BattleActionType.DEFEND]
                if i < len(action_types):
                    return self.select_action(action_types[i])
        
        return False
    
    def handle_escape(self) -> bool:
        """ESCキーの処理"""
        self.send_message('battle_menu_requested', {})
        
        logger.debug("戦闘メニュー要求")
        return True
    
    def cleanup_ui(self) -> None:
        """UI要素のクリーンアップ"""
        # ボタンリストをクリア
        self.action_buttons.clear()
        self.magic_buttons.clear()
        self.item_buttons.clear()
        self.character_status_displays.clear()
        self.enemy_status_displays.clear()
        
        # UI要素をクリア
        self.party_status_panel = None
        self.enemy_status_panel = None
        self.action_menu_panel = None
        self.battle_log_panel = None
        self.magic_menu_panel = None
        self.item_menu_panel = None
        self.status_effects_panel = None
        
        # pygame-guiの要素を削除
        if self.ui_manager:
            for element in list(self.ui_manager.get_root_container().elements):
                element.kill()
            self.ui_manager = None
        
        logger.debug(f"BattleUIWindow UI要素をクリーンアップ: {self.window_id}")


# BattlePhase, BattleActionTypeを直接エクスポート
from .battle_types import BattlePhase, BattleActionType