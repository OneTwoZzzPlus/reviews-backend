from fastapi import APIRouter, Depends, HTTPException

from src.models import *
from src.dependencies import get_reviews_service, ReviewsService, get_moderator_service, ModeratorService
from src.auth import token_header, get_isu

router = APIRouter(dependencies=[Depends(token_header)])


@router.get("/search", response_model_exclude_none=True)
async def search(query: Annotated[str, Query(min_length=3)],
                 strainer: SearchType | None = None,
                 service: ReviewsService = Depends(get_reviews_service)) -> SearchResponse:
    answer = await service.search(query, strainer)
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


@router.post("/suggestion", status_code=202)
async def suggestion(body: SuggestionAddRequest,
                     isu: int | None = Depends(get_isu),
                     service: ReviewsService = Depends(get_reviews_service)) -> SuggestionAddResponse:

    if body.teacher.id is None and body.teacher.title is None:
        raise HTTPException(
            status_code=400,
            detail='The "teacher" field requires either an "id" (for existing) or a "title" (for new).'
        )
    if body.subject.id is None and body.subject.title is None:
        raise HTTPException(
            status_code=400,
            detail='The "subject" field requires either an "id" (for existing) or a "title" (for new).'
        )
    for sub in body.subs:
        if sub.id is None and sub.title is None:
            raise HTTPException(
                status_code=400,
                detail='Items in the "subs" field require either an "id" (for existing) or a "title" (for new).'
            )
    answer = await service.add_suggestion(isu, body)
    return SuggestionAddResponse(id=answer)


@router.get("/suggestion", response_model_exclude_none=True)
async def suggestion_list(isu: int | None = Depends(get_isu),
                          mod: ModeratorService = Depends(get_moderator_service),
                          service: ReviewsService = Depends(get_reviews_service)) -> SuggestionListResponse:
    if not await mod.have_access(isu):
        raise HTTPException(status_code=403, detail="You aren't in the moderator list")
    answer = await service.list_suggestion()
    return answer.model_dump(exclude_none=True)


@router.get("/suggestion/{iid}", response_model_exclude_none=True)
async def suggestion_get(iid: int,
                         isu: int | None = Depends(get_isu),
                         mod: ModeratorService = Depends(get_moderator_service),
                         service: ReviewsService = Depends(get_reviews_service)) -> SuggestionResponse:
    if not await mod.have_access(isu):
        raise HTTPException(status_code=403, detail="You aren't in the moderator list")
    answer = await service.get_suggestion(iid)
    if answer is None:
        raise HTTPException(status_code=404, detail=f"Suggestion '{iid}' not found")
    return answer.model_dump(exclude_none=True)
