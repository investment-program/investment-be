from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.schemas import Condition, ConditionBacktestRequest

condition_router = APIRouter()

START_YEAR = 1966

@condition_router.post("/condition", response_model=ConditionBacktestRequest, summary="분산 투자를 위한 조건 생성")
async def create_condition(request: Condition):
    current_year = datetime.now().year

    # 조건 검사 및 에러 처리
    if request.n_stock <= 0:
        raise HTTPException(status_code=400, detail="종목 수를 선택해주세요.")

    if request.min_dividend <= 0:
        raise HTTPException(status_code=400, detail="배당 수익률을 입력해주세요.")

    if request.investment_style == "공격투자형":
        max_volatility = 15
        target_return = 6
    elif request.investment_style == "적극투자형":
        max_volatility = 10
        target_return = 5
    elif request.investment_style == "위험중립형":
        max_volatility = 7
        target_return = 4
    elif request.investment_style == "위험회피형":
        max_volatility = 3
        target_return = 3
    elif request.investment_style == "안전추구형":
        max_volatility = 1
        target_return = 2
    else:
        raise HTTPException(status_code=400, detail="투자 스타일을 선택해주세요.")

    # 기간 검증
    if request.backtesting_period.start_year <= 0:
        raise HTTPException(status_code=400, detail="시작 연도를 입력해주세요.")
    elif request.backtesting_period.start_year < START_YEAR or request.backtesting_period.end_year > current_year:
        raise HTTPException(status_code=400, detail="시작 연도 값이 유효하지 않습니다.")
    if request.backtesting_period.start_month < 1 or request.backtesting_period.start_month > 12:
        raise HTTPException(status_code=400, detail="시작 월은 1부터 12 사이여야 합니다.")

    if request.backtesting_period.end_year <= 0:
        raise HTTPException(status_code=400, detail="종료 연도를 입력해주세요.")
    if request.backtesting_period.end_year < request.backtesting_period.start_year:
        raise HTTPException(status_code=400, detail="종료 연도는 시작 연도보다 커야 합니다.")
    elif request.backtesting_period.end_year < START_YEAR or request.backtesting_period.end_year > current_year:
        raise HTTPException(status_code=400, detail="종료 연도 값이 유효하지 않습니다.")
    if (request.backtesting_period.end_year == request.backtesting_period.start_year and
            request.backtesting_period.end_month < request.backtesting_period.start_month):
        raise HTTPException(status_code=400, detail="종료 월은 시작 월보다 커야 합니다.")
    if request.backtesting_period.end_month < 1 or request.backtesting_period.end_month > 12:
        raise HTTPException(status_code=400, detail="종료 월은 1부터 12 사이여야 합니다.")

    return ConditionBacktestRequest(
        condition=request,
        max_volatility=max_volatility,
        target_return=target_return
    )