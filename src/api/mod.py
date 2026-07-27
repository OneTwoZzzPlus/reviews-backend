from fastapi import APIRouter, Depends, HTTPException, status

from core.auth import get_isu, token_header
from schemas.reviews import (
    CommentAddRequest,
    CommentAddResponse,
    GSParserResponse,
    ModeratorResponse,
    SubjectUpdateRequest,
    SubjectUpdateResponse,
    SuggestionCancelRequest,
    SuggestionCancelResponse,
    SuggestionCommitRequest,
    SuggestionCommitResponse,
    SuggestionListResponse,
    SuggestionResponse,
    TeacherUpdateRequest,
    TeacherUpdateResponse,
)
from services.gsparser import GSParserService, get_gsparser_service
from services.moderator import ModeratorService, get_moderator_service
from services.reviews import ReviewsService, get_reviews_service

router = APIRouter(
    prefix="/mod", dependencies=[Depends(token_header)], tags=["Moderator"]
)


@router.get("")
async def moderator(
    isu: int | None = Depends(get_isu),
    mod: ModeratorService = Depends(get_moderator_service),
) -> ModeratorResponse:
    if isu is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    return ModeratorResponse(access=await mod.have_access(isu))


@router.get("/suggestion", response_model_exclude_none=True)
async def suggestion_list(
    isu: int | None = Depends(get_isu),
    mod: ModeratorService = Depends(get_moderator_service),
    service: ReviewsService = Depends(get_reviews_service),
) -> SuggestionListResponse:
    if not await mod.have_access(isu):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You aren't in the moderator list",
        )
    answer = await service.list_suggestion()
    return answer.model_dump(exclude_none=True)


@router.get("/suggestion/{iid}", response_model_exclude_none=True)
async def suggestion_get(
    iid: int,
    isu: int | None = Depends(get_isu),
    mod: ModeratorService = Depends(get_moderator_service),
    service: ReviewsService = Depends(get_reviews_service),
) -> SuggestionResponse:
    if not await mod.have_access(isu):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You aren't in the moderator list",
        )
    answer = await service.get_suggestion(iid)
    if answer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Suggestion '{iid}' not found",
        )
    return answer.model_dump(exclude_none=True)


@router.post(
    "/suggestion/{iid}/commit", response_model_exclude_none=True, status_code=201
)
async def suggestion_commit(
    iid: int,
    body: SuggestionCommitRequest,
    isu: int | None = Depends(get_isu),
    mod: ModeratorService = Depends(get_moderator_service),
    service: ReviewsService = Depends(get_reviews_service),
) -> SuggestionCommitResponse:
    if not await mod.have_access(isu):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You aren't in the moderator list",
        )
    answer = await service.commit_suggestion(isu, iid, body)
    if answer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Suggestion '{iid}' not found",
        )
    return answer.model_dump(exclude_none=True)


@router.post("/suggestion/{iid}/cancel", response_model_exclude_none=True)
async def suggestion_cancel(
    iid: int,
    body: SuggestionCancelRequest,
    isu: int | None = Depends(get_isu),
    mod: ModeratorService = Depends(get_moderator_service),
    service: ReviewsService = Depends(get_reviews_service),
) -> SuggestionCancelResponse:
    if not await mod.have_access(isu):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You aren't in the moderator list",
        )
    answer = await service.cancel_suggestion(isu, iid, body)
    if answer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Suggestion '{iid}' not found",
        )
    return answer.model_dump(exclude_none=True)


@router.post("/comment", response_model_exclude_none=True, status_code=201)
async def comment_add(
    body: CommentAddRequest,
    isu: int | None = Depends(get_isu),
    mod: ModeratorService = Depends(get_moderator_service),
    service: ReviewsService = Depends(get_reviews_service),
) -> CommentAddResponse:
    if not await mod.have_access(isu):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You aren't in the moderator list",
        )
    answer = await service.add_comment(body)
    return answer.model_dump(exclude_none=True)


@router.post("/teacher", response_model_exclude_none=True, status_code=201)
async def teacher_upsert(
    body: TeacherUpdateRequest,
    isu: int | None = Depends(get_isu),
    mod: ModeratorService = Depends(get_moderator_service),
    service: ReviewsService = Depends(get_reviews_service),
) -> TeacherUpdateResponse:
    if not await mod.have_access(isu):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You aren't in the moderator list",
        )
    answer = await service.upsert_teacher(body)
    return answer.model_dump(exclude_none=True)


@router.post("/subject", response_model_exclude_none=True, status_code=201)
async def subject_upsert(
    body: SubjectUpdateRequest,
    isu: int | None = Depends(get_isu),
    mod: ModeratorService = Depends(get_moderator_service),
    service: ReviewsService = Depends(get_reviews_service),
) -> SubjectUpdateResponse:
    if not await mod.have_access(isu):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You aren't in the moderator list",
        )
    answer = await service.upsert_subject(body)
    return answer.model_dump(exclude_none=True)


@router.get("/gsparser", response_model_exclude_none=True)
async def gsparser(
    isu: int | None = Depends(get_isu),
    mod: ModeratorService = Depends(get_moderator_service),
    service: GSParserService = Depends(get_gsparser_service),
) -> GSParserResponse:
    if not await mod.have_access(isu):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You aren't in the moderator list",
        )
    try:
        count = await service.parse()
        return GSParserResponse(count=count).model_dump(exclude_none=True)
    except GSParserService.InaccessibleGSheet as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err)
        )
    except GSParserService.InvalidGSheet as err:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(err))
