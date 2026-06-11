import mimetypes
import uuid
from enum import Enum
from pathlib import Path

import aiofiles
import magic
from fastapi import HTTPException, UploadFile, status


"""
Walidacja i async-owy streaming uploadow obrazow.

- async streaming w kawalkach (aiofiles) z limit rozmiaru,
- walidacja content_type + rozszerzenia + magic-bytes (realna zawartosc),
- blokada path traversal: nazwa pliku generowana po stronie serwera (uuid).
"""


# zależne od pilow, dla tego heic do wyjebania
# bo nawet jak dodam to pilow i tak się wyjebie
ALLOWED_IMAGE = {"image/jpeg", "image/png", "image/webp", "image/bmp"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB

# Staly, wewnetrzny katalog na tymczasowe uploady
UPLOAD_DIR = (Path(__file__).resolve().parent / "uploads_tmp")


def validate_content_type(file: UploadFile) -> None:
    # Tani, wczesny filtr po naglowku requestu. Realna weryfikacja: magic + Pillow.
    if not file.content_type or file.content_type not in ALLOWED_IMAGE:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Nieobslugiwany format obrazu: {file.content_type}",
        )


def _safe_dest(upload_dir: Path, original_name: str) -> Path:
    # Nazwa generowana po stronie serwera -> filename uzytkownika NIGDY nie buduje sciezki.
    suffix = Path(original_name or "").suffix.lower()[:10]
    upload_dir = upload_dir.resolve()
    dest = (upload_dir / f"{uuid.uuid4().hex}{suffix}").resolve()
    # Bezpiecznik: cel musi byc wewnatrz katalogu uploadow (blokada path traversal)
    if not dest.is_relative_to(upload_dir):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid upload path")
    return dest


async def stream_image_to_disk(file: UploadFile, max_bytes: int = MAX_IMAGE_SIZE) -> Path:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = _safe_dest(UPLOAD_DIR, file.filename)

    total = 0
    try:
        async with aiofiles.open(dest, "wb") as out:
            while chunk := await file.read(1024 * 1024):  # 1 MB
                total += len(chunk)
                if total > max_bytes:
                    dest.unlink(missing_ok=True)
                    raise HTTPException(
                        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="Image too large",
                    )
                await out.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        dest.unlink(missing_ok=True)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error while streaming file: {e}")

    # 3. magic-bytes: weryfikujemy REALNA zawartosc zapisanego pliku
    detected = magic.from_file(str(dest), mime=True)
    if detected not in ALLOWED_IMAGE:
        dest.unlink(missing_ok=True)
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Zawartosc nie jest obrazem (magic): {detected}",
        )
    return dest