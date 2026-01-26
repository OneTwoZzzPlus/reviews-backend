from fastapi import APIRouter, Depends, HTTPException
from pygments.lexers import data

from src.models import *
from src.dependencies import get_reviews_service, ReviewsService, get_moderator_service, ModeratorService
from src.auth import token_header, get_isu

router = APIRouter(prefix='/mod', dependencies=[Depends(token_header)])


@router.get("")
async def moderator(isu: int | None = Depends(get_isu),
                    mod: ModeratorService = Depends(get_moderator_service)) -> ModeratorResponse:
    if isu is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return ModeratorResponse(access=await mod.have_access(isu))


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


@router.post("/suggestion/{iid}/commit", response_model_exclude_none=True, status_code=201)
async def suggestion_commit(iid: int, body: SuggestionCommitRequest,
                            isu: int | None = Depends(get_isu),
                            mod: ModeratorService = Depends(get_moderator_service),
                            service: ReviewsService = Depends(get_reviews_service)) -> SuggestionCommitResponse:
    if not await mod.have_access(isu):
        raise HTTPException(status_code=403, detail="You aren't in the moderator list")
    answer = await service.commit_suggestion(isu, iid, body)
    if answer is None:
        raise HTTPException(status_code=404, detail=f"Suggestion '{iid}' not found")
    return answer.model_dump(exclude_none=True)


@router.post("/suggestion/{iid}/cancel", response_model_exclude_none=True)
async def suggestion_cancel(iid: int, body: SuggestionCancelRequest,
                            isu: int | None = Depends(get_isu),
                            mod: ModeratorService = Depends(get_moderator_service),
                            service: ReviewsService = Depends(get_reviews_service)) -> SuggestionCancelResponse:
    if not await mod.have_access(isu):
        raise HTTPException(status_code=403, detail="You aren't in the moderator list")
    answer = await service.cancel_suggestion(isu, iid, body)
    if answer is None:
        raise HTTPException(status_code=404, detail=f"Suggestion '{iid}' not found")
    return answer.model_dump(exclude_none=True)


@router.post("/comment", response_model_exclude_none=True, status_code=201)
async def comment_add(body: CommentAddRequest,
                      isu: int | None = Depends(get_isu),
                      mod: ModeratorService = Depends(get_moderator_service),
                      service: ReviewsService = Depends(get_reviews_service)) -> CommentAddResponse:
    if not await mod.have_access(isu):
        raise HTTPException(status_code=403, detail="You aren't in the moderator list")
    answer = await service.add_comment(body)
    return answer.model_dump(exclude_none=True)


@router.post("/teacher", response_model_exclude_none=True, status_code=201)
async def teacher_upsert(body: TeacherUpdateRequest,
                         isu: int | None = Depends(get_isu),
                         mod: ModeratorService = Depends(get_moderator_service),
                         service: ReviewsService = Depends(get_reviews_service)) -> TeacherUpdateResponse:
    if not await mod.have_access(isu):
        raise HTTPException(status_code=403, detail="You aren't in the moderator list")
    answer = await service.upsert_teacher(body)
    return answer.model_dump(exclude_none=True)


@router.post("/subject", response_model_exclude_none=True, status_code=201)
async def subject_upsert(body: SubjectUpdateRequest,
                         isu: int | None = Depends(get_isu),
                         mod: ModeratorService = Depends(get_moderator_service),
                         service: ReviewsService = Depends(get_reviews_service)) -> SubjectUpdateResponse:
    if not await mod.have_access(isu):
        raise HTTPException(status_code=403, detail="You aren't in the moderator list")
    answer = await service.upsert_subject(body)
    return answer.model_dump(exclude_none=True)
