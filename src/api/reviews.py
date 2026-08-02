from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from enums.reviews import SearchType
from schemas.reviews import (
    RegistryResponse,
    SearchResponse,
    SubjectResponse,
    SuggestionRequest,
    SuggestionResponse,
    TeacherResponse,
)
from services.reviews import ReviewsService, get_reviews_service

router = APIRouter(tags=["Reviews"])


@router.get("/search", response_model_exclude_none=True)
async def search(
    query: Annotated[str, Query(min_length=2)],
    strainer: SearchType | None = None,
    service: ReviewsService = Depends(get_reviews_service),
) -> SearchResponse:
    answer = await service.search(query, strainer)
    if answer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nothing was found for the query '{query}'",
        )
    return answer.model_dump(exclude_none=True)


@router.get("/teacher/{iid}", response_model_exclude_none=True)
async def teacher(
    iid: int,
    service: ReviewsService = Depends(get_reviews_service),
) -> TeacherResponse:
    answer = await service.teacher(iid)
    if answer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Teacher '{iid}' not found"
        )
    return answer.model_dump(exclude_none=True)


@router.get("/subject/{iid}", response_model_exclude_none=True)
async def subject(
    iid: int,
    service: ReviewsService = Depends(get_reviews_service),
) -> SubjectResponse:
    answer = await service.subject(iid)
    if answer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Subject '{iid}' not found"
        )
    return answer.model_dump(exclude_none=True)


@router.get("/registry", response_model_exclude_none=True)
async def registry(
    service: ReviewsService = Depends(get_reviews_service),
) -> RegistryResponse:
    answer = await service.registry()
    return answer.model_dump(exclude_none=True)


@router.post("/suggestion", status_code=status.HTTP_202_ACCEPTED)
async def suggestion(
    body: SuggestionRequest,
    service: ReviewsService = Depends(get_reviews_service),
) -> SuggestionResponse:

    if body.teacher.id is None and body.teacher.title is None:
        raise HTTPException(
            status_code=400,
            detail='The "teacher" field requires either an "id" (for existing) or a "title" (for new).',
        )
    if body.subject.id is None and body.subject.title is None:
        raise HTTPException(
            status_code=400,
            detail='The "subject" field requires either an "id" (for existing) or a "title" (for new).',
        )
    for sub in body.subs:
        if sub.id is None and sub.title is None:
            raise HTTPException(
                status_code=400,
                detail='Items in the "subs" field require either an "id" (for existing) or a "title" (for new).',
            )
    answer = await service.add_suggestion(body)
    return answer
