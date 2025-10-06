from pydantic import BaseModel

class FundBase(BaseModel):
    balance: float

class FundCreate(FundBase):
    pass

class FundUpdate(FundBase):
    pass

class FundDeduct(BaseModel):
    amount: float

class FundSetBalance(BaseModel):
    balance: float

class FundRead(FundBase):
    id: int

    class Config:
        from_attributes = True
