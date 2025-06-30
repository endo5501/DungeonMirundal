"""装備ウィンドウ - WindowSystem用装備管理UI"""

from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import pygame
import pygame_gui

from src.ui.window_system.window import Window
from src.ui.window_system.window_manager import WindowManager
from src.equipment.equipment import Equipment, EquipmentSlot, EquipmentBonus
from src.items.item import Item, ItemInstance, item_manager
from src.character.party import Party
from src.character.character import Character
from src.core.config_manager import config_manager
from src.utils.logger import logger


class EquipmentViewMode(Enum):
    """装備表示モード"""
    PARTY_OVERVIEW = "party_overview"       # パーティ概要
    CHARACTER_EQUIPMENT = "character_equipment"  # キャラクター装備
    SLOT_OPTIONS = "slot_options"           # スロットオプション
    EQUIPMENT_SELECTION = "equipment_selection"  # 装備選択
    EQUIPMENT_BONUS = "equipment_bonus"     # 装備ボーナス
    EQUIPMENT_EFFECTS = "equipment_effects" # 装備効果
    PARTY_STATS = "party_stats"            # パーティ統計


class EquipmentWindow(Window):
    """装備ウィンドウクラス - WindowSystem準拠"""
    
    def __init__(self, window_id: str, parent: Optional[Window] = None, modal: bool = True):
        """
        装備ウィンドウを初期化
        
        Args:
            window_id: ウィンドウID
            parent: 親ウィンドウ
            modal: モーダル表示
        """
        super().__init__(window_id, parent, modal)
        
        # データ管理
        self.current_party: Optional[Party] = None
        self.current_character: Optional[Character] = None
        self.current_equipment: Optional[Equipment] = None
        self.selected_slot: Optional[EquipmentSlot] = None
        self.comparison_item: Optional[ItemInstance] = None
        
        # 表示モード
        self.current_mode = EquipmentViewMode.PARTY_OVERVIEW
        
        # UI要素
        self.ui_elements: Dict[str, pygame_gui.UIElement] = {}
        self.content_panel: Optional[pygame_gui.elements.UIPanel] = None
        
        # コールバック
        self.callback_on_close: Optional[Callable] = None
        
        logger.info(f"EquipmentWindow作成: {window_id}")

    def create(self) -> None:
        """UI要素を作成"""
        if not self.ui_manager:
            window_manager = WindowManager.get_instance()
            self.ui_manager = window_manager.ui_manager
            self.surface = window_manager.screen
        
        if not self.surface:
            logger.error("画面サーフェスが設定されていません")
            return
        
        # ウィンドウサイズ設定
        screen_rect = self.surface.get_rect()
        self.rect = pygame.Rect(
            screen_rect.width // 8,
            screen_rect.height // 8,
            screen_rect.width * 3 // 4,
            screen_rect.height * 3 // 4
        )
        
        # メインパネル作成
        self.content_panel = pygame_gui.elements.UIPanel(
            relative_rect=self.rect,
            manager=self.ui_manager,
            element_id="equipment_window_panel"
        )
        self.ui_elements["main_panel"] = self.content_panel
        
        # 現在のモードに応じてコンテンツを作成
        self._create_content_for_current_mode()
        
        logger.debug(f"EquipmentWindow UI要素を作成: {self.window_id}")

    def _create_content_for_current_mode(self) -> None:
        """現在のモードに応じてコンテンツを作成"""
        if self.current_mode == EquipmentViewMode.PARTY_OVERVIEW:
            self.create_party_overview()
        elif self.current_mode == EquipmentViewMode.CHARACTER_EQUIPMENT:
            self.create_character_equipment()
        elif self.current_mode == EquipmentViewMode.SLOT_OPTIONS:
            self.create_slot_options()
        elif self.current_mode == EquipmentViewMode.EQUIPMENT_SELECTION:
            self.create_equipment_selection(self.selected_slot)
        # 他のモードも必要に応じて追加

    def set_party(self, party: Party) -> None:
        """パーティを設定"""
        self.current_party = party
        if party is not None:
            logger.debug(f"パーティを設定: {party.name}")
        else:
            logger.debug("パーティを設定: None（パーティなし）")

    def show_party_equipment_overview(self) -> None:
        """パーティ装備概要を表示"""
        self.current_mode = EquipmentViewMode.PARTY_OVERVIEW
        if self.state.value == "shown":
            self._clear_content()
            self.create_party_overview()

    def create_party_overview(self) -> None:
        """パーティ概要のUI要素を作成"""
        if not self.content_panel or not self.current_party:
            return
        
        # タイトル
        title_rect = pygame.Rect(20, 20, 400, 30)
        title = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text=config_manager.get_text("equipment.party_title"),
            manager=self.ui_manager,
            container=self.content_panel
        )
        self.ui_elements["title"] = title
        
        # キャラクター一覧
        y_offset = 60
        for i, character in enumerate(self.current_party.get_all_characters()):
            equipment = character.get_equipment()
            summary = equipment.get_equipment_summary()
            equipped_count = summary['equipped_count']
            
            char_info = f"{character.name} ({equipped_count}/4)"
            
            button_rect = pygame.Rect(20, y_offset + i * 40, 300, 35)
            char_button = pygame_gui.elements.UIButton(
                relative_rect=button_rect,
                text=char_info,
                manager=self.ui_manager,
                container=self.content_panel,
                object_id=f"char_button_{i}"
            )
            self.ui_elements[f"char_button_{i}"] = char_button
        
        # パーティ統計ボタン
        stats_rect = pygame.Rect(20, y_offset + len(self.current_party.get_all_characters()) * 40 + 20, 200, 35)
        stats_button = pygame_gui.elements.UIButton(
            relative_rect=stats_rect,
            text=config_manager.get_text("equipment.party_stats"),
            manager=self.ui_manager,
            container=self.content_panel,
            object_id="party_stats_button"
        )
        self.ui_elements["party_stats_button"] = stats_button
        
        # 閉じるボタン
        close_rect = pygame.Rect(self.rect.width - 120, self.rect.height - 50, 100, 35)
        close_button = pygame_gui.elements.UIButton(
            relative_rect=close_rect,
            text=config_manager.get_text("common.close"),
            manager=self.ui_manager,
            container=self.content_panel,
            object_id="close_button"
        )
        self.ui_elements["close_button"] = close_button

    def show_character_equipment(self, character: Character) -> None:
        """キャラクター装備画面を表示"""
        self.current_character = character
        self.current_equipment = character.get_equipment()
        self.current_mode = EquipmentViewMode.CHARACTER_EQUIPMENT
        
        if self.state.value == "shown":
            self._clear_content()
            self.create_character_equipment()

    def create_character_equipment(self) -> None:
        """キャラクター装備のUI要素を作成"""
        if not self.content_panel or not self.current_character:
            return
        
        # タイトル
        title_text = config_manager.get_text("equipment_ui.character_equipment_title").format(
            character_name=self.current_character.name
        )
        title_rect = pygame.Rect(20, 20, 400, 30)
        title = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text=title_text,
            manager=self.ui_manager,
            container=self.content_panel
        )
        self.ui_elements["title"] = title
        
        # 装備スロット表示
        y_offset = 60
        for i, slot in enumerate(EquipmentSlot):
            item_instance = self.current_equipment.get_equipped_item(slot)
            slot_text = self._get_slot_display_text(slot, item_instance)
            
            button_rect = pygame.Rect(20, y_offset + i * 40, 400, 35)
            slot_button = pygame_gui.elements.UIButton(
                relative_rect=button_rect,
                text=slot_text,
                manager=self.ui_manager,
                container=self.content_panel,
                object_id=f"slot_button_{slot.value}"
            )
            self.ui_elements[f"slot_button_{slot.value}"] = slot_button
        
        # その他のボタン
        button_y = y_offset + len(EquipmentSlot) * 40 + 20
        
        bonus_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(20, button_y, 200, 35),
            text="装備ボーナス詳細",
            manager=self.ui_manager,
            container=self.content_panel,
            object_id="bonus_button"
        )
        self.ui_elements["bonus_button"] = bonus_button
        
        effects_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(20, button_y + 40, 200, 35),
            text="装備効果確認",
            manager=self.ui_manager,
            container=self.content_panel,
            object_id="effects_button"
        )
        self.ui_elements["effects_button"] = effects_button
        
        back_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(20, button_y + 80, 100, 35),
            text="戻る",
            manager=self.ui_manager,
            container=self.content_panel,
            object_id="back_button"
        )
        self.ui_elements["back_button"] = back_button

    def show_slot_options(self, slot: EquipmentSlot) -> None:
        """スロットオプションを表示"""
        self.selected_slot = slot
        self.current_mode = EquipmentViewMode.SLOT_OPTIONS
        
        if self.state.value == "shown":
            self._clear_content()
            self.create_slot_options()

    def create_slot_options(self) -> None:
        """スロットオプションのUI要素を作成"""
        if not self.content_panel or not self.selected_slot:
            return
        
        # タイトル
        title_text = f"{self._get_slot_name(self.selected_slot)}の操作"
        title_rect = pygame.Rect(20, 20, 400, 30)
        title = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text=title_text,
            manager=self.ui_manager,
            container=self.content_panel
        )
        self.ui_elements["title"] = title
        
        y_offset = 60
        item_instance = self.current_equipment.get_equipped_item(self.selected_slot)
        
        if item_instance:
            # 装備中の場合のオプション
            detail_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(20, y_offset, 200, 35),
                text="アイテム詳細",
                manager=self.ui_manager,
                container=self.content_panel,
                object_id="detail_button"
            )
            self.ui_elements["detail_button"] = detail_button
            
            unequip_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(20, y_offset + 40, 200, 35),
                text="装備を外す",
                manager=self.ui_manager,
                container=self.content_panel,
                object_id="unequip_button"
            )
            self.ui_elements["unequip_button"] = unequip_button
            
            y_offset += 80
        
        # 装備変更ボタン
        change_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(20, y_offset, 200, 35),
            text="装備を変更する",
            manager=self.ui_manager,
            container=self.content_panel,
            object_id="change_button"
        )
        self.ui_elements["change_button"] = change_button
        
        # 戻るボタン
        back_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(20, y_offset + 40, 100, 35),
            text="戻る",
            manager=self.ui_manager,
            container=self.content_panel,
            object_id="back_button"
        )
        self.ui_elements["back_button"] = back_button

    def show_equipment_selection(self, slot: EquipmentSlot) -> None:
        """装備選択画面を表示"""
        self.selected_slot = slot
        self.current_mode = EquipmentViewMode.EQUIPMENT_SELECTION
        
        if self.state.value == "shown":
            self._clear_content()
            self.create_equipment_selection(slot)

    def create_equipment_selection(self, slot: EquipmentSlot) -> None:
        """装備選択のUI要素を作成"""
        if not self.content_panel or not self.current_character:
            return
        
        # タイトル
        title_text = f"{self._get_slot_name(slot)}に装備するアイテム"
        title_rect = pygame.Rect(20, 20, 400, 30)
        title = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text=title_text,
            manager=self.ui_manager,
            container=self.content_panel
        )
        self.ui_elements["title"] = title
        
        # 装備可能アイテムを取得
        suitable_items = self._get_suitable_items_for_slot(slot)
        
        y_offset = 60
        if not suitable_items:
            no_items_label = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(20, y_offset, 400, 30),
                text="装備可能なアイテムがありません",
                manager=self.ui_manager,
                container=self.content_panel
            )
            self.ui_elements["no_items"] = no_items_label
        else:
            # アイテムリスト作成
            for i, (inventory_index, item_instance, item) in enumerate(suitable_items):
                item_text = self._get_item_display_text(item_instance, item, slot)
                
                button_rect = pygame.Rect(20, y_offset + i * 40, 450, 35)
                item_button = pygame_gui.elements.UIButton(
                    relative_rect=button_rect,
                    text=item_text,
                    manager=self.ui_manager,
                    container=self.content_panel,
                    object_id=f"item_button_{inventory_index}"
                )
                self.ui_elements[f"item_button_{inventory_index}"] = item_button
        
        # キャンセルボタン
        cancel_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(20, self.rect.height - 80, 100, 35),
            text="キャンセル",
            manager=self.ui_manager,
            container=self.content_panel,
            object_id="cancel_button"
        )
        self.ui_elements["cancel_button"] = cancel_button

    def equip_item_from_inventory(self, item_instance: ItemInstance, slot: EquipmentSlot, inventory_index: int) -> None:
        """インベントリからアイテムを装備"""
        if not self.current_character or not self.current_equipment:
            return
        
        # 装備試行
        success, reason, replaced_item = self.current_equipment.equip_item(
            item_instance, slot, self.current_character.character_class.value
        )
        
        if success:
            # インベントリからアイテムを除去
            inventory = self.current_character.get_inventory()
            inventory.remove_item(inventory_index, 1)
            
            # 置き換えられたアイテムがあればインベントリに追加
            if replaced_item:
                if not inventory.add_item(replaced_item):
                    self.show_message("インベントリに空きがないため、外した装備が失われました")
            
            item = item_manager.get_item(item_instance.item_id)
            item_name = item.get_name() if item and item_instance.identified else "アイテム"
            self.show_message(f"{item_name}を装備しました")
            
            # キャラクターステータスを更新
            self.current_character.update_derived_stats()
            
            # 画面を更新
            self.refresh_view()
        else:
            self.show_message(f"装備に失敗: {reason}")

    def unequip_item(self, slot: EquipmentSlot) -> None:
        """アイテムの装備を解除"""
        if not self.current_character or not self.current_equipment:
            return
        
        item_instance = self.current_equipment.unequip_item(slot)
        
        if item_instance:
            inventory = self.current_character.get_inventory()
            if inventory.add_item(item_instance):
                item = item_manager.get_item(item_instance.item_id)
                item_name = item.get_name() if item and item_instance.identified else "アイテム"
                self.show_message(f"{item_name}の装備を解除しました")
                
                # キャラクターステータスを更新
                self.current_character.update_derived_stats()
                
                # 画面を更新
                self.refresh_view()
            else:
                # インベントリに空きがない場合、装備を戻す
                self.current_equipment.equipped_items[slot] = item_instance
                self.show_message("インベントリに空きがありません")

    def show_equipment_bonus(self) -> None:
        """装備ボーナス詳細を表示"""
        if not self.current_equipment:
            return
        
        bonus = self.current_equipment.calculate_equipment_bonus()
        
        details = "【装備ボーナス合計】\\n\\n"
        details += f"筋力: +{bonus.strength}\\n"
        details += f"敏捷性: +{bonus.agility}\\n"
        details += f"知力: +{bonus.intelligence}\\n"
        details += f"信仰: +{bonus.faith}\\n"
        details += f"運: +{bonus.luck}\\n\\n"
        details += f"攻撃力: +{bonus.attack_power}\\n"
        details += f"防御力: +{bonus.defense}\\n"
        details += f"魔法力: +{bonus.magic_power}\\n"
        details += f"魔法抵抗: +{bonus.magic_resistance}\\n\\n"
        details += f"装備重量: {self.current_equipment.get_total_weight():.1f}kg"
        
        self.show_dialog("装備ボーナス", details)

    def show_equipment_effects(self) -> None:
        """装備効果確認を表示"""
        if not self.current_character or not self.current_equipment:
            return
        
        # 装備前後のステータス比較
        original_stats = self.current_character.get_base_stats()
        current_stats = self.current_character.get_derived_stats()
        equipment_bonus = self.current_equipment.calculate_equipment_bonus()
        
        details = "【装備効果確認】\\n\\n"
        details += "ベース → 装備込み (装備効果)\\n\\n"
        
        # 基本ステータス
        details += f"筋力: {original_stats.strength} → {current_stats.strength} (+{equipment_bonus.strength})\\n"
        details += f"敏捷性: {original_stats.agility} → {current_stats.agility} (+{equipment_bonus.agility})\\n"
        details += f"知力: {original_stats.intelligence} → {current_stats.intelligence} (+{equipment_bonus.intelligence})\\n"
        details += f"信仰: {original_stats.faith} → {current_stats.faith} (+{equipment_bonus.faith})\\n"
        details += f"運: {original_stats.luck} → {current_stats.luck} (+{equipment_bonus.luck})\\n\\n"
        
        # 戦闘ステータス
        details += f"攻撃力: {current_stats.attack_power - equipment_bonus.attack_power} → {current_stats.attack_power} (+{equipment_bonus.attack_power})\\n"
        details += f"防御力: {current_stats.defense - equipment_bonus.defense} → {current_stats.defense} (+{equipment_bonus.defense})\\n"
        details += f"魔法力: {current_stats.magic_power - equipment_bonus.magic_power} → {current_stats.magic_power} (+{equipment_bonus.magic_power})\\n"
        details += f"魔法抵抗: {current_stats.magic_resistance - equipment_bonus.magic_resistance} → {current_stats.magic_resistance} (+{equipment_bonus.magic_resistance})"
        
        self.show_dialog("装備効果確認", details)

    def show_party_equipment_stats(self) -> None:
        """パーティ装備統計を表示"""
        if not self.current_party:
            return
        
        stats_text = "【パーティ装備統計】\\n\\n"
        
        total_equipped = 0
        total_slots = 0
        total_weight = 0.0
        total_value = 0
        
        for character in self.current_party.get_all_characters():
            equipment = character.get_equipment()
            summary = equipment.get_equipment_summary()
            
            total_equipped += summary['equipped_count']
            total_slots += len(EquipmentSlot)
            total_weight += summary['total_weight']
            
            # アイテム価値計算
            for item_instance in equipment.get_all_equipped_items().values():
                if item_instance:
                    item = item_manager.get_item(item_instance.item_id)
                    if item:
                        total_value += item.price
        
        stats_text += f"装備率: {total_equipped}/{total_slots} ({int(total_equipped/total_slots*100)}%)\\n"
        stats_text += f"総重量: {total_weight:.1f}kg\\n"
        stats_text += f"総価値: {total_value}G\\n\\n"
        
        # キャラクター別詳細
        stats_text += "【キャラクター別】\\n"
        for character in self.current_party.get_all_characters():
            equipment = character.get_equipment()
            summary = equipment.get_equipment_summary()
            stats_text += f"{character.name}: {summary['equipped_count']}/4 ({summary['total_weight']:.1f}kg)\\n"
        
        self.show_dialog("パーティ装備統計", stats_text)

    def show_dialog(self, title: str, message: str) -> None:
        """ダイアログを表示"""
        # 簡単な実装 - 実際にはより詳細なダイアログウィンドウを作成
        logger.info(f"ダイアログ表示: {title} - {message}")

    def show_message(self, message: str) -> None:
        """メッセージを表示"""
        logger.info(f"メッセージ表示: {message}")

    def refresh_view(self) -> None:
        """ビューを更新"""
        if self.state.value == "shown":
            self._clear_content()
            self._create_content_for_current_mode()

    def _get_slot_display_text(self, slot: EquipmentSlot, item_instance: Optional[ItemInstance]) -> str:
        """スロット表示テキストを取得"""
        if item_instance:
            item = item_manager.get_item(item_instance.item_id)
            if item:
                if item_instance.identified:
                    item_name = item.get_name()
                    condition_text = f" ({int(item_instance.condition * 100)}%)"
                else:
                    item_name = f"未鑑定の{item.item_type.value}"
                    condition_text = ""
                
                return f"{self._get_slot_name(slot)}: {item_name}{condition_text}"
            else:
                return f"{self._get_slot_name(slot)}: 不明なアイテム"
        else:
            return f"{self._get_slot_name(slot)}: (なし)"

    def _get_item_display_text(self, item_instance: ItemInstance, item: Item, slot: EquipmentSlot) -> str:
        """アイテム表示テキストを取得"""
        if item_instance.identified:
            item_name = item.get_name()
            preview_text = self._get_equipment_preview(item, item_instance, slot)
            return f"{item_name} {preview_text}"
        else:
            return f"未鑑定の{item.item_type.value}"

    def _get_suitable_items_for_slot(self, slot: EquipmentSlot) -> List[tuple]:
        """スロットに装備可能なアイテムリストを取得"""
        if not self.current_character:
            return []
        
        suitable_items = []
        inventory = self.current_character.get_inventory()
        
        for i, inventory_slot in enumerate(inventory.slots):
            if not inventory_slot.is_empty():
                item_instance = inventory_slot.item_instance
                item = item_manager.get_item(item_instance.item_id)
                
                if item and self._can_equip_in_slot(item, slot):
                    can_equip, reason = self.current_equipment.can_equip_item(
                        item_instance, slot, self.current_character.character_class.value
                    )
                    
                    if can_equip:
                        suitable_items.append((i, item_instance, item))
        
        return suitable_items

    def _can_equip_in_slot(self, item: Item, slot: EquipmentSlot) -> bool:
        """アイテムがスロットに装備可能かチェック"""
        if slot == EquipmentSlot.WEAPON:
            return item.is_weapon()
        elif slot == EquipmentSlot.ARMOR:
            return item.is_armor()
        elif slot in [EquipmentSlot.ACCESSORY_1, EquipmentSlot.ACCESSORY_2]:
            return item.item_type.value == "treasure"
        return False

    def _get_equipment_preview(self, item: Item, item_instance: ItemInstance, slot: EquipmentSlot) -> str:
        """装備効果プレビューを取得"""
        if not item_instance.identified:
            return ""
        
        preview = ""
        
        if item.is_weapon():
            attack_power = int(item.get_attack_power() * item_instance.condition)
            current_item = self.current_equipment.get_equipped_item(slot)
            
            if current_item:
                current_attack = 0
                current_item_data = item_manager.get_item(current_item.item_id)
                if current_item_data and current_item_data.is_weapon():
                    current_attack = int(current_item_data.get_attack_power() * current_item.condition)
                
                diff = attack_power - current_attack
                if diff > 0:
                    preview = f"(+{diff})"
                elif diff < 0:
                    preview = f"({diff})"
            else:
                preview = f"(+{attack_power})"
                
        elif item.is_armor():
            defense = int(item.get_defense() * item_instance.condition)
            current_item = self.current_equipment.get_equipped_item(slot)
            
            if current_item:
                current_defense = 0
                current_item_data = item_manager.get_item(current_item.item_id)
                if current_item_data and current_item_data.is_armor():
                    current_defense = int(current_item_data.get_defense() * current_item.condition)
                
                diff = defense - current_defense
                if diff > 0:
                    preview = f"(+{diff})"
                elif diff < 0:
                    preview = f"({diff})"
            else:
                preview = f"(+{defense})"
        
        return preview

    def _get_slot_name(self, slot: EquipmentSlot) -> str:
        """スロット名を取得"""
        slot_names = {
            EquipmentSlot.WEAPON: "武器",
            EquipmentSlot.ARMOR: "防具",
            EquipmentSlot.ACCESSORY_1: "アクセサリ1",
            EquipmentSlot.ACCESSORY_2: "アクセサリ2"
        }
        return slot_names.get(slot, slot.value)

    def _clear_content(self) -> None:
        """コンテンツをクリア"""
        for element_id, element in list(self.ui_elements.items()):
            if element_id != "main_panel":  # メインパネルは残す
                element.kill()
                del self.ui_elements[element_id]

    def set_close_callback(self, callback: Callable) -> None:
        """閉じるコールバックを設定"""
        self.callback_on_close = callback

    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベントを処理"""
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            return self._handle_button_press(event)
        return False

    def _handle_button_press(self, event: pygame.event.Event) -> bool:
        """ボタン押下イベントを処理"""
        element_id = getattr(event.ui_object_id, 'object_id', '') if hasattr(event, 'ui_object_id') else ''
        
        # パーティ概要でのボタン処理
        if self.current_mode == EquipmentViewMode.PARTY_OVERVIEW:
            if element_id.startswith('char_button_'):
                index = int(element_id.split('_')[-1])
                characters = self.current_party.get_all_characters()
                if 0 <= index < len(characters):
                    self.show_character_equipment(characters[index])
                    return True
            elif element_id == 'party_stats_button':
                self.show_party_equipment_stats()
                return True
            elif element_id == 'close_button':
                self.hide()
                if self.callback_on_close:
                    self.callback_on_close()
                return True
        
        # キャラクター装備でのボタン処理
        elif self.current_mode == EquipmentViewMode.CHARACTER_EQUIPMENT:
            if element_id.startswith('slot_button_'):
                slot_value = element_id.split('_')[-1]
                slot = EquipmentSlot(slot_value)
                self.show_slot_options(slot)
                return True
            elif element_id == 'bonus_button':
                self.show_equipment_bonus()
                return True
            elif element_id == 'effects_button':
                self.show_equipment_effects()
                return True
            elif element_id == 'back_button':
                self.show_party_equipment_overview()
                return True
        
        # スロットオプションでのボタン処理
        elif self.current_mode == EquipmentViewMode.SLOT_OPTIONS:
            if element_id == 'detail_button':
                # アイテム詳細を表示（実装は省略）
                return True
            elif element_id == 'unequip_button':
                self.unequip_item(self.selected_slot)
                return True
            elif element_id == 'change_button':
                self.show_equipment_selection(self.selected_slot)
                return True
            elif element_id == 'back_button':
                self.show_character_equipment(self.current_character)
                return True
        
        # 装備選択でのボタン処理
        elif self.current_mode == EquipmentViewMode.EQUIPMENT_SELECTION:
            if element_id.startswith('item_button_'):
                inventory_index = int(element_id.split('_')[-1])
                suitable_items = self._get_suitable_items_for_slot(self.selected_slot)
                for inv_idx, item_instance, item in suitable_items:
                    if inv_idx == inventory_index:
                        self.equip_item_from_inventory(item_instance, self.selected_slot, inventory_index)
                        break
                return True
            elif element_id == 'cancel_button':
                self.show_slot_options(self.selected_slot)
                return True
        
        return False

    def destroy(self) -> None:
        """ウィンドウを破棄"""
        self._clear_content()
        
        if self.content_panel:
            self.content_panel.kill()
            self.content_panel = None
        
        self.current_party = None
        self.current_character = None
        self.current_equipment = None
        self.selected_slot = None
        self.comparison_item = None
        
        super().destroy()
        logger.debug(f"EquipmentWindowを破棄: {self.window_id}")

    def on_show(self) -> None:
        """表示時の処理"""
        logger.debug(f"EquipmentWindowを表示: {self.window_id}")

    def on_hide(self) -> None:
        """非表示時の処理"""
        logger.debug(f"EquipmentWindowを非表示: {self.window_id}")

    def on_update(self, time_delta: float) -> None:
        """更新処理"""
        pass