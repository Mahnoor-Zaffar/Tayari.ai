"""S3-compatible object storage abstraction.

Supports any S3-compatible service (AWS S3, MinIO, Cloudflare R2, DigitalOcean
Spaces).  Falls back to local filesystem when ``STORAGE_ENDPOINT`` is empty.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path
from uuid import UUID

from core.config import settings

log = logging.getLogger("app.storage")

UPLOAD_DIR = Path("uploads")


class StorageError(Exception):
    """Base for storage-layer errors."""


class S3StorageError(StorageError):
    """S3 API call failed."""


class LocalStorageError(StorageError):
    """Local filesystem operation failed."""


class StorageService:
    """Abstracts S3 vs. local filesystem storage.

    When ``STORAGE_ENDPOINT`` is configured, uses ``boto3`` to talk to an
    S3-compatible service (MinIO for local dev, S3/R2 for production).
    Otherwise, stores files under ``./uploads/``.

    Callers should use ``store_file()`` / ``retrieve_file()`` and not worry
    about the backing store.
    """

    def __init__(self) -> None:
        self._bucket = settings.STORAGE_BUCKET
        self._use_s3 = bool(settings.STORAGE_ENDPOINT and settings.STORAGE_ACCESS_KEY)
        self._client = None
        if self._use_s3:
            self._client = self._init_s3()

    # ── Public API ────────────────────────────────────────────────────────

    async def store_file(
        self,
        key: str,
        content: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Persist ``content`` at ``key`` and return the storage path."""
        self._validate_key(key)
        if self._use_s3:
            return await self._store_s3(key, content, content_type)
        return await self._store_local(key, content)

    async def retrieve_file(self, key: str) -> bytes | None:
        """Return file content for ``key``, or ``None`` if missing."""
        self._validate_key(key)
        if self._use_s3:
            return await self._retrieve_s3(key)
        return await self._retrieve_local(key)

    async def delete_file(self, key: str) -> None:
        """Remove file at ``key``."""
        self._validate_key(key)
        if self._use_s3:
            await self._delete_s3(key)
        else:
            await self._delete_local(key)

    async def generate_upload_url(
        self,
        key: str,
        content_type: str = "application/octet-stream",
        expiration: int = 3600,
    ) -> str | None:
        """Return a presigned PUT URL for direct client uploads.

        Returns ``None`` when using local filesystem (client should send
        bytes to the API instead).
        """
        if not self._use_s3 or self._client is None:
            return None
        try:
            return self._client.generate_presigned_url(
                "put_object",
                Params={"Bucket": self._bucket, "Key": key, "ContentType": content_type},
                ExpiresIn=expiration,
            )
        except Exception as exc:
            log.error("Failed to generate presigned URL for key=%s: %s", key, exc)
            raise S3StorageError(str(exc)) from exc

    def build_key(self, user_id: UUID, prefix: str, filename: str) -> str:
        """Build a namespaced object key, e.g. ``users/{user_id}/{prefix}/{filename}``."""
        return f"users/{user_id}/{prefix}/{filename}"

    # ── Key safety ────────────────────────────────────────────────────────

    @staticmethod
    def _validate_key(key: str) -> None:
        """Reject keys that could escape the storage root (path traversal).

        Also blocks null bytes and absolute paths so neither the local
        filesystem nor S3 can be addressed outside the intended namespace.
        """
        if not key or key.startswith("/") or "\x00" in key or ".." in key:
            raise ValueError(f"Invalid storage key: {key!r}")

    # ── S3 implementation ─────────────────────────────────────────────────

    def _init_s3(self):
        import boto3

        session = boto3.Session(
            aws_access_key_id=settings.STORAGE_ACCESS_KEY,
            aws_secret_access_key=settings.STORAGE_SECRET_KEY,
        )
        client = session.client(
            "s3",
            endpoint_url=settings.STORAGE_ENDPOINT,
            region_name=settings.STORAGE_REGION,
        )
        self._ensure_bucket(client)
        return client

    def _ensure_bucket(self, client) -> None:
        try:
            client.head_bucket(Bucket=self._bucket)
        except Exception:
            try:
                client.create_bucket(Bucket=self._bucket)
                log.info("Created S3 bucket: %s", self._bucket)
            except Exception as exc:
                log.warning("Could not create bucket %s (may already exist): %s", self._bucket, exc)

    async def _store_s3(self, key: str, content: bytes, content_type: str) -> str:
        try:
            buf = io.BytesIO(content)
            self._client.upload_fileobj(  # type: ignore[union-attr]
                buf,
                self._bucket,
                key,
                ExtraArgs={"ContentType": content_type},
            )
            log.debug("Stored s3://%s/%s", self._bucket, key)
            return key
        except Exception as exc:
            log.error("S3 upload failed for key=%s: %s", key, exc)
            raise S3StorageError(str(exc)) from exc

    async def _retrieve_s3(self, key: str) -> bytes | None:
        try:
            buf = io.BytesIO()
            self._client.download_fileobj(self._bucket, key, buf)  # type: ignore[union-attr]
            return buf.getvalue()
        except Exception as exc:
            if "404" in str(exc) or "Not Found" in str(exc):
                return None
            log.error("S3 download failed for key=%s: %s", key, exc)
            raise S3StorageError(str(exc)) from exc

    async def _delete_s3(self, key: str) -> None:
        try:
            self._client.delete_object(Bucket=self._bucket, Key=key)  # type: ignore[union-attr]
        except Exception as exc:
            log.warning("S3 delete failed for key=%s: %s", key, exc)

    # ── Local filesystem implementation ───────────────────────────────────

    async def _store_local(self, key: str, content: bytes) -> str:
        path = UPLOAD_DIR / key
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            log.debug("Stored local: %s", path)
            return str(path)
        except OSError as exc:
            log.error("Local store failed for key=%s: %s", key, exc)
            raise LocalStorageError(str(exc)) from exc

    async def _retrieve_local(self, key: str) -> bytes | None:
        path = UPLOAD_DIR / key
        if not path.exists():
            return None
        try:
            return path.read_bytes()
        except OSError as exc:
            log.error("Local read failed for key=%s: %s", key, exc)
            raise LocalStorageError(str(exc)) from exc

    async def _delete_local(self, key: str) -> None:
        path = UPLOAD_DIR / key
        try:
            if path.exists():
                path.unlink()
        except OSError as exc:
            log.warning("Local delete failed for key=%s: %s", key, exc)


# ── Singleton + DI ───────────────────────────────────────────────────────────

_storage_service: StorageService | None = None


def get_storage_service() -> StorageService:
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
