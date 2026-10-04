# clay-notes

CLI tool for Apple Notes on Mac, integrated via AppleScript.

## Features

- 📁 **List folders** - Show all note folders
- 📝 **List notes** - List all notes, optionally filtered by folder
- 📖 **Read notes** - Get note content
- ➕ **Create notes** - Add new notes to any folder
- 🗑️ **Delete notes** - Remove notes
- 🔧 **Config management** - Save default settings
- 📄 **JSON output** - For scripting

## Requirements

- macOS
- Apple Notes app
- Python 3.7+

## Installation

```bash
# Clone or download
git clone https://github.com/robb99/clay-notes.git
cd clay-notes

# Make executable
chmod +x clay_notes.py

# Optional: link to PATH
ln -s "$(pwd)/clay_notes.py" /usr/local/bin/clay-notes
```

## Usage

```bash
# List all folders
python3 clay_notes.py folders

# List notes (all or in specific folder)
python3 clay_notes.py list
python3 clay_notes.py list --folder "Work"

# Read a note
python3 clay_notes.py read "Meeting Notes"
python3 clay_notes.py read "Meeting Notes" --folder "Work"

# Create a new note
python3 clay_notes.py add "New Note" "This is the note body"
python3 clay_notes.py add "Shopping List" "Milk, Eggs, Bread" --folder "Personal"

# Delete a note
python3 clay_notes.py delete "Old Note"
python3 clay_notes.py delete "Old Note" --folder "Work"

# JSON output
python3 clay_notes.py list --json
python3 clay_notes.py read "Note Name" --json
```

## Configuration

```bash
# View config
python3 clay_notes.py config

# Set default folder
python3 clay_notes.py config --set=default_folder=Work
```

## Permissions

On first run, macOS may ask for permission to control Notes. Go to:
**System Preferences > Security & Privacy > Privacy > Automation**

Enable access for `osascript` or your terminal app.

## Files

- `clay_notes.py` - Main CLI tool (~350 lines)
- `README.md` - This documentation

## Related Tools

- [clay-reminders](https://github.com/robb99/clay-reminders) - Apple Reminders CLI
- [clay-contacts](https://github.com/robb99/clay-contacts) - Contacts CLI
