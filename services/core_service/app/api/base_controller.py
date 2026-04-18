from typing import Any, Optional
from fastapi import HTTPException, status
from shared.schemas.response import BaseResponse

class BaseController:
    def handle_success(self, data: Any = None, meta: Optional[dict] = None) -> BaseResponse:
        return BaseResponse(success=True, data=data, meta=meta)

    def handle_error(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        raise HTTPException(status_code=status_code, detail=message)
