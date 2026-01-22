from fastapi import APIRouter, Depends, HTTPException

from src.dependencies import get_moderator_service, ModeratorService
from src.auth import token_header, get_isu
from src.models import *

router = APIRouter(dependencies=[Depends(token_header)])


@router.get("/moderator")
async def moderator(isu: int | None = Depends(get_isu),
                    mod: ModeratorService = Depends(get_moderator_service)) -> ModeratorResponse:
    if isu is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return ModeratorResponse(access=await mod.have_access(isu))
