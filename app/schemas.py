from typing import Dict, Optional, Any

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

class BacktestRequest(BaseModel):
    condition: Condition
    max_volatility: float
    target_return: float

class BacktestResponse(BaseModel):
    portfolio: Dict
    results: Dict
    condition: Optional[str] = None
    max_volatility: Optional[float] = None
    target_return: Optional[float] = None

class BacktestResponsee(BaseModel):
    portfolio: Any  # JSON 직렬화된 포트폴리오 데이터 형식으로 수정
    results: Any    # JSON 직렬화된 백테스트 결과 데이터 형식으로 수정