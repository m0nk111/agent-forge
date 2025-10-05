"""Parallel file editing capability for Agent-Forge.

This module enables batch creation and editing of multiple files simultaneously,
improving performance for large refactorings and multi-file operations.

Features:
- Batch file creation (atomic operation)
- Parallel file editing with conflict detection
- Transaction/rollback support
- Progress tracking
- Validation before commit

Usage:
    from agents.parallel_editor import ParallelEditor, FileEdit
    
    editor = ParallelEditor()
    
    # Batch create files
    files = {
        'src/models/user.py': 'class User: pass',
        'src/models/post.py': 'class Post: pass',
        'tests/test_user.py': 'def test_user(): pass'
    }
    editor.batch_create_files(files)
    
    # Batch edit files
    edits = [
        FileEdit('src/main.py', old='import x', new='import y'),
        FileEdit('src/utils.py', old='def foo():', new='def bar():')
    ]
    editor.batch_edit_files(edits)
"""

import asyncio
import logging
import os
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class FileEdit:
    """Represents a single file edit operation."""
    
    filepath: str
    old_content: str
    new_content: str
    description: Optional[str] = None
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        """Validate the edit operation.
        
        Returns:
            (is_valid, error_message)
        """
        # Check file exists
        if not Path(self.filepath).exists():
            return False, f"File not found: {self.filepath}"
        
        # Read current content
        try:
            with open(self.filepath, 'r') as f:
                current = f.read()
        except Exception as e:
            return False, f"Cannot read file: {e}"
        
        # Check old content matches
        if self.old_content not in current:
            return False, f"Old content not found in {self.filepath}"
        
        return True, None


@dataclass
class FileCreation:
    """Represents a file creation operation."""
    
    filepath: str
    content: str
    mode: int = 0o644
    create_dirs: bool = True
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        """Validate the creation operation.
        
        Returns:
            (is_valid, error_message)
        """
        path = Path(self.filepath)
        
        # Check if file already exists
        if path.exists():
            return False, f"File already exists: {self.filepath}"
        
        # Check parent directory
        if not self.create_dirs and not path.parent.exists():
            return False, f"Parent directory does not exist: {path.parent}"
        
        return True, None


@dataclass
class BatchOperation:
    """Tracks a batch operation with rollback capability."""
    
    operation_id: str
    timestamp: str
    files_created: List[str] = field(default_factory=list)
    files_modified: Dict[str, str] = field(default_factory=dict)  # filepath -> backup path
    success: bool = False
    error: Optional[str] = None
    
    def save_state(self, state_dir: Path):
        """Save operation state for recovery."""
        state_file = state_dir / f"{self.operation_id}.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        
        with state_file.open('w') as f:
            json.dump({
                'operation_id': self.operation_id,
                'timestamp': self.timestamp,
                'files_created': self.files_created,
                'files_modified': self.files_modified,
                'success': self.success,
                'error': self.error
            }, f, indent=2)


