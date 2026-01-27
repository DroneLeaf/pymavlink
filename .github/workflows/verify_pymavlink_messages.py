#!/usr/bin/env python3
"""
Verify that all required pymavlink messages and constants exist.

This script loads the required_pymavlink_messages.json configuration file
and verifies that all specified imports, dialects, messages, enums, and
constants are available in the installed pymavlink package.

Usage:
    python verify_pymavlink_messages.py [--config CONFIG_PATH] [--verbose]

Exit codes:
    0: All required symbols found
    1: Some required symbols missing
    2: Configuration file error
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load the configuration file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Configuration file not found: {config_path}")
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in configuration file: {e}")
        sys.exit(2)


def verify_import(module_path: str, verbose: bool = False) -> Tuple[bool, Any]:
    """Try to import a module and return success status and module.
    
    Uses importlib to properly import submodules (e.g., pymavlink.mavutil)
    which may not be accessible as attributes of the parent module.
    """
    try:
        import importlib
        module = importlib.import_module(module_path)
        if verbose:
            print(f"  ✓ {module_path}")
        return True, module
    except (ImportError, ModuleNotFoundError) as e:
        print(f"  ✗ {module_path}: {e}")
        return False, None


def verify_attribute(module: Any, attr_name: str, module_path: str, verbose: bool = False) -> bool:
    """Verify that an attribute exists on a module."""
    if hasattr(module, attr_name):
        if verbose:
            print(f"    ✓ {module_path}.{attr_name}")
        return True
    else:
        print(f"    ✗ {module_path}.{attr_name} NOT FOUND")
        return False


def verify_imports(config: Dict[str, Any], verbose: bool = False) -> Tuple[int, int]:
    """Verify all basic imports."""
    print("\n=== Verifying Basic Imports ===")
    success = 0
    failed = 0
    
    imports = config.get("imports", {})
    for module_path, details in imports.items():
        is_optional = details.get("optional", False)
        ok, module = verify_import(module_path, verbose)
        if ok:
            success += 1
            # Check required attributes
            for attr in details.get("required_attributes", []):
                if verify_attribute(module, attr, module_path, verbose):
                    success += 1
                else:
                    failed += 1
        else:
            if is_optional:
                print(f"    (optional - skipped)")
            else:
                failed += 1
    
    return success, failed

def verify_dialects(config: Dict[str, Any], verbose: bool = False) -> Tuple[int, int]:
    """Verify all dialect imports and their contents."""
    print("\n=== Verifying Dialects ===")
    success = 0
    failed = 0
    
    dialects = config.get("dialects", {})
    for dialect_path, details in dialects.items():
        print(f"\n  Dialect: {dialect_path}")
        ok, module = verify_import(dialect_path, verbose)
        if not ok:
            failed += 1
            continue
        success += 1
        
        # Check messages (legacy format - list directly)
        for msg_id in details.get("messages", []) + details.get("custom_messages", []):
            if verify_attribute(module, msg_id, dialect_path, verbose):
                success += 1
            else:
                failed += 1
        
        # Check message_ids (new format - dict with "items" key)
        message_ids = details.get("message_ids", {})
        if isinstance(message_ids, dict):
            for msg_id in message_ids.get("items", []):
                if verify_attribute(module, msg_id, dialect_path, verbose):
                    success += 1
                else:
                    failed += 1
        
        # Check message classes (legacy format - list directly)
        msg_classes = details.get("message_classes", [])
        if isinstance(msg_classes, list):
            for msg_class in msg_classes:
                if verify_attribute(module, msg_class, dialect_path, verbose):
                    success += 1
                else:
                    failed += 1
        # Check message classes (new format - dict with "items" key)
        elif isinstance(msg_classes, dict):
            for msg_class in msg_classes.get("items", []):
                if verify_attribute(module, msg_class, dialect_path, verbose):
                    success += 1
                else:
                    failed += 1
        
        # Check constants (legacy format - list directly)
        consts = details.get("constants", [])
        if isinstance(consts, list):
            for const in consts:
                if verify_attribute(module, const, dialect_path, verbose):
                    success += 1
                else:
                    failed += 1
        # Check constants (new format - dict with "items" key)
        elif isinstance(consts, dict):
            for const in consts.get("items", []):
                if verify_attribute(module, const, dialect_path, verbose):
                    success += 1
                else:
                    failed += 1
        
        # Check required_attributes (new format) or attributes (legacy)
        for attr in details.get("required_attributes", []) + details.get("attributes", []):
            if verify_attribute(module, attr, dialect_path, verbose):
                success += 1
            else:
                failed += 1
        
        # Check enums
        enums = details.get("enums", {})
        if enums and hasattr(module, 'enums'):
            for enum_name, enum_values in enums.items():
                # Skip comment keys
                if enum_name.startswith("_"):
                    continue
                if enum_name in module.enums:
                    if verbose:
                        print(f"    ✓ enum {enum_name}")
                    success += 1
                    # Check individual enum values as module constants
                    for value in enum_values:
                        if verify_attribute(module, value, dialect_path, verbose):
                            success += 1
                        else:
                            failed += 1
                else:
                    print(f"    ✗ enum {enum_name} NOT FOUND")
                    failed += 1
    
    return success, failed


def verify_mavutil_mavlink(config: Dict[str, Any], verbose: bool = False) -> Tuple[int, int]:
    """Verify mavutil.mavlink constants."""
    print("\n=== Verifying mavutil.mavlink Constants ===")
    success = 0
    failed = 0
    
    try:
        from pymavlink import mavutil
        mavlink = mavutil.mavlink
    except (ImportError, AttributeError) as e:
        print(f"  ✗ Cannot import pymavlink.mavutil.mavlink: {e}")
        return 0, 1
    
    constants = config.get("mavutil_mavlink_constants", {})
    
    # Flatten all constant lists
    all_constants: List[str] = []
    for category, items in constants.items():
        if category == "description":
            continue
        if isinstance(items, list):
            all_constants.extend(items)
    
    for const in all_constants:
        if hasattr(mavlink, const):
            if verbose:
                print(f"  ✓ mavutil.mavlink.{const}")
            success += 1
        else:
            print(f"  ✗ mavutil.mavlink.{const} NOT FOUND")
            failed += 1
    
    return success, failed


def main():
    parser = argparse.ArgumentParser(
        description="Verify pymavlink messages and constants exist"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).parent / "required_pymavlink_messages.json",
        help="Path to the configuration JSON file"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show all checks, not just failures"
    )
    args = parser.parse_args()
    
    print("=" * 60)
    print("PyMAVLink Message Verification")
    print("=" * 60)
    
    config = load_config(args.config)
    
    total_success = 0
    total_failed = 0
    
    # Verify basic imports
    s, f = verify_imports(config, args.verbose)
    total_success += s
    total_failed += f
    
    # Verify dialects
    s, f = verify_dialects(config, args.verbose)
    total_success += s
    total_failed += f
    
    # Verify mavutil.mavlink constants
    s, f = verify_mavutil_mavlink(config, args.verbose)
    total_success += s
    total_failed += f
    
    # Summary
    print("\n" + "=" * 60)
    print(f"SUMMARY: {total_success} passed, {total_failed} failed")
    print("=" * 60)
    
    if total_failed > 0:
        print("\n❌ VERIFICATION FAILED")
        print("Some required pymavlink symbols are missing.")
        print("Please update message_definitions or fix the configuration.")
        sys.exit(1)
    else:
        print("\n✅ VERIFICATION PASSED")
        print("All required pymavlink symbols are available.")
        sys.exit(0)


if __name__ == "__main__":
    main()
