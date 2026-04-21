# Project Initialization and Data Clearing Design

## Overview

Add project initialization functionality to automatically check and create required directories and database on FastAPI startup, plus a CLI script to clear all video data.

## Design

### 1. Project Initialization

**Purpose**: Ensure required directories and database exist when FastAPI starts.

**Implementation**: Modify `main.py` to check and create:

| Item | Path | Action |
|------|------|--------|
| Videos directory | `data/videos/` | `mkdir(parents=True, exist_ok=True)` |
| Frames directory | `data/frames/` | `mkdir(parents=True, exist_ok=True)` |
| Database | `skyeye.db` | Call `init_db()` if not exists |

**Timing**: Run initialization before FastAPI app creation.

### 2. CLI Clear All Data

**Purpose**: Allow users to clear all video/frame data and reset database.

**Implementation**: Create `cli.py` using Typer.

**Command**: `python cli.py clear-all`

**Flow**:
1. Print warning message
2. Ask for confirmation (type `yes` to confirm)
3. If confirmed:
   - Delete all files in `data/videos/`
   - Delete all files in `data/frames/`
   - TRUNCATE tables: `videos` and `frames`
4. Print success message

**Error Handling**: Catch exceptions, print error message, exit with code 1.

## File Changes

| File | Action |
|------|--------|
| `main.py` | Add initialization check before app creation |
| `cli.py` | New file - CLI script with clear-all command |
| `db.py` | Export `init_db` function (already exported via import) |

## Acceptance Criteria

1. FastAPI starts without errors when directories/database don't exist
2. `python cli.py clear-all --yes` clears all data without confirmation
3. `python cli.py clear-all` asks for confirmation
4. Database tables are truncated (not dropped)