class ParallelEditor:
    """Handles parallel file creation and editing with transaction support."""
    
    def __init__(self, max_workers: int = 4, backup_dir: str = ".agent-forge/backups"):
        """Initialize parallel editor.
        
        Args:
            max_workers: Maximum number of parallel workers
            backup_dir: Directory for backup files
        """
        self.max_workers = max_workers
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir = self.backup_dir / "operations"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
    def _create_backup(self, filepath: str) -> str:
        """Create backup of file before editing.
        
        Args:
            filepath: Path to file
            
        Returns:
            Path to backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup_name = f"{Path(filepath).name}.{timestamp}.bak"
        backup_path = self.backup_dir / backup_name
        
        shutil.copy2(filepath, backup_path)
        logger.debug(f"Created backup: {backup_path}")
        
        return str(backup_path)
    
    def _restore_backup(self, filepath: str, backup_path: str):
        """Restore file from backup.
        
        Args:
            filepath: Original file path
            backup_path: Backup file path
        """
        shutil.copy2(backup_path, filepath)
        logger.info(f"Restored {filepath} from backup")
    
    def _detect_conflicts(self, edits: List[FileEdit]) -> List[Tuple[int, int]]:
        """Detect conflicts between edits (same file).
        
        Args:
            edits: List of edit operations
            
        Returns:
            List of conflicting edit indices
        """
        conflicts = []
        file_indices = {}
        
        for i, edit in enumerate(edits):
            if edit.filepath in file_indices:
                conflicts.append((file_indices[edit.filepath], i))
            file_indices[edit.filepath] = i
        
        return conflicts
    
    def batch_create_files(
        self,
        files: Dict[str, str],
        mode: int = 0o644,
        dry_run: bool = False
    ) -> Tuple[bool, List[str], List[str]]:
        """Create multiple files in parallel (atomic operation).
        
        Args:
            files: Dictionary mapping filepath to content
            mode: File permissions (octal)
            dry_run: If True, validate but don't create
            
        Returns:
            (success, created_files, errors)
        """
        logger.info(f"Batch creating {len(files)} files...")
        
        # Generate operation ID
        operation_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        operation = BatchOperation(
            operation_id=operation_id,
            timestamp=datetime.now().isoformat()
        )
        
        # Create FileCreation objects
        creations = [
            FileCreation(filepath, content, mode)
            for filepath, content in files.items()
        ]
        
        # Validate all operations first
        validation_errors = []
        for creation in creations:
            is_valid, error = creation.validate()
            if not is_valid:
                validation_errors.append(f"{creation.filepath}: {error}")
        
        if validation_errors:
            logger.error(f"Validation failed: {validation_errors}")
            operation.error = "; ".join(validation_errors)
            operation.save_state(self.state_dir)
            return False, [], validation_errors
        
        if dry_run:
            logger.info("Dry run: validation passed, no files created")
            return True, list(files.keys()), []
        
        # Execute creations in parallel
        created = []
        errors = []
        
        def create_file(creation: FileCreation) -> Tuple[bool, str, Optional[str]]:
            """Create single file."""
            try:
                path = Path(creation.filepath)
                
                # Create parent directories
                if creation.create_dirs:
                    path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write file
                with path.open('w') as f:
                    f.write(creation.content)
                
                # Set permissions
                os.chmod(path, creation.mode)
                
                logger.debug(f"Created: {creation.filepath}")
                return True, creation.filepath, None
                
            except Exception as e:
                logger.error(f"Failed to create {creation.filepath}: {e}")
                return False, creation.filepath, str(e)
        
        # Use ThreadPoolExecutor for I/O-bound operations
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(create_file, creation): creation
                for creation in creations
            }
            
            for future in as_completed(futures):
                success, filepath, error = future.result()
                if success:
                    created.append(filepath)
                    operation.files_created.append(filepath)
                else:
                    errors.append(f"{filepath}: {error}")
        
        # Check results
        if errors:
            logger.error(f"Batch creation failed: {len(errors)} errors")
            operation.error = "; ".join(errors)
            operation.success = False
            
            # Rollback: delete successfully created files
            logger.info(f"Rolling back: deleting {len(created)} files")
            for filepath in created:
                try:
                    Path(filepath).unlink()
                    logger.debug(f"Deleted: {filepath}")
                except Exception as e:
                    logger.error(f"Rollback failed for {filepath}: {e}")
            
            operation.save_state(self.state_dir)
            return False, [], errors
        
        # Success
        operation.success = True
        operation.save_state(self.state_dir)
        
        logger.info(f"✅ Successfully created {len(created)} files")
        return True, created, []
    
    def batch_edit_files(
        self,
        edits: List[FileEdit],
        dry_run: bool = False
    ) -> Tuple[bool, List[str], List[str]]:
        """Apply multiple edits in parallel with rollback support.
        
        Args:
            edits: List of FileEdit operations
            dry_run: If True, validate but don't apply
            
        Returns:
            (success, modified_files, errors)
        """
        logger.info(f"Batch editing {len(edits)} files...")
        
        # Generate operation ID
        operation_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        operation = BatchOperation(
            operation_id=operation_id,
            timestamp=datetime.now().isoformat()
        )
        
        # Check for conflicts
        conflicts = self._detect_conflicts(edits)
        if conflicts:
            error_msg = f"Conflicting edits detected: {conflicts}"
            logger.error(error_msg)
            operation.error = error_msg
            operation.save_state(self.state_dir)
            return False, [], [error_msg]
        
        # Validate all operations first
        validation_errors = []
        for i, edit in enumerate(edits):
            is_valid, error = edit.validate()
            if not is_valid:
                validation_errors.append(f"Edit {i} - {error}")
        
        if validation_errors:
            logger.error(f"Validation failed: {validation_errors}")
            operation.error = "; ".join(validation_errors)
            operation.save_state(self.state_dir)
            return False, [], validation_errors
        
        if dry_run:
            logger.info("Dry run: validation passed, no files modified")
            return True, [edit.filepath for edit in edits], []
        
        # Create backups first (sequential to avoid race conditions)
        for edit in edits:
            try:
                backup_path = self._create_backup(edit.filepath)
                operation.files_modified[edit.filepath] = backup_path
            except Exception as e:
                logger.error(f"Failed to backup {edit.filepath}: {e}")
                operation.error = f"Backup failed: {e}"
                operation.save_state(self.state_dir)
                return False, [], [f"Backup failed: {e}"]
        
        # Apply edits in parallel
        modified = []
        errors = []
        
        def apply_edit(edit: FileEdit) -> Tuple[bool, str, Optional[str]]:
            """Apply single edit."""
            try:
                # Read file
                with open(edit.filepath, 'r') as f:
                    content = f.read()
                
                # Apply replacement
                new_content = content.replace(edit.old_content, edit.new_content)
                
                # Write back
                with open(edit.filepath, 'w') as f:
                    f.write(new_content)
                
                logger.debug(f"Modified: {edit.filepath}")
                return True, edit.filepath, None
                
            except Exception as e:
                logger.error(f"Failed to edit {edit.filepath}: {e}")
                return False, edit.filepath, str(e)
        
        # Use ThreadPoolExecutor for I/O-bound operations
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(apply_edit, edit): edit
                for edit in edits
            }
            
            for future in as_completed(futures):
                success, filepath, error = future.result()
                if success:
                    modified.append(filepath)
                else:
                    errors.append(f"{filepath}: {error}")
        
        # Check results
        if errors:
            logger.error(f"Batch editing failed: {len(errors)} errors")
            operation.error = "; ".join(errors)
            operation.success = False
            
            # Rollback: restore from backups
            logger.info(f"Rolling back: restoring {len(operation.files_modified)} files")
            for filepath, backup_path in operation.files_modified.items():
                try:
                    self._restore_backup(filepath, backup_path)
                except Exception as e:
                    logger.error(f"Rollback failed for {filepath}: {e}")
            
            operation.save_state(self.state_dir)
            return False, [], errors
        
        # Success
        operation.success = True
        operation.save_state(self.state_dir)
        
        logger.info(f"✅ Successfully modified {len(modified)} files")
        return True, modified, []
    
    def batch_delete_files(
        self,
        filepaths: List[str],
        dry_run: bool = False
    ) -> Tuple[bool, List[str], List[str]]:
        """Delete multiple files in parallel with backup.
        
        Args:
            filepaths: List of file paths to delete
            dry_run: If True, validate but don't delete
            
        Returns:
            (success, deleted_files, errors)
        """
        logger.info(f"Batch deleting {len(filepaths)} files...")
        
        # Generate operation ID
        operation_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        operation = BatchOperation(
            operation_id=operation_id,
            timestamp=datetime.now().isoformat()
        )
        
        # Validate files exist
        validation_errors = []
        for filepath in filepaths:
            if not Path(filepath).exists():
                validation_errors.append(f"File not found: {filepath}")
        
        if validation_errors:
            logger.error(f"Validation failed: {validation_errors}")
            operation.error = "; ".join(validation_errors)
            operation.save_state(self.state_dir)
            return False, [], validation_errors
        
        if dry_run:
            logger.info("Dry run: validation passed, no files deleted")
            return True, filepaths, []
        
        # Create backups before deletion
        for filepath in filepaths:
            try:
                backup_path = self._create_backup(filepath)
                operation.files_modified[filepath] = backup_path
            except Exception as e:
                logger.error(f"Failed to backup {filepath}: {e}")
                operation.error = f"Backup failed: {e}"
                operation.save_state(self.state_dir)
                return False, [], [f"Backup failed: {e}"]
        
        # Delete files
        deleted = []
        errors = []
        
        for filepath in filepaths:
            try:
                Path(filepath).unlink()
                deleted.append(filepath)
                logger.debug(f"Deleted: {filepath}")
            except Exception as e:
                logger.error(f"Failed to delete {filepath}: {e}")
                errors.append(f"{filepath}: {e}")
        
        # Check results
        if errors:
            logger.error(f"Batch deletion failed: {len(errors)} errors")
            operation.error = "; ".join(errors)
            operation.success = False
            
            # Rollback: restore deleted files
            logger.info(f"Rolling back: restoring {len(deleted)} files")
            for filepath in deleted:
                try:
                    backup_path = operation.files_modified[filepath]
                    self._restore_backup(filepath, backup_path)
                except Exception as e:
                    logger.error(f"Rollback failed for {filepath}: {e}")
            
            operation.save_state(self.state_dir)
            return False, [], errors
        
        # Success
        operation.success = True
        operation.save_state(self.state_dir)
        
        logger.info(f"✅ Successfully deleted {len(deleted)} files")
        return True, deleted, []


# CLI interface
async def main():
    """CLI entry point for parallel editor."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Parallel File Editor")
    parser.add_argument("--create", nargs="+", help="Create files (format: path:content)")
    parser.add_argument("--edit", nargs="+", help="Edit files (format: path:old:new)")
    parser.add_argument("--delete", nargs="+", help="Delete files")
    parser.add_argument("--dry-run", action="store_true", help="Validate but don't execute")
    parser.add_argument("--workers", type=int, default=4, help="Max parallel workers")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    editor = ParallelEditor(max_workers=args.workers)
    
    # Create files
    if args.create:
        files = {}
        for spec in args.create:
            path, content = spec.split(':', 1)
            files[path] = content
        
        success, created, errors = editor.batch_create_files(files, dry_run=args.dry_run)
        if success:
            print(f"✅ Created {len(created)} files")
        else:
            print(f"❌ Failed: {errors}")
            return 1
    
    # Edit files
    if args.edit:
        edits = []
        for spec in args.edit:
            parts = spec.split(':', 2)
            if len(parts) != 3:
                print(f"Invalid edit spec: {spec}")
                return 1
            path, old, new = parts
            edits.append(FileEdit(path, old, new))
        
        success, modified, errors = editor.batch_edit_files(edits, dry_run=args.dry_run)
        if success:
            print(f"✅ Modified {len(modified)} files")
        else:
            print(f"❌ Failed: {errors}")
            return 1
    
    # Delete files
    if args.delete:
        success, deleted, errors = editor.batch_delete_files(args.delete, dry_run=args.dry_run)
        if success:
            print(f"✅ Deleted {len(deleted)} files")
        else:
            print(f"❌ Failed: {errors}")
            return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
