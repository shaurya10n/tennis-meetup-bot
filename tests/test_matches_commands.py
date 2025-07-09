"""Test script to verify matches commands are properly registered."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_matches_command_import():
    """Test that matches command can be imported."""
    try:
        from src.cogs.user.commands.matches.command import MatchesCommand
        print("✅ MatchesCommand imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import MatchesCommand: {e}")
        return False

def test_matches_constants_import():
    """Test that matches constants can be imported."""
    try:
        from src.cogs.user.commands.matches.constants import (
            MATCHES_VIEW_COMPLETED_DESC, 
            MATCHES_VIEW_UPCOMING_DESC,
            MATCHES_COMPLETE_DESC, 
            MATCH_NOT_FOUND
        )
        print("✅ Matches constants imported successfully")
        print(f"✅ MATCHES_VIEW_COMPLETED_DESC: {MATCHES_VIEW_COMPLETED_DESC}")
        print(f"✅ MATCHES_VIEW_UPCOMING_DESC: {MATCHES_VIEW_UPCOMING_DESC}")
        print(f"✅ MATCHES_COMPLETE_DESC: {MATCHES_COMPLETE_DESC}")
        print(f"✅ MATCH_NOT_FOUND: {MATCH_NOT_FOUND}")
        return True
    except Exception as e:
        print(f"❌ Failed to import matches constants: {e}")
        return False

def test_matches_views_import():
    """Test that matches views can be imported."""
    try:
        from src.cogs.user.commands.matches.views import (
            CompleteMatchModal,
            create_match_embed,
            create_match_completion_embed
        )
        print("✅ Matches views imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import matches views: {e}")
        return False

def test_file_structure():
    """Test that all required files exist."""
    files_to_check = [
        "src/cogs/user/commands/matches/__init__.py",
        "src/cogs/user/commands/matches/command.py",
        "src/cogs/user/commands/matches/constants.py",
        "src/cogs/user/commands/matches/views.py"
    ]
    
    all_exist = True
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            all_exist = False
    
    return all_exist

def test_wrapper_integration():
    """Test that matches commands are integrated into the wrapper."""
    try:
        # Check if the wrapper file contains the necessary imports
        wrapper_path = "src/cogs/user/commands/wrapper.py"
        if not os.path.exists(wrapper_path):
            print(f"❌ {wrapper_path} not found")
            return False
        
        with open(wrapper_path, 'r') as f:
            content = f.read()
        
        required_imports = [
            "from .matches.command import MatchesCommand",
            "from .matches.constants import MATCHES_VIEW_COMPLETED_DESC, MATCHES_VIEW_UPCOMING_DESC, MATCHES_COMPLETE_DESC"
        ]
        
        all_imports_found = True
        for import_line in required_imports:
            if import_line in content:
                print(f"✅ Found import: {import_line}")
            else:
                print(f"❌ Missing import: {import_line}")
                all_imports_found = False
        
        # Check for command registration
        required_commands = [
            "@nextcord.slash_command(\n        name=\"matches\"",
            "@matches.subcommand(\n        name=\"view-completed\"",
            "@matches.subcommand(\n        name=\"view-upcoming\"",
            "@matches.subcommand(\n        name=\"complete\""
        ]
        
        all_commands_found = True
        for command in required_commands:
            if command in content:
                print(f"✅ Found command: {command.split('name=')[1].split(',')[0]}")
            else:
                print(f"❌ Missing command: {command.split('name=')[1].split(',')[0]}")
                all_commands_found = False
        
        return all_imports_found and all_commands_found
        
    except Exception as e:
        print(f"❌ Failed to check wrapper integration: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Matches Commands Registration")
    print("=" * 50)
    
    # Test file structure
    print("📁 Testing file structure:")
    test_file_structure()
    print()
    
    # Test imports
    print("📦 Testing imports:")
    test_matches_constants_import()
    print()
    test_matches_views_import()
    print()
    test_matches_command_import()
    print()
    
    # Test wrapper integration
    print("🔗 Testing wrapper integration:")
    test_wrapper_integration()
    print()
    
    print("✅ All matches command tests completed!")

if __name__ == "__main__":
    main() 