from fastapi import APIRouter, Depends, HTTPException

from src.models import *
from src.dependencies import get_reviews_service, ReviewsService
from src.auth import token_header, get_isu

router = APIRouter(dependencies=[Depends(token_header)])


@router.get("/search", response_model_exclude_none=True)
async def search(query: Annotated[str | None, Query(min_length=3)],
                 service: ReviewsService = Depends(get_reviews_service)) -> SearchResponse:
    answer = await service.search(query)
    if answer is None:
        raise HTTPException(status_code=404, detail=f"Nothing was found for the query '{query}'")
    return answer.model_dump(exclude_none=True)


@router.get("/teacher/{iid}", response_model_exclude_none=True)
async def teacher(iid: int, isu: int | None = Depends(get_isu),
                  service: ReviewsService = Depends(get_reviews_service)) -> TeacherResponse:
    answer = await service.teacher(iid, isu)
    if answer is None:
        raise HTTPException(status_code=404, detail=f"Teacher '{iid}' not found")
    return answer.model_dump(exclude_none=True)


@router.get("/subject/{iid}", response_model_exclude_none=True)
async def subject(iid: int, isu: int | None = Depends(get_isu),
                  service: ReviewsService = Depends(get_reviews_service)) -> SubjectResponse:
    answer = await service.subject(iid, isu)
    if answer is None:
        raise HTTPException(status_code=404, detail=f"Subject '{iid}' not found")
    return answer.model_dump(exclude_none=True)


@router.post("/teacher/{iid}/rate", response_model_exclude_none=True)
async def teacher_rate(iid: int, body: TeacherRateRequest,
                       isu: int | None = Depends(get_isu),
                       service: ReviewsService = Depends(get_reviews_service)) -> TeacherRateResponse:
    if isu is None:
        raise HTTPException(status_code=401, detail="A 'token' header is required")
    answer = await service.teacher_rate(isu, iid, body.user_rating)
    if answer is None:
        raise HTTPException(status_code=404, detail=f"Teacher '{iid}' not found")
    return answer.model_dump(exclude_none=True)


@router.post("/comment/{iid}/vote", response_model_exclude_none=True)
async def comment_vote(iid: int, body: CommentKarmaRequest,
                       isu: int | None = Depends(get_isu),
                       service: ReviewsService = Depends(get_reviews_service)) -> CommentKarmaResponse:
    if isu is None:
        raise HTTPException(status_code=401, detail="A 'token' header is required")
    answer = await service.comment_vote(isu, iid, body.user_karma)
    if answer is None:
        raise HTTPException(status_code=404, detail=f"Comment '{iid}' not found")
    return answer.model_dump(exclude_none=True)
