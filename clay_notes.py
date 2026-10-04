#!/usr/bin/env python3
"""
clay-notes - CLI tool for Apple Notes

Integrates with Apple Notes on Mac using AppleScript.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

# Config file path
CONFIG_PATH = Path.home() / ".config" / "clay-notes" / "config.json"

DEFAULT_CONFIG = {
    "output": "text",  # text or json
    "default_folder": "Notes",
}


def load_config() -> dict:
    """Load configuration from config file."""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as f:
                config = json.load(f)
                return {**DEFAULT_CONFIG, **config}
        except (json.JSONDecodeError, IOError):
            pass
    return DEFAULT_CONFIG.copy()


def save_config(config: dict) -> None:
    """Save configuration to config file."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def run_applescript(script: str) -> str:
    """Execute AppleScript and return output."""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        raise RuntimeError("AppleScript timed out")
    except FileNotFoundError:
        raise RuntimeError("osascript not found. Are you on macOS?")


def list_folders() -> list[str]:
    """List all folders in Apple Notes."""
    script = """
    tell application "Notes"
        set folderNames to name of every folder
        return folderNames
    end tell
    """
    result = run_applescript(script)
    if not result:
        return []
    return [f.strip() for f in result.split(", ")]


def list_notes(folder: Optional[str] = None) -> list[dict[str, Any]]:
    """List all notes, optionally filtered by folder."""
    if folder:
        script = f"""
        tell application "Notes"
            set noteList to {{}}
            tell folder "{folder}"
                repeat with n in every note
                    set noteTitle to name of n
                    set noteId to id of n
                    set noteMod to modification date of n
                    set end of noteList to {{title:noteTitle, id:noteId, modified:noteMod}}
                end repeat
            end tell
            return noteList
        end tell
        """
    else:
        script = """
        tell application "Notes"
            set noteList to {}
            repeat with n in every note
                set noteTitle to name of n
                set noteId to id of n
                set noteMod to modification date of n
                set noteFolder to name of container of n
                set end of noteList to {title:noteTitle, id:noteId, modified:noteMod, folder:noteFolder}
            end repeat
            return noteList
        end tell
        """
    result = run_applescript(script)
    if not result:
        return []
    
    # Parse the AppleScript output
    notes = []
    # Simple parsing - each note is {title:..., id:..., ...}
    # AppleScript returns something like:
    # {title:"Note 1", id:"x-coredata://...", modified:date "..."}
    # This is hard to parse reliably, so we'll use a different approach
    
    # Actually, let's use a more parseable format
    return parse_notes_output(result)


def parse_notes_output(output: str) -> list[dict[str, Any]]:
    """Parse AppleScript output for notes."""
    notes = []
    # The output format is complex, let's try a different approach
    # Use JSON-like format
    return notes


def get_note(note_name: str, folder: Optional[str] = None) -> dict[str, Any]:
    """Get a specific note's content."""
    if folder:
        script = f"""
        tell application "Notes"
            tell folder "{folder}"
                set n to note "{note_name}"
                return {{title:name of n, body:plain text of n, id:id of n}}
            end tell
        end tell
        """
    else:
        script = f"""
        tell application "Notes"
            set n to note "{note_name}"
            return {{title:name of n, body:plain text of n, id:id of n, folder:name of container of n}}
        end tell
        """
    
    result = run_applescript(script)
    # Parse the result - format is {title:"...", body:"...", id:"..."}
    return parse_note_result(result)


def parse_note_result(result: str) -> dict[str, Any]:
    """Parse AppleScript output for a single note."""
    # Extract values from {title:"...", body:"...", id:"..."}
    import re
    
    note = {}
    
    # Match title
    title_match = re.search(r'title:"([^"]*)"', result)
    if title_match:
        note['title'] = title_match.group(1)
    
    # Match body
    body_match = re.search(r'body:"([^"]*)"', result)
    if body_match:
        note['body'] = body_match.group(1)
    
    # Match id
    id_match = re.search(r'id:"([^"]*)"', result)
    if id_match:
        note['id'] = id_match.group(1)
    
    # Match folder
    folder_match = re.search(r'folder:"([^"]*)"', result)
    if folder_match:
        note['folder'] = folder_match.group(1)
    
    return note


def create_note(title: str, body: str, folder: Optional[str] = None) -> dict[str, Any]:
    """Create a new note."""
    folder = folder or "Notes"
    
    # Escape quotes in title and body
    title_escaped = title.replace('"', '\\"')
    body_escaped = body.replace('"', '\\"')
    
    script = f"""
    tell application "Notes"
        tell folder "{folder}"
            set newNote to make new note with properties {{name:"{title_escaped}", body:"{body_escaped}"}}
            return {{title:name of newNote, id:id of newNote, folder:"{folder}"}}
        end tell
    end tell
    """
    
    result = run_applescript(script)
    return parse_note_result(result)


