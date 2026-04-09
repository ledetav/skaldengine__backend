from typing import Any, Optional
from fastapi import HTTPException, status
from shared.schemas.response import BaseResponse

class BaseController:
    def handle_success(self, data: Any = None, message: str = "Operation successful") -> BaseResponse:
        return BaseResponse(
            success=True,
            data=data,
            message=message
        )

    def handle_error(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, error_code: Optional[str] = None):
        raise HTTPException(
            status_code=status_code,
            detail={
                "success": False,
                "message": message,
                "error_code": error_code
            }
        )
