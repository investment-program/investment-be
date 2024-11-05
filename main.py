from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


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

START_YEAR = 1966
@app.post("/condition", response_model=ResponseModel, summary="분산 투자를 위한 조건 생성")
async def create_condition(request: Condition):
    current_year = datetime.now().year

    if request.n_stock <= 0:
        raise HTTPException(status_code=400, detail="종목 수를 선택해주세요.")

    if request.min_dividend <= 0:
        raise HTTPException(status_code=400, detail="배당 수익률을 입력해주세요.")
    else:
        request.min_dividend = request.min_dividend / 100

    if request.investment_style == "공격투자형":
        max_volatility = 0.15
        target_return = 0.06
    elif request.investment_style == "적극투자형":
        max_volatility = 0.10
        target_return = 0.05
    elif request.investment_style == "위험중립형":
        max_volatility = 0.07
        target_return = 0.04
    elif request.investment_style == "위험회피형":
        max_volatility = 0.03
        target_return = 0.03
    elif request.investment_style == "안전추구형":
        max_volatility = 0.01
        target_return = 0.02
    else:
        raise HTTPException(status_code=400, detail="투자 스타일을 선택해주세요.")

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

    return ResponseModel(
        condition=request,
        max_volatility=max_volatility,
        target_return=target_return
    )


@app.get("/result")
def result():
    return {}
