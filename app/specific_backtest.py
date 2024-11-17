import calendar
import sqlite3
import traceback
from typing import List, Union, Optional

import pandas as pd
from fastapi import APIRouter, HTTPException
import psycopg2

from app.schemas import InputBacktestRequest, BacktestResponse
from app.schemas import PortfolioMetrics, PortfolioComposition, BenchmarkMetrics, \
    IndividualStockPerformance, Visualizations
from backtest.backtest_engine import BacktestEngine
from backtest.data_loader import DataLoader
from backtest.optimizer import PortfolioOptimizer
from backtest.portfolio import Portfolio
from backtest.visualizer import BacktestVisualizer


async def specific_backtest(
        stock_names: List[str],
        initial_capital: float = 100_000_000,
        start_date: str = "2020-01-01",
        end_date: str = "2023-12-31",
        min_weight: float = 0.05,
        max_weight: float = 0.90,
        target_return: float = 0.05,
        risk_free_rate: float = 0.03,
        # db_path: str = "/data/stock_data.db"
        db_path: str = "/Users/daeun/toyproject/stock_investment/data/stock_data.db"
) -> Union[BacktestResponse, dict[str, Optional[str]]]:
    try:
        # 1. 포트폴리오 초기화
        portfolio = Portfolio(
            initial_capital=initial_capital, start_date=start_date, end_date=end_date
        )

        # 2. 데이터 로드
        data_loader = DataLoader(db_path)

        if "/Users/" in data_loader.get_db_path():
            print("요기")
            # 종목명으로 종목 코드 조회
            with sqlite3.connect(db_path) as conn:
                placeholders = ",".join(["?" for _ in stock_names])
                query = f"""
                    SELECT code, name, dividend_yield, liquidity
                    FROM stock_analysis
                    WHERE name IN ({placeholders})
                """
                stock_data = pd.read_sql(query, conn, params=stock_names)
                print("Loaded stock data:", stock_data)
        elif "postgresql" in data_loader.get_db_path():
            with psycopg2.connect(db_path) as conn:
                placeholders = ",".join(["%s" for _ in stock_names])  # PostgreSQL에서는 %s를 사용
                query = f"""
                    SELECT code, name, dividend_yield, liquidity
                    FROM stock_analysis
                    WHERE name IN ({placeholders})
                """

        # DataFrame에 쿼리 결과를 로드
        stock_data = pd.read_sql(query, conn, params=stock_names)
        print("Loaded stock data:", stock_data)

        if len(stock_data) != len(stock_names):
            missing_stocks = set(stock_names) - set(stock_data["name"])
            raise ValueError(f"다음 종목들을 찾을 수 없습니다: {missing_stocks}")

        # 3. 주가 데이터 로드
        data_loader.load_stock_data(
            portfolio=portfolio, stock_codes=stock_data["code"].tolist()
        )

        # 4. 포트폴리오 최적화
        optimizer = PortfolioOptimizer(
            min_weight=min_weight,
            max_weight=max_weight,
            target_return=target_return,
            risk_free_rate=risk_free_rate,
        )
        optimizer.optimize(portfolio)

        # 5. 백테스트 실행
        engine = BacktestEngine(portfolio)
        backtest_results = engine.run()

        # 6. 결과 생성
        visualizer = BacktestVisualizer(portfolio)
        results = visualizer.generate_results(backtest_results)

        # 7. 반환할 데이터 구조 생성
        response_data = BacktestResponse(
            portfolio=PortfolioMetrics(
                composition=[
                    PortfolioComposition(**stock) for stock in results["metrics"]["portfolio"]["composition"]
                ],
                final_value=results["metrics"]["portfolio"]["final_value"],
                total_return=results["metrics"]["portfolio"]["total_return"],
                annual_volatility=results["metrics"]["portfolio"]["annual_volatility"],
                sharpe_ratio=results["metrics"]["portfolio"]["sharpe_ratio"],
                max_drawdown=results["metrics"]["portfolio"]["max_drawdown"],
                win_rate=results["metrics"]["portfolio"]["win_rate"]
            ),
            benchmark=BenchmarkMetrics(
                final_value=results["metrics"]["benchmark"]["final_value"],
                total_return=results["metrics"]["benchmark"]["total_return"],
                annual_volatility=results["metrics"]["benchmark"]["annual_volatility"]
            ),
            individual_stocks=[
                IndividualStockPerformance(
                    code=stock["code"],
                    name=stock["name"],
                    return_=stock["return"],
                    volatility=stock["volatility"]
                ) for stock in results["metrics"]["individual_stocks"]
            ],
            visualizations=Visualizations(
                value_changes=results["visualizations"]["value_changes"],
                composition=results["visualizations"]["composition"],
                risk_return=results["visualizations"]["risk_return"]
            )
        )

        return response_data
    except Exception as e:
        # 오류 발생 시, traceback을 포함한 상세 오류 메시지 출력
        print(f"오류 발생: {str(e)}")
        print("Traceback: ", traceback.format_exc())  # 오류 발생 시 traceback 출력
        return {"error": str(e), "metrics": None, "visualizations": None}


specific_router = APIRouter()


@specific_router.post("/specific-backtest", response_model=BacktestResponse, summary="사용자 종목 선택 벡테스팅 결과 생성")
async def run_backtest(request: InputBacktestRequest):
    try:
        stock_names = request.stock_names

        # 백테스트 기간 계산
        start_date = f"{request.backtesting_period.start_year}-{request.backtesting_period.start_month:02d}-01"
        end_date = get_end_date(request.backtesting_period.end_year, request.backtesting_period.end_month)

        # specific_backtest 함수 호출
        response_data = await specific_backtest(
            stock_names=stock_names,
            start_date=start_date,
            end_date=end_date
        )

        if response_data:
            return response_data
        else:
            raise HTTPException(status_code=500, detail="백테스트 실행 중 오류가 발생했습니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"백테스트 실행 중 오류가 발생했습니다: {str(e)}")


def get_end_date(year: int, month: int) -> str:
    last_day = calendar.monthrange(year, month)[1]
    return f"{year}-{month:02d}-{last_day:02d}"
