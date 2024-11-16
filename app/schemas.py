from typing import List

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

# 백테스트 요청 모델 및 조건 응답 모델
class BacktestRequest(BaseModel):
    condition: Condition  # 조건을 포함
    max_volatility: float  # max_volatility는 BacktestRequest 레벨에서 정의
    target_return: float   # target_return도 BacktestRequest 레벨에서 정의

# 포트폴리오 구성을 정의하는 모델
class PortfolioComposition(BaseModel):
    code: str
    name: str
    weight: float
    dividend_yield: float

# 포트폴리오 성과 지표 모델
class PortfolioMetrics(BaseModel):
    composition: List[PortfolioComposition]  # composition 리스트가 포함
    final_value: float
    total_return: float
    annual_volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float

# 벤치마크 성과 지표 모델
class BenchmarkMetrics(BaseModel):
    final_value: float
    total_return: float
    annual_volatility: float

# 개별 종목 성과 모델
class IndividualStockPerformance(BaseModel):
    code: str
    name: str
    return_: float
    volatility: float

# 시각화 데이터 모델
class Visualizations(BaseModel):
    value_changes: str
    composition: str
    risk_return: str

# 백테스트 응답 전체 모델
class BacktestResponse(BaseModel):
    portfolio: PortfolioMetrics  # PortfolioMetrics 모델을 사용하는 응답
    benchmark: BenchmarkMetrics
    individual_stocks: List[IndividualStockPerformance]
    visualizations: Visualizations