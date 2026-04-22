import pytest
import io
import sys
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_upload_valid_image():
    # Mock all the app modules so we don't hit import errors for unrelated code
    mock_app = MagicMock()
    mock_app_api = MagicMock()
    mock_deps = MagicMock()
    mock_deps.CurrentUser = MagicMock
    mock_deps.get_current_user = MagicMock()
    sys.modules['app.api.deps'] = mock_deps

    mock_settings = MagicMock()
    mock_settings.UPLOAD_DIR = "/tmp"
    mock_config = MagicMock()
    mock_config.settings = mock_settings
    sys.modules['app.core.config'] = mock_config

    from app.api.endpoints.upload import upload_file
    from fastapi import UploadFile

    # PNG magic number
    png_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'

    # Mock UploadFile
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test.png"

    # Mock read
    async def mock_read(size=-1):
        if hasattr(mock_read, "first_call") and mock_read.first_call:
            mock_read.first_call = False
            return png_content
        return b""
    mock_read.first_call = True

    mock_file.read = mock_read

    async def mock_seek(*args, **kwargs):
        pass
    mock_file.seek = mock_seek

    # We mock out aiofiles.open to not write to disk
    with patch("app.api.endpoints.upload.aiofiles.open"):
        # Mock the read function for the while loop
        async def mock_read_loop(size=-1):
            if hasattr(mock_read_loop, "first_call") and mock_read_loop.first_call:
                mock_read_loop.first_call = False
                return png_content
            return b""
        mock_read_loop.first_call = True
        mock_file.read = mock_read_loop

        result = await upload_file(file=mock_file, current_user=MagicMock())
        assert "url" in result
        assert result["url"].endswith(".png")

@pytest.mark.asyncio
async def test_upload_invalid_image():
    # Mock all the app modules so we don't hit import errors for unrelated code
    mock_app = MagicMock()
    mock_app_api = MagicMock()
    mock_deps = MagicMock()
    mock_deps.CurrentUser = MagicMock
    mock_deps.get_current_user = MagicMock()
    sys.modules['app.api.deps'] = mock_deps

    mock_settings = MagicMock()
    mock_settings.UPLOAD_DIR = "/tmp"
    mock_config = MagicMock()
    mock_config.settings = mock_settings
    sys.modules['app.core.config'] = mock_config

    from app.api.endpoints.upload import upload_file
    from fastapi import UploadFile, HTTPException

    # Text content pretending to be an image
    text_content = b'This is just a text file with a .png extension'

    # Mock UploadFile
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "malicious.png"

    async def mock_read(size=-1):
        return text_content
    mock_file.read = mock_read

    async def mock_seek(*args, **kwargs):
        pass
    mock_file.seek = mock_seek

    with patch("app.api.endpoints.upload.aiofiles.open"):
        with pytest.raises(HTTPException) as exc_info:
            await upload_file(file=mock_file, current_user=MagicMock())

        assert exc_info.value.status_code == 400
        assert "File type not allowed" in exc_info.value.detail

class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)
