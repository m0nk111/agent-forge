"""Tests for parallel file editor."""

import os
import tempfile
import shutil
from pathlib import Path
import pytest

from agents.parallel_editor import (
    ParallelEditor,
    FileEdit,
    FileCreation,
    BatchOperation
)


class TestFileEdit:
    """Tests for FileEdit dataclass."""
    
    def test_file_edit_creation(self):
        """Test creating FileEdit object."""
        edit = FileEdit(
            filepath="test.py",
            old_content="old",
            new_content="new",
            description="Test edit"
        )
        assert edit.filepath == "test.py"
        assert edit.old_content == "old"
        assert edit.new_content == "new"
        assert edit.description == "Test edit"
    
    def test_validate_nonexistent_file(self):
        """Test validation fails for nonexistent file."""
        edit = FileEdit("nonexistent.py", "old", "new")
        is_valid, error = edit.validate()
        assert not is_valid
        assert "not found" in error.lower()
    
    def test_validate_content_mismatch(self, tmp_path):
        """Test validation fails when old content doesn't match."""
        test_file = tmp_path / "test.py"
        test_file.write_text("actual content")
        
        edit = FileEdit(str(test_file), "wrong content", "new")
        is_valid, error = edit.validate()
        assert not is_valid
        assert "not found" in error.lower()
    
    def test_validate_success(self, tmp_path):
        """Test validation succeeds for valid edit."""
        test_file = tmp_path / "test.py"
        test_file.write_text("old content here")
        
        edit = FileEdit(str(test_file), "old content", "new content")
        is_valid, error = edit.validate()
        assert is_valid
        assert error is None


class TestFileCreation:
    """Tests for FileCreation dataclass."""
    
    def test_file_creation_object(self):
        """Test creating FileCreation object."""
        creation = FileCreation("test.py", "content", mode=0o755)
        assert creation.filepath == "test.py"
        assert creation.content == "content"
        assert creation.mode == 0o755
        assert creation.create_dirs is True
    
    def test_validate_existing_file(self, tmp_path):
        """Test validation fails for existing file."""
        test_file = tmp_path / "exists.py"
        test_file.write_text("content")
        
        creation = FileCreation(str(test_file), "new content")
        is_valid, error = creation.validate()
        assert not is_valid
        assert "already exists" in error.lower()
    
    def test_validate_missing_parent(self, tmp_path):
        """Test validation fails when parent doesn't exist and create_dirs=False."""
        test_file = tmp_path / "missing" / "test.py"
        
        creation = FileCreation(str(test_file), "content", create_dirs=False)
        is_valid, error = creation.validate()
        assert not is_valid
        assert "does not exist" in error.lower()
    
    def test_validate_success(self, tmp_path):
        """Test validation succeeds for new file."""
        test_file = tmp_path / "new.py"
        
        creation = FileCreation(str(test_file), "content")
        is_valid, error = creation.validate()
        assert is_valid
        assert error is None


