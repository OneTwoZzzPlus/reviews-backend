from httpx import HTTPError
from fastapi import APIRouter, Depends, HTTPException, status
from services.authp import get_authp_service, AuthItmoIdService
from schemas.reviews import LoginRequest, RefreshRequest, TokenResponse

router = APIRouter(prefix="/authp", tags=["Auth Proxy"])


@router.post("/login")
async def login(
    body: LoginRequest, service: AuthItmoIdService = Depends(get_authp_service)
) -> TokenResponse:
    try:
        return await service.login(body.username, body.password)
    except AuthItmoIdService.InvalidCredentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Credentials"
        )
    except AuthItmoIdService.MainException as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except HTTPError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))


@router.post("/refresh")
async def refresh(
    body: RefreshRequest, service: AuthItmoIdService = Depends(get_authp_service)
) -> TokenResponse:
    try:
        return await service.refresh(body.refresh_token)
    except AuthItmoIdService.MainException as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except HTTPError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
