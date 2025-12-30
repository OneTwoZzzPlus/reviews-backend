from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Annotated

from src.models import *
from src.dependencies import get_service, Service

router = APIRouter()


@router.get("/search", response_model_exclude_none=True)
async def search(query: Annotated[str | None, Query(min_length=3)],
                 service: Service = Depends(get_service)) -> SearchResponse:
    answer = await service.search(query)
    if answer is None:
        raise HTTPException(status_code=404, detail=f'Nothing was found for the query "{query}"')
    return answer.model_dump(exclude_none=True)


@router.get("/teacher/{iid}", response_model_exclude_none=True)
async def teacher(iid: int, service: Service = Depends(get_service)) -> TeacherResponse:
    answer = await service.teacher(iid)
    if answer is None:
        raise HTTPException(status_code=404, detail=f'Teacher "{iid}" not found')
    return answer.model_dump(exclude_none=True)


@router.get("/subject/{uid}", response_model_exclude_none=True)
async def subject(iid: int, service: Service = Depends(get_service)) -> SubjectResponse:
    answer = await service.subject(iid)
    if answer is None:
        raise HTTPException(status_code=404, detail=f'Subject "{iid}" not found')
    return answer.model_dump(exclude_none=True)
