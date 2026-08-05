"""Tests for the storage service key-safety guard."""

from __future__ import annotations

import pytest

from core.storage import StorageService


@pytest.mark.asyncio
async def test_store_file_rejects_traversal_key() -> None:
    svc = StorageService()
    for bad in ["../secret.txt", "uploads/../../etc/passwd", "/abs/path", "a\x00b"]:
        with pytest.raises(ValueError):
            await svc.store_file(bad, b"content")


@pytest.mark.asyncio
async def test_retrieve_file_rejects_traversal_key() -> None:
    svc = StorageService()
    with pytest.raises(ValueError):
        await svc.retrieve_file("../../etc/passwd")


@pytest.mark.asyncio
async def test_delete_file_rejects_traversal_key() -> None:
    svc = StorageService()
    with pytest.raises(ValueError):
        await svc.delete_file("../../etc/passwd")
