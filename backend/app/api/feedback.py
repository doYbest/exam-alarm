from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.common import fail, require_client_token
from app.db.session import get_session
from app.models.content import UserFeedback
from app.models.news import HotspotEvent
from app.schemas.api import ApiError, FeedbackRequest, FeedbackResponse

router = APIRouter(
    prefix="/v1",
    dependencies=[Depends(require_client_token)],
    responses={401: {"model": ApiError}, 422: {"model": ApiError}},
)


@router.post("/feedback/events", response_model=FeedbackResponse)
async def feedback(
    request: FeedbackRequest, session: Annotated[AsyncSession, Depends(get_session)]
) -> FeedbackResponse:
    hotspot_ids = {event.hotspot_id for event in request.events}
    known_ids = set(
        (
            await session.scalars(select(HotspotEvent.id).where(HotspotEvent.id.in_(hotspot_ids)))
        ).all()
    )
    if not hotspot_ids <= known_ids:
        fail(422, "UNKNOWN_HOTSPOT", "反馈包含未知热点")
    accepted = 0
    for event in request.events:
        statement = (
            insert(UserFeedback)
            .values(
                client_event_id=event.client_event_id,
                hotspot_id=event.hotspot_id,
                event_type=event.event_type,
                occurred_at=event.occurred_at,
                install_id_hash=None,
            )
            .on_conflict_do_nothing(index_elements=[UserFeedback.client_event_id])
            .returning(UserFeedback.id)
        )
        if await session.scalar(statement) is not None:
            accepted += 1
    await session.commit()
    return FeedbackResponse(accepted=accepted)
