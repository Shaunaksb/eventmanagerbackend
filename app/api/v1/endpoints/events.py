from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app import schemas
from app.api import deps
from app.db.models.user import User, Role
from app.db.models.event import Event
from app.db.models.fund import Fund

router = APIRouter()


def is_admin(current_user: User = Depends(deps.get_current_active_user)) -> bool:
    if current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return True

@router.post("/", response_model=schemas.EventRead, dependencies=[Depends(deps.is_event_manager)])
async def create_event(
    *, 
    db: AsyncSession = Depends(deps.get_db), 
    event_in: schemas.EventCreate
) -> Event:
    fund = await db.execute(select(Fund))
    fund = fund.scalars().first()
    if not fund or fund.balance < event_in.budget:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    
    fund.balance -= event_in.budget
    db.add(fund)

    db_event = Event(**event_in.dict())
    db.add(db_event)
    await db.commit()
    await db.refresh(db_event)
    return db_event

@router.get("/", response_model=List[schemas.EventRead])
async def read_events(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> List[Event]:
    result = await db.execute(select(Event).offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/{event_id}", response_model=schemas.EventRead)
async def read_event(
    event_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Event:
    event = await db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.put("/{event_id}", response_model=schemas.EventRead, dependencies=[Depends(deps.is_event_manager)])
async def update_event(
    event_id: int,
    event_in: schemas.EventUpdate,
    db: AsyncSession = Depends(deps.get_db),
) -> Event:
    event = await db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    update_data = event_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(event, key, value)

    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event

@router.delete("/{event_id}", response_model=schemas.EventRead, dependencies=[Depends(deps.is_event_manager)])
async def delete_event(
    event_id: int,
    db: AsyncSession = Depends(deps.get_db),
) -> Event:
    event = await db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    await db.delete(event)
    await db.commit()
    return event
