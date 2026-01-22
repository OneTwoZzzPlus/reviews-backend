from fastapi import APIRouter, Depends, HTTPException

from src.dependencies import get_moderator_service
from src.auth import token_header, get_isu
from src.models import *

router = APIRouter(dependencies=[Depends(token_header)])


@router.get("/moderator")
async def moderator(isu: int | None = Depends(get_isu), mod=Depends(get_moderator_service)) -> ModeratorResponse:
    if isu is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    await mod.refresh_moderators()
    return ModeratorResponse(access=mod.have_access(isu))
