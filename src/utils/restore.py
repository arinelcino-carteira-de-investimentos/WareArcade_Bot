import os
import shutil
from datetime import datetime
from pathlib import Path

BACKUP_DIR = Path(__file__).parent.parent / 'backup'
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

def _timestamp() -> str:
    """Return a timestamp string suitable for filenames."""
    return datetime.now().strftime('%Y%m%d_%H%M%S')

def backup_file(target_path: str) -> str:
    """Create a backup copy of *target_path*.

    Returns the path to the backup file.
    """
    target = Path(target_path).resolve()
    if not target.is_file():
        raise FileNotFoundError(f"File not found: {target_path}")
    backup_name = f"{target.name}.{_timestamp()}.bak"
    backup_path = BACKUP_DIR / backup_name
    shutil.copy2(target, backup_path)
    return str(backup_path)

def restore_file(backup_path: str, original_path: str) -> None:
    """Restore *original_path* from *backup_path*.

    Overwrites the original file with the backup content.
    """
    backup = Path(backup_path).resolve()
    original = Path(original_path).resolve()
    if not backup.is_file():
        raise FileNotFoundError(f"Backup not found: {backup_path}")
    # Ensure backup directory exists
    original.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backup, original)
