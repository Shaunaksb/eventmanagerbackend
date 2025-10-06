from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app import schemas
from app.api import deps
from app.db.models.user import User, Role
from app.db.models.fund import Fund

router = APIRouter()

@router.get("/balance", response_model=schemas.FundRead, dependencies=[Depends(deps.is_finance_or_event_manager)])
async def get_fund_balance(
    db: AsyncSession = Depends(deps.get_db),
) -> Fund:
    fund = await db.execute(select(Fund))
    fund = fund.scalars().first()
    if not fund:
        fund = Fund(balance=0)
        db.add(fund)
        await db.commit()
        await db.refresh(fund)
    return fund

@router.post("/set-balance", response_model=schemas.FundRead, dependencies=[Depends(deps.is_finance)])
async def set_fund_balance(
    *, 
    db: AsyncSession = Depends(deps.get_db), 
    balance_in: schemas.FundSetBalance
) -> Fund:
    fund = await db.execute(select(Fund))
    fund = fund.scalars().first()
    if not fund:
        fund = Fund(balance=balance_in.balance)
    else:
        fund.balance = balance_in.balance
    db.add(fund)
    await db.commit()
    await db.refresh(fund)
    return fund

@router.post("/deduct", response_model=schemas.FundRead, dependencies=[Depends(deps.is_finance_or_event_manager)])
async def deduct_fund(
    *, 
    db: AsyncSession = Depends(deps.get_db), 
    deduct_in: schemas.FundDeduct
) -> Fund:
    fund = await db.execute(select(Fund))
    fund = fund.scalars().first()
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")
    if fund.balance < deduct_in.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    
    fund.balance -= deduct_in.amount
    db.add(fund)
    await db.commit()
    await db.refresh(fund)
    return fund