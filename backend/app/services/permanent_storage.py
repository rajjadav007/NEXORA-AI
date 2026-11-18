"""
Permanent Resume Storage Service
Phase 2 | Feature 6: Resume Storage
"""

import shutil
import logging
from pathlib import Path
from typing import Optional, Tuple

from app.core.config import settings

logger = logging.getLogger(__name__)


class PermanentStorageService:
    """
    Manages long-term storage of validated resume documents and their versions.
    Enforces safe paths, non-exposure of internal disk layout, and clean deletion.
    """

    def __init__(self, base_dir: Optional[Path | str] = None):
        target = base_dir or settings.RESUME_STORAGE_DIR
        self.storage_dir = Path(target).resolve()
        self._ensure_storage_dir()

    def _ensure_storage_dir(self) -> None:
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error("Failed to initialize permanent storage dir %s: %s", self.storage_dir, e)
            raise

    def persist_staged_file(
        self,
        staged_path: Path,
        resume_id: str,
        version: int = 1,
    ) -> Tuple[str, Path]:
        """
        Copies a staged resume file to permanent storage under the resume's version hierarchy.
        Returns (storage_key, permanent_file_path).
        """
        if not staged_path.exists():
            raise FileNotFoundError(f"Staged file not found: {staged_path}")

        # Construct target directory for resume
        target_resume_dir = (self.storage_dir / str(resume_id)).resolve()
        if not str(target_resume_dir).startswith(str(self.storage_dir)):
            raise ValueError("Path traversal attempt in resume storage")

        target_resume_dir.mkdir(parents=True, exist_ok=True)

        # Reconstruct safe file name
        raw_name = staged_path.name
        safe_filename = raw_name.split("_", 1)[1] if "_" in raw_name else raw_name
        dest_filename = f"v{version}_{safe_filename}"
        dest_path = (target_resume_dir / dest_filename).resolve()

        # Copy staged file
        shutil.copy2(staged_path, dest_path)

        storage_key = f"{resume_id}/{dest_filename}"
        logger.info(
            "Persisted resume %s to permanent storage: key=%s, bytes=%d",
            resume_id,
            storage_key,
            dest_path.stat().st_size,
        )
        return storage_key, dest_path

    def get_storage_path(self, storage_key: str) -> Optional[Path]:
        """
        Resolves a safe storage key to a filesystem path.
        Never allows directory traversal.
        """
        if not storage_key or ".." in storage_key or storage_key.startswith("/") or storage_key.startswith("\\"):
            return None

        target_path = (self.storage_dir / storage_key).resolve()
        if not str(target_path).startswith(str(self.storage_dir)):
            return None

        if target_path.exists() and target_path.is_file():
            return target_path
        return None

    def delete_resume_files(self, resume_id: str) -> bool:
        """
        Deletes all stored versions and files associated with a resume_id.
        """
        if not resume_id or ".." in resume_id:
            return False

        target_resume_dir = (self.storage_dir / str(resume_id)).resolve()
        if not str(target_resume_dir).startswith(str(self.storage_dir)):
            return False

        if target_resume_dir.exists() and target_resume_dir.is_dir():
            shutil.rmtree(target_resume_dir, ignore_errors=True)
            return True
        return False


permanent_storage = PermanentStorageService()
