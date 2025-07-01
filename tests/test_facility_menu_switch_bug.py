"""
Test for facility menu switching bug (Issue #0057)

This test reproduces the bug where:
[inn] -> [exit] -> [guild] displays inn menu instead of guild menu
"""

import pytest
from unittest.mock import Mock, patch
from src.overworld.base_facility import facility_manager
from src.overworld.facilities.inn import Inn
from src.overworld.facilities.guild import AdventurersGuild
from src.ui.window_system.window_manager import WindowManager


class TestFacilityMenuSwitchBug:
    """Test facility menu switching to ensure different menus are displayed correctly"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_window_manager = Mock(spec=WindowManager)
        
        # Create facility instances
        self.inn = Inn()
        self.guild = AdventurersGuild()
    
    def test_inn_then_guild_shows_different_menus(self):
        """
        Test that switching from inn to guild shows different menu configurations
        
        Bug scenario:
        1. Enter inn -> shows inn menu
        2. Exit inn -> return to overworld  
        3. Enter guild -> should show guild menu, not inn menu
        """
        
        # Step 1: Enter inn
        self.inn.enter()
        
        # Verify inn menu window was created
        inn_calls = [call for call in self.mock_window_manager.show_window.call_args_list 
                    if 'inn' in str(call)]
        assert len(inn_calls) > 0, "Inn window should be created when entering inn"
        
        # Get the inn menu configuration
        inn_window_call = inn_calls[0]
        inn_window_args = inn_window_call[0] if inn_window_call[0] else inn_window_call[1]
        
        # Step 2: Exit inn (simulate window close)
        self.inn.exit()
        
        # Step 3: Enter guild  
        self.guild.enter()
        
        # Verify guild menu window was created
        guild_calls = [call for call in self.mock_window_manager.show_window.call_args_list 
                      if 'guild' in str(call)]
        assert len(guild_calls) > 0, "Guild window should be created when entering guild"
        
        # Get the guild menu configuration
        guild_window_call = guild_calls[0]
        guild_window_args = guild_window_call[0] if guild_window_call[0] else guild_window_call[1]
        
        # Verify different window IDs are used
        # This should prevent the same menu from being reused
        assert inn_window_args != guild_window_args, \
            "Inn and guild should use different window configurations"
    
    def test_facility_menu_configurations_are_different(self):
        """Test that inn and guild have different menu configurations"""
        
        # Get inn menu config
        inn_config = self.inn._create_inn_menu_config()
        
        # Get guild menu config  
        guild_config = self.guild._create_guild_menu_config()
        
        print(f"Inn config: {inn_config}")
        print(f"Guild config: {guild_config}")
        
        # Verify configs are different
        assert inn_config != guild_config, \
            "Inn and guild should have different menu configurations"
        
        # Verify specific menu items are different
        inn_buttons = inn_config.get('buttons', inn_config.get('menu_items', []))
        guild_buttons = guild_config.get('buttons', guild_config.get('menu_items', []))
        
        inn_button_texts = [btn.get('text', btn.get('label', '')) for btn in inn_buttons]
        guild_button_texts = [btn.get('text', btn.get('label', '')) for btn in guild_buttons]
        
        print(f"Inn button texts: {inn_button_texts}")
        print(f"Guild button texts: {guild_button_texts}")
        
        # Should have at least some different menu items
        assert inn_button_texts != guild_button_texts, \
            "Inn and guild should have different menu button texts"
    
    def test_window_manager_creates_unique_window_ids(self):
        """Test that each facility creates windows with unique IDs"""
        
        # Enter inn
        self.inn.enter()
        
        # Enter guild (without explicitly exiting inn first)
        self.guild.enter()
        
        # Check all window creation calls
        show_window_calls = self.mock_window_manager.show_window.call_args_list
        
        # Extract window IDs from calls
        window_ids = []
        for call in show_window_calls:
            # Window ID should be the first argument or in kwargs
            if call[0]:  # positional args
                if hasattr(call[0][0], 'id'):
                    window_ids.append(call[0][0].id)
            elif 'window' in call[1]:  # keyword args
                if hasattr(call[1]['window'], 'id'):
                    window_ids.append(call[1]['window'].id)
        
        # Verify unique window IDs
        unique_ids = set(window_ids)
        assert len(unique_ids) == len(window_ids), \
            f"All window IDs should be unique. Found: {window_ids}"
    
    def test_facility_exit_clears_window_state(self):
        """Test that exiting a facility properly clears its window state"""
        
        # Enter inn
        self.inn.enter()
        
        # Verify inn window was shown
        assert self.mock_window_manager.show_window.called, \
            "Window should be shown when entering facility"
        
        # Exit inn
        self.inn.exit()
        
        # Verify window manager was called to close/hide window
        # This could be close_window, hide_window, or pop_window depending on implementation
        close_methods = ['close_window', 'hide_window', 'pop_window', 'remove_window']
        close_called = any(getattr(self.mock_window_manager, method).called 
                          for method in close_methods 
                          if hasattr(self.mock_window_manager, method))
        
        assert close_called, \
            "Window manager should close/hide window when exiting facility"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])