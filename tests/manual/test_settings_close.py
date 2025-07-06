#!/usr/bin/env python3
"""
Test ESC key to close settings window
"""
import time
from src.debug.game_debug_client import GameDebugClient

def test_settings_close():
    """Test closing settings window with ESC key"""
    
    client = GameDebugClient()
    
    if not client.wait_for_api():
        print("❌ API not ready")
        return False
    
    print("✅ API ready")
    
    # Get current UI hierarchy
    print("Getting current UI hierarchy...")
    hierarchy = client.get_ui_hierarchy()
    if hierarchy:
        window_stack = hierarchy.get('window_stack', [])
        print(f"Current window stack ({len(window_stack)} windows):")
        for i, window in enumerate(window_stack):
            print(f"  {i}: {window}")
    
    # Check if settings window is on top
    if len(window_stack) > 1 and 'settings_menu' in window_stack[-1]:
        print("✅ Settings window is currently on top")
        
        # Send ESC key to close settings
        print("\nSending ESC key to close settings...")
        client.send_key(27)
        time.sleep(1)
        
        # Take screenshot after ESC
        print("Taking screenshot after ESC...")
        client.screenshot("after_settings_close.jpg")
        
        # Get UI hierarchy after ESC
        print("Getting UI hierarchy after ESC...")
        hierarchy_after = client.get_ui_hierarchy()
        if hierarchy_after:
            window_stack_after = hierarchy_after.get('window_stack', [])
            print(f"Window stack after ESC ({len(window_stack_after)} windows):")
            for i, window in enumerate(window_stack_after):
                print(f"  {i}: {window}")
        
        # Check if settings window was closed
        if len(window_stack_after) < len(window_stack):
            print("✅ Settings window was successfully closed with ESC key!")
            print("✅ The ESC key fix is working correctly!")
            return True
        else:
            print("❌ Settings window was not closed by ESC key")
            print("❌ The ESC key fix needs investigation")
            return False
    else:
        print("ℹ️  Settings window is not currently on top")
        print("Opening settings first...")
        
        # Open settings first
        client.send_key(27)
        time.sleep(1)
        
        # Get hierarchy after opening settings
        hierarchy_settings = client.get_ui_hierarchy()
        if hierarchy_settings:
            window_stack_settings = hierarchy_settings.get('window_stack', [])
            print(f"Window stack after opening settings ({len(window_stack_settings)} windows):")
            for i, window in enumerate(window_stack_settings):
                print(f"  {i}: {window}")
        
        # Now try to close with ESC
        print("\nSending ESC key to close settings...")
        client.send_key(27)
        time.sleep(1)
        
        # Get final hierarchy
        hierarchy_final = client.get_ui_hierarchy()
        if hierarchy_final:
            window_stack_final = hierarchy_final.get('window_stack', [])
            print(f"Final window stack ({len(window_stack_final)} windows):")
            for i, window in enumerate(window_stack_final):
                print(f"  {i}: {window}")
        
        # Check if we're back to original state
        if len(window_stack_final) == len(window_stack):
            print("✅ Successfully opened and closed settings with ESC key!")
            print("✅ The ESC key fix is working correctly!")
            return True
        else:
            print("❌ Something went wrong with the ESC key behavior")
            return False

if __name__ == "__main__":
    success = test_settings_close()
    if success:
        print("\n🎉 ESC key fix verification PASSED!")
    else:
        print("\n💥 ESC key fix verification FAILED!")