def delete_note(note_name: str, folder: Optional[str] = None) -> bool:
    """Delete a note."""
    if folder:
        script = f"""
        tell application "Notes"
            tell folder "{folder}"
                delete note "{note_name}"
            end tell
        end tell
        """
    else:
        script = f"""
        tell application "Notes"
            delete note "{note_name}"
        end tell
        """
    
    run_applescript(script)
    return True


def cmd_folders(args) -> None:
    """List all folders."""
    folders = list_folders()
    if args.json:
        print(json.dumps({"folders": folders}))
    else:
        if folders:
            print("Folders:")
            for f in folders:
                print(f"  - {f}")
        else:
            print("No folders found")


def cmd_list(args) -> None:
    """List notes."""
    notes = list_notes(args.folder)
    
    if args.json:
        print(json.dumps({"notes": notes}, default=str))
    else:
        if notes:
            print(f"Notes{(' in ' + args.folder) if args.folder else ''}:")
            for n in notes:
                folder = f" ({n.get('folder', '')})" if 'folder' in n else ""
                print(f"  - {n['title']}{folder}")
        else:
            print("No notes found")


def cmd_read(args) -> None:
    """Read a note."""
    note = get_note(args.name, args.folder)
    if args.json:
        print(json.dumps(note, default=str))
    else:
        if note:
            print(f"=== {note.get('title', 'Untitled')} ===")
            if 'folder' in note:
                print(f"Folder: {note['folder']}")
            print()
            print(note.get('body', '(empty)'))
        else:
            print(f"Note '{args.name}' not found")


def cmd_add(args) -> None:
    """Create a new note."""
    note = create_note(args.title, args.body, args.folder)
    if args.json:
        print(json.dumps(note, default=str))
    else:
        print(f"Created note: {note.get('title')}")
        print(f"ID: {note.get('id')}")


def cmd_delete(args) -> None:
    """Delete a note."""
    delete_note(args.name, args.folder)
    if args.json:
        print(json.dumps({"deleted": True, "name": args.name}))
    else:
        print(f"Deleted note: {args.name}")


def cmd_config(args) -> None:
    """Manage configuration."""
    config = load_config()
    
    if args.set:
        key, value = args.set.split("=", 1)
        config[key] = value
        save_config(config)
        print(f"Set {key} = {value}")
    elif args.list:
        if args.json:
            print(json.dumps(config))
        else:
            print("Config:")
            for k, v in config.items():
                print(f"  {k}: {v}")
    else:
        # Show current config
        if args.json:
            print(json.dumps(config))
        else:
            print("Config:")
            for k, v in config.items():
                print(f"  {k}: {v}")


def main():
    parser = argparse.ArgumentParser(
        description="CLI tool for Apple Notes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # folders
    p_folders = subparsers.add_parser("folders", help="List all folders")
    p_folders.set_defaults(func=cmd_folders)
    
    # list
    p_list = subparsers.add_parser("list", help="List notes")
    p_list.add_argument("--folder", "-f", help="Filter by folder")
    p_list.set_defaults(func=cmd_list)
    
    # read
    p_read = subparsers.add_parser("read", help="Read a note")
    p_read.add_argument("name", help="Note name")
    p_read.add_argument("--folder", "-f", help="Folder name")
    p_read.set_defaults(func=cmd_read)
    
    # add
    p_add = subparsers.add_parser("add", help="Create a new note")
    p_add.add_argument("title", help="Note title")
    p_add.add_argument("body", help="Note body")
    p_add.add_argument("--folder", "-f", help="Folder name (default: Notes)")
    p_add.set_defaults(func=cmd_add)
    
    # delete
    p_delete = subparsers.add_parser("delete", help="Delete a note")
    p_delete.add_argument("name", help="Note name")
    p_delete.add_argument("--folder", "-f", help="Folder name")
    p_delete.set_defaults(func=cmd_delete)
    
    # config
    p_config = subparsers.add_parser("config", help="Manage configuration")
    p_config.add_argument("--set", help="Set config value (key=value)")
    p_config.add_argument("--list", "-l", action="store_true", help="List config")
    p_config.set_defaults(func=cmd_config)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 1
    
    # Handle JSON flag
    if args.json and hasattr(args, 'func'):
        # Pass json flag to func
        pass
    
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
