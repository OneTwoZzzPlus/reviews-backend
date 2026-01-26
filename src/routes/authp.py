from fastapi import APIRouter, Depends, HTTPException

from src.dependencies import get_authp_service
from src.models import *

router = APIRouter(prefix="/authp")


@router.post("/login")
async def login(body: LoginRequest, service=Depends(get_authp_service)) -> TokenResponse:
    try:
        return await service.login(body.username, body.password)
    except service.InvalidCredentials:
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    except service.MainException as e:
        raise HTTPException(status_code=502, detail=str(e))
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/refresh")
async def refresh(body: RefreshRequest, service=Depends(get_authp_service)) -> TokenResponse:
    try:
        return await service.refresh(body.refresh_token)
    except service.MainException as e:
        raise HTTPException(status_code=502, detail=str(e))
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=str(e))


