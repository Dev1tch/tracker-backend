import mimetypes
from typing import Optional
from uuid import UUID, uuid4

from app.core.supabase_client import SupabaseClient


BUCKET = "user-media"

_EXT_BY_MIME = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
}


def _guess_extension(filename: Optional[str], mime: Optional[str]) -> str:
    if filename and "." in filename:
        return "." + filename.rsplit(".", 1)[1].lower()
    if mime and mime in _EXT_BY_MIME:
        return _EXT_BY_MIME[mime]
    if mime:
        ext = mimetypes.guess_extension(mime)
        if ext:
            return ext
    return ".bin"


class MediaService:
    def __init__(self, db: SupabaseClient):
        self.db = db
        self.table_name = "media_objects"

    def upload(
        self,
        user_id: UUID,
        kind: str,
        file_bytes: bytes,
        mime: Optional[str],
        filename: Optional[str],
    ) -> dict:
        if kind not in ("notes", "board"):
            raise ValueError("kind must be 'notes' or 'board'")

        ext = _guess_extension(filename, mime)
        media_id = uuid4()
        path = f"{user_id}/{kind}/{media_id}{ext}"
        content_type = mime or "application/octet-stream"

        storage = self.db.client.storage.from_(BUCKET)
        # Service-role client bypasses RLS; upsert=False to fail if path
        # collides (UUIDs make that essentially impossible).
        storage.upload(
            path=path,
            file=file_bytes,
            file_options={"content-type": content_type, "upsert": "false"},
        )

        public_url = storage.get_public_url(path)
        # supabase-py returns either a plain string or an object with a `.public_url`
        # depending on version; normalize to string.
        if isinstance(public_url, dict):
            public_url = public_url.get("publicURL") or public_url.get("publicUrl") or ""
        elif hasattr(public_url, "public_url"):
            public_url = public_url.public_url
        public_url = str(public_url)

        record = {
            "id": str(media_id),
            "user_id": str(user_id),
            "kind": kind,
            "storage_path": path,
            "mime": content_type,
            "size_bytes": len(file_bytes),
        }
        inserted = self.db.create(self.table_name, record)
        row = inserted.data[0] if inserted.data else record

        return {
            **row,
            "url": public_url,
        }