class TestParallelEditor:
    """Tests for ParallelEditor class."""
    
    @pytest.fixture
    def editor(self, tmp_path):
        """Create editor with temporary backup directory."""
        backup_dir = tmp_path / "backups"
        return ParallelEditor(max_workers=2, backup_dir=str(backup_dir))
    
    @pytest.fixture
    def test_files(self, tmp_path):
        """Create test files for editing."""
        files = {
            'file1.txt': tmp_path / "file1.txt",
            'file2.txt': tmp_path / "file2.txt",
            'file3.txt': tmp_path / "file3.txt"
        }
        
        for key, path in files.items():
            path.write_text(f"Content of {key}")
        
        return files
    
    def test_batch_create_files_success(self, editor, tmp_path):
        """Test successful batch file creation."""
        files = {
            str(tmp_path / "new1.txt"): "Content 1",
            str(tmp_path / "new2.txt"): "Content 2",
            str(tmp_path / "new3.txt"): "Content 3"
        }
        
        success, created, errors = editor.batch_create_files(files)
        
        assert success
        assert len(created) == 3
        assert len(errors) == 0
        
        # Verify files exist with correct content
        for filepath, content in files.items():
            assert Path(filepath).exists()
            assert Path(filepath).read_text() == content
    
    def test_batch_create_files_with_directories(self, editor, tmp_path):
        """Test batch creation creates parent directories."""
        files = {
            str(tmp_path / "dir1" / "file1.txt"): "Content 1",
            str(tmp_path / "dir2" / "sub" / "file2.txt"): "Content 2"
        }
        
        success, created, errors = editor.batch_create_files(files)
        
        assert success
        assert len(created) == 2
        assert Path(tmp_path / "dir1").is_dir()
        assert Path(tmp_path / "dir2" / "sub").is_dir()
    
    def test_batch_create_files_existing_file(self, editor, tmp_path):
        """Test batch creation fails for existing files."""
        existing = tmp_path / "existing.txt"
        existing.write_text("already exists")
        
        files = {
            str(existing): "new content",
            str(tmp_path / "new.txt"): "content"
        }
        
        success, created, errors = editor.batch_create_files(files)
        
        assert not success
        assert len(errors) > 0
        assert "already exists" in errors[0].lower()
    
    def test_batch_create_files_dry_run(self, editor, tmp_path):
        """Test dry run doesn't create files."""
        files = {
            str(tmp_path / "dry1.txt"): "Content 1",
            str(tmp_path / "dry2.txt"): "Content 2"
        }
        
        success, created, errors = editor.batch_create_files(files, dry_run=True)
        
        assert success
        assert len(created) == 2
        
        # Files should NOT exist
        for filepath in files.keys():
            assert not Path(filepath).exists()
    
    def test_batch_edit_files_success(self, editor, test_files):
        """Test successful batch file editing."""
        edits = [
            FileEdit(str(test_files['file1.txt']), "Content", "Modified"),
            FileEdit(str(test_files['file2.txt']), "Content", "Changed"),
            FileEdit(str(test_files['file3.txt']), "Content", "Updated")
        ]
        
        success, modified, errors = editor.batch_edit_files(edits)
        
        assert success
        assert len(modified) == 3
        assert len(errors) == 0
        
        # Verify content changed
        assert "Modified" in test_files['file1.txt'].read_text()
        assert "Changed" in test_files['file2.txt'].read_text()
        assert "Updated" in test_files['file3.txt'].read_text()
    
    def test_batch_edit_files_conflict_detection(self, editor, test_files):
        """Test conflict detection for same file."""
        edits = [
            FileEdit(str(test_files['file1.txt']), "Content", "Version1"),
            FileEdit(str(test_files['file1.txt']), "Content", "Version2")  # Conflict!
        ]
        
        success, modified, errors = editor.batch_edit_files(edits)
        
        assert not success
        assert len(errors) > 0
        assert "conflict" in errors[0].lower()
    
    def test_batch_edit_files_validation_error(self, editor, test_files):
        """Test editing fails validation for wrong content."""
        edits = [
            FileEdit(str(test_files['file1.txt']), "WRONG", "New")
        ]
        
        success, modified, errors = editor.batch_edit_files(edits)
        
        assert not success
        assert len(errors) > 0
        assert "not found" in errors[0].lower()
    
    def test_batch_edit_files_dry_run(self, editor, test_files):
        """Test dry run doesn't modify files."""
        original_content = test_files['file1.txt'].read_text()
        
        edits = [
            FileEdit(str(test_files['file1.txt']), "Content", "Modified")
        ]
        
        success, modified, errors = editor.batch_edit_files(edits, dry_run=True)
        
        assert success
        assert len(modified) == 1
        
        # Content should NOT change
        assert test_files['file1.txt'].read_text() == original_content
    
    def test_batch_edit_files_rollback(self, editor, test_files):
        """Test rollback on partial failure."""
        # Create one invalid edit to trigger rollback
        edits = [
            FileEdit(str(test_files['file1.txt']), "Content", "Modified"),
            FileEdit(str(test_files['file2.txt']), "Content", "Changed"),
            FileEdit("nonexistent.txt", "old", "new")  # This will fail validation
        ]
        
        success, modified, errors = editor.batch_edit_files(edits)
        
        assert not success
        # Original content should be preserved
        assert "Content of file1.txt" in test_files['file1.txt'].read_text()
        assert "Content of file2.txt" in test_files['file2.txt'].read_text()
    
    def test_batch_delete_files_success(self, editor, test_files):
        """Test successful batch file deletion."""
        filepaths = [
            str(test_files['file1.txt']),
            str(test_files['file2.txt'])
        ]
        
        success, deleted, errors = editor.batch_delete_files(filepaths)
        
        assert success
        assert len(deleted) == 2
        assert len(errors) == 0
        
        # Files should be deleted
        assert not test_files['file1.txt'].exists()
        assert not test_files['file2.txt'].exists()
        # But file3 should still exist
        assert test_files['file3.txt'].exists()
    
    def test_batch_delete_files_nonexistent(self, editor):
        """Test deletion fails for nonexistent files."""
        filepaths = ["nonexistent1.txt", "nonexistent2.txt"]
        
        success, deleted, errors = editor.batch_delete_files(filepaths)
        
        assert not success
        assert len(errors) > 0
    
    def test_batch_delete_files_dry_run(self, editor, test_files):
        """Test dry run doesn't delete files."""
        filepaths = [str(test_files['file1.txt'])]
        
        success, deleted, errors = editor.batch_delete_files(filepaths, dry_run=True)
        
        assert success
        assert len(deleted) == 1
        
        # File should still exist
        assert test_files['file1.txt'].exists()
    
    def test_backup_creation(self, editor, test_files):
        """Test backup file creation."""
        filepath = str(test_files['file1.txt'])
        backup_path = editor._create_backup(filepath)
        
        assert Path(backup_path).exists()
        assert Path(backup_path).read_text() == test_files['file1.txt'].read_text()
    
    def test_backup_restore(self, editor, test_files):
        """Test backup restoration."""
        filepath = str(test_files['file1.txt'])
        original_content = test_files['file1.txt'].read_text()
        
        # Create backup
        backup_path = editor._create_backup(filepath)
        
        # Modify original
        test_files['file1.txt'].write_text("MODIFIED")
        assert test_files['file1.txt'].read_text() == "MODIFIED"
        
        # Restore
        editor._restore_backup(filepath, backup_path)
        assert test_files['file1.txt'].read_text() == original_content
    
    def test_conflict_detection_no_conflicts(self, editor):
        """Test conflict detection with no conflicts."""
        edits = [
            FileEdit("file1.txt", "old", "new"),
            FileEdit("file2.txt", "old", "new"),
            FileEdit("file3.txt", "old", "new")
        ]
        
        conflicts = editor._detect_conflicts(edits)
        assert len(conflicts) == 0
    
    def test_conflict_detection_with_conflicts(self, editor):
        """Test conflict detection finds conflicts."""
        edits = [
            FileEdit("file1.txt", "old", "new"),
            FileEdit("file2.txt", "old", "new"),
            FileEdit("file1.txt", "old2", "new2"),  # Conflict with first edit
            FileEdit("file3.txt", "old", "new"),
            FileEdit("file2.txt", "old3", "new3")   # Conflict with second edit
        ]
        
        conflicts = editor._detect_conflicts(edits)
        assert len(conflicts) == 2
        assert (0, 2) in conflicts  # file1.txt conflict
        assert (1, 4) in conflicts  # file2.txt conflict


class TestBatchOperation:
    """Tests for BatchOperation tracking."""
    
    def test_batch_operation_creation(self):
        """Test creating BatchOperation object."""
        op = BatchOperation(
            operation_id="test123",
            timestamp="2025-10-05T12:00:00"
        )
        assert op.operation_id == "test123"
        assert op.success is False
        assert op.error is None
    
    def test_batch_operation_save_state(self, tmp_path):
        """Test saving operation state."""
        state_dir = tmp_path / "state"
        
        op = BatchOperation(
            operation_id="test123",
            timestamp="2025-10-05T12:00:00",
            files_created=["file1.txt", "file2.txt"],
            success=True
        )
        
        op.save_state(state_dir)
        
        # Check state file was created
        state_file = state_dir / "test123.json"
        assert state_file.exists()
        
        # Verify content
        import json
        with state_file.open() as f:
            data = json.load(f)
        
        assert data['operation_id'] == "test123"
        assert data['success'] is True
        assert len(data['files_created']) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
