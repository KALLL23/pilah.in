from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/v1/admin/demo-mode", tags=["admin"])


@router.get("")
async def get_demo_mode(request: Request) -> JSONResponse:
    return JSONResponse(content={"demo_mode": bool(request.app.state.demo_mode)})


@router.post("")
async def toggle_demo_mode(request: Request) -> JSONResponse:
    request.app.state.demo_mode = not request.app.state.demo_mode
    return JSONResponse(content={"demo_mode": bool(request.app.state.demo_mode)})
