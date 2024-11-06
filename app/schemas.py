from pydantic import BaseModel

class BacktestingPeriod(BaseModel):
    start_year: int
    start_month: int
    end_year: int
    end_month: int

class Condition(BaseModel):
    n_stock: int
    min_dividend: float
    investment_style: str
    backtesting_period: BacktestingPeriod

class ResponseModel(BaseModel):
    condition: Condition
    max_volatility: float
    target_return: float