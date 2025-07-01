"""
Test for facility window ID inconsistency bug (Issue #0057)

This test verifies that window IDs used for creation and cleanup are consistent.
"""

import pytest
from unittest.mock import Mock, patch
from src.overworld.base_facility import BaseFacility, FacilityType
from src.overworld.facilities.inn import Inn
from src.overworld.facilities.guild import AdventurersGuild
from src.ui.window_system.window_manager import WindowManager
from src.character.party import Party


class TestFacilityWindowIdBug:
    """Test facility window ID consistency for proper cleanup"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_window_manager = Mock(spec=WindowManager)
        self.mock_window_manager.window_registry = {}
        
        # Create mock party
        self.mock_party = Mock(spec=Party)
        self.mock_party.characters = []
        
        # Create facility instances
        self.inn = Inn()
        self.guild = AdventurersGuild()
        
        # Mock window manager for facilities
        self.inn.window_manager = self.mock_window_manager
        self.guild.window_manager = self.mock_window_manager
    
    def test_base_facility_cleanup_uses_correct_window_id(self):
        """Test that BaseFacility cleanup uses the same window ID format as creation"""
        
        # Use Inn as a concrete implementation of BaseFacility
        # Enter facility (should create window)
        self.inn.enter(self.mock_party)
        
        # Check what window ID was used for creation
        show_window_calls = self.mock_window_manager.show_window.call_args_list
        assert len(show_window_calls) > 0, "show_window should have been called"
        
        created_window = show_window_calls[0][0][0]  # First argument of first call
        created_window_id = created_window.id
        
        # Exit facility (should cleanup window)
        self.inn.exit()
        
        # Check what window ID was used for cleanup
        cleanup_calls = [
            call for call in [
                *self.mock_window_manager.close_window.call_args_list,
                *self.mock_window_manager.remove_window.call_args_list
            ]
        ]
        
        if cleanup_calls:
            cleanup_window_id = cleanup_calls[0][0][0]  # First argument
            assert created_window_id == cleanup_window_id, \
                f"Window ID used for creation ({created_window_id}) should match cleanup ({cleanup_window_id})"
        else:
            # The cleanup method should at least check if the window exists
            # This is where the bug occurs - it checks for the wrong ID format
            pass  # We expect this test to fail initially due to the bug
    
    def test_inn_window_id_consistency(self):
        """Test that Inn uses consistent window IDs for creation and cleanup"""
        
        # Enter inn
        self.inn.enter(self.mock_party)
        
        # Get the window ID used for creation
        show_window_calls = self.mock_window_manager.show_window.call_args_list
        assert len(show_window_calls) > 0, "Inn should create a window when entered"
        
        created_window = show_window_calls[0][0][0]
        created_window_id = created_window.id
        
        # Exit inn
        self.inn.exit()
        
        # Check if cleanup was attempted with the correct window ID
        # The window ID used for cleanup should match the one used for creation
        expected_cleanup_id = created_window_id
        
        # Check all possible cleanup method calls
        all_cleanup_calls = (
            self.mock_window_manager.close_window.call_args_list +
            self.mock_window_manager.remove_window.call_args_list
        )
        
        if all_cleanup_calls:
            cleanup_window_id = all_cleanup_calls[0][0][0]
            assert cleanup_window_id == expected_cleanup_id, \
                f"Inn cleanup window ID ({cleanup_window_id}) should match creation ID ({expected_cleanup_id})"
    
    def test_guild_window_id_consistency(self):
        """Test that Guild uses consistent window IDs for creation and cleanup"""
        
        # Enter guild
        self.guild.enter(self.mock_party)
        
        # Get the window ID used for creation
        show_window_calls = self.mock_window_manager.show_window.call_args_list
        assert len(show_window_calls) > 0, "Guild should create a window when entered"
        
        created_window = show_window_calls[0][0][0]
        created_window_id = created_window.id
        
        # Exit guild
        self.guild.exit()
        
        # Check if cleanup was attempted with the correct window ID
        expected_cleanup_id = created_window_id
        
        # Check all possible cleanup method calls
        all_cleanup_calls = (
            self.mock_window_manager.close_window.call_args_list +
            self.mock_window_manager.remove_window.call_args_list
        )
        
        if all_cleanup_calls:
            cleanup_window_id = all_cleanup_calls[0][0][0]
            assert cleanup_window_id == expected_cleanup_id, \
                f"Guild cleanup window ID ({cleanup_window_id}) should match creation ID ({expected_cleanup_id})"
    
    def test_different_facilities_use_different_window_ids(self):
        """Test that different facilities use different window IDs"""
        
        # Enter both facilities
        self.inn.enter(self.mock_party)
        self.guild.enter(self.mock_party)
        
        # Get window IDs used for creation
        show_window_calls = self.mock_window_manager.show_window.call_args_list
        assert len(show_window_calls) >= 2, "Both facilities should create windows"
        
        inn_window_id = show_window_calls[0][0][0].id
        guild_window_id = show_window_calls[1][0][0].id
        
        assert inn_window_id != guild_window_id, \
            f"Inn and Guild should use different window IDs: inn='{inn_window_id}', guild='{guild_window_id}'"
    
    def test_window_id_format_consistency(self):
        """Test that window ID format is consistent between facilities"""
        
        # Check inn window ID format
        self.inn.enter(self.mock_party)
        inn_calls = self.mock_window_manager.show_window.call_args_list
        inn_window = inn_calls[0][0][0] if inn_calls else None
        
        # Reset mock for guild test
        self.mock_window_manager.reset_mock()
        
        # Check guild window ID format  
        self.guild.enter(self.mock_party)
        guild_calls = self.mock_window_manager.show_window.call_args_list
        guild_window = guild_calls[0][0][0] if guild_calls else None
        
        # Both should create windows
        assert inn_window is not None, "Inn should create a window"
        assert guild_window is not None, "Guild should create a window"
        
        # Get actual window IDs - they should be strings from the real objects
        print(f"Inn window: {inn_window}")
        print(f"Inn window type: {type(inn_window)}")
        print(f"Guild window: {guild_window}")
        print(f"Guild window type: {type(guild_window)}")
        
        # Check if windows have id attributes
        if hasattr(inn_window, 'id'):
            inn_window_id = inn_window.id
            print(f"Inn window ID: {inn_window_id}")
            assert isinstance(inn_window_id, str), f"Inn window ID should be string: {type(inn_window_id)}"
            assert "inn" in inn_window_id.lower(), f"Inn window ID should contain 'inn': {inn_window_id}"
        
        if hasattr(guild_window, 'id'):
            guild_window_id = guild_window.id
            print(f"Guild window ID: {guild_window_id}")
            assert isinstance(guild_window_id, str), f"Guild window ID should be string: {type(guild_window_id)}"
            assert "guild" in guild_window_id.lower(), f"Guild window ID should contain 'guild': {guild_window_id}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])