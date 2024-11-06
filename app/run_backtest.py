from fastapi import APIRouter, HTTPException

from app.schemas import BacktestRequest
from backtest.portfolio import Portfolio
from backtest.backtest_engine import BacktestEngine
from backtest.data_loader import DataLoader
from backtest.optimizer import PortfolioOptimizer
from backtest.visualizer import BacktestVisualizer

backtest_router = APIRouter()

# 실제 백테스트를 실행하는 함수 정의
def run_backtest_api(
        n_stocks: int,
        min_dividend: float,
        max_volatility: float,
        target_return: float,
        backtesting_period,
        initial_capital: float = 100_000_000,
        risk_free_rate: float = 0.03,
        db_path: str = "/Users/daeun/toyproject/stock_investment/data/stock_data.db"
):
    start_date = f"{backtesting_period.start_year}-{backtesting_period.start_month:02}-01"
    end_date = f"{backtesting_period.end_year}-{backtesting_period.end_month:02}-01"

    try:
        # 포트폴리오 초기화
        portfolio = Portfolio(initial_capital=initial_capital, start_date=start_date, end_date=end_date)

        # 데이터 로드
        data_loader = DataLoader(db_path)
        data_loader.load_stock_data(
            portfolio=portfolio,
            n_stocks=n_stocks,
            min_dividend=min_dividend,
            max_volatility=max_volatility,
        )

        # 포트폴리오 최적화
        optimizer = PortfolioOptimizer(min_weight=0.05, max_weight=0.90, target_return=target_return,
                                       risk_free_rate=risk_free_rate)
        optimizer.optimize(portfolio)

        # 백테스트 실행
        engine = BacktestEngine(portfolio)
        results = engine.run()

        # 결과 시각화
        visualizer = BacktestVisualizer(portfolio)
        visualizer.plot_results(results)

        return portfolio, results

    except Exception as e:
        print(f"오류 발생: {str(e)}")
        return None, None


# API 엔드포인트 정의
@backtest_router.post("/run-backtest", response_model=BacktestRequest, summary = "백테스팅 결과 생성")
async def run_backtest(request: BacktestRequest, ):
    condition = request.condition
    portfolio, results = run_backtest_api(
        n_stocks=condition.n_stock,
        min_dividend=condition.min_dividend,
        max_volatility=request.max_volatility,
        target_return=request.target_return,
        backtesting_period=condition.backtesting_period
    )

    if portfolio and results:
        return {
            "portfolio": "Portfolio result",  # 필요 시 실제 포트폴리오 데이터를 JSON 직렬화하여 반환
            "results": results
        }
    else:
        raise HTTPException(status_code=500, detail="백테스트 실행 중 오류가 발생했습니다.")
