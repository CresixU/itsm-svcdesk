# ai-generated: 90% - Claude Code drafted this; the author reviewed the error shape against API.md section 7
from fastapi import HTTPException


class ApiError(HTTPException):
    """An HTTP error whose body is always {"error": {"code", "message"}} (API.md section 7)."""

    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(status_code=status_code, detail={"error": {"code": code, "message": message}})
