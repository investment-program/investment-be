from typing import Dict, Any, Union, Optional

from fastapi import APIRouter, HTTPException
from app.schemas import BacktestRequest, BacktestResponse
from backtest.portfolio import Portfolio
from backtest.backtest_engine import BacktestEngine
from backtest.data_loader import DataLoader
from backtest.optimizer import PortfolioOptimizer
from backtest.visualizer import BacktestVisualizer
from app.schemas import PortfolioMetrics, PortfolioComposition, BenchmarkMetrics, IndividualStockPerformance, \
    Visualizations

backtest_router = APIRouter()


# 실제 백테스트를 실행하는 함수 정의
def run_backtest_api(
        # 기본 설정
        initial_capital: float = 100_000_000,
        start_date: str = "2020-01-01",
        end_date: str = "2023-12-31",
        # 종목 선정 조건
        n_stocks: int = 5,
        min_dividend: float = 2.0,  # 최소 배당수익률
        min_liquidity: float = 100,  # 최소 일평균 거래대금 (백만원)
        max_volatility: float = float("inf"),  # 최대 변동성
        # 포트폴리오 최적화 조건
        min_weight: float = 0.05,  # 최소 투자 비중
        max_weight: float = 0.90,  # 최대 투자 비중
        target_return: float = 0.05,  # 목표 수익률
        risk_free_rate: float = 0.03,  # 무위험 수익률
        # 기타 설정
        db_path: str = "data/stock_data.db",
) -> Union[BacktestResponse, dict[str, Optional[str]]]:
    """백테스트 실행 함수

    Returns:
        Dict: 백테스트 결과를 담은 딕셔너리
        {
            "metrics": {
                "period": {
                    "start_date": str,
                    "end_date": str
                },
                "portfolio": {
                    "composition": List[Dict],  # 포트폴리오 구성 종목 정보
                    "final_value": float,       # 최종 포트폴리오 가치
                    "total_return": float,      # 총 수익률
                    "annual_volatility": float, # 연간 변동성
                    "sharpe_ratio": float,      # 샤프 비율
                    "max_drawdown": float,      # 최대 낙폭
                    "win_rate": float          # 승률
                },
                "benchmark": {
                    "final_value": float,
                    "total_return": float,
                    "annual_volatility": float
                },
                "individual_stocks": List[Dict]  # 개별 종목 성과
            },
            "visualizations": {
                "value_changes": str,     # Base64 인코딩된 포트폴리오 가치 변화 그래프
                "composition": str,       # Base64 인코딩된 포트폴리오 구성 파이 차트
                "risk_return": str        # Base64 인코딩된 위험-수익 산점도
            }
        }
    """
    try:
        # 1. 포트폴리오 초기화
        portfolio = Portfolio(
            initial_capital=initial_capital, start_date=start_date, end_date=end_date
        )

        # 2. 데이터 로드
        data_loader = DataLoader(db_path)
        data_loader.load_stock_data(
            portfolio=portfolio,
            n_stocks=n_stocks,
            min_dividend=min_dividend,
            min_liquidity=min_liquidity,
            max_volatility=max_volatility,
        )

        # 3. 포트폴리오 최적화
        optimizer = PortfolioOptimizer(
            min_weight=min_weight,
            max_weight=max_weight,
            target_return=target_return,
            risk_free_rate=risk_free_rate,
        )
        optimizer.optimize(portfolio)

        # 4. 백테스트 실행
        engine = BacktestEngine(portfolio)
        backtest_results = engine.run()

        # 5. 결과 생성
        visualizer = BacktestVisualizer(portfolio)
        results = visualizer.generate_results(backtest_results)

        # 6. 반환할 데이터 구조 생성
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
        print(f"\n오류 발생: {str(e)}")
        return {"error": str(e), "metrics": None, "visualizations": None}


# API 엔드포인트 정의
@backtest_router.post("/run-backtest", response_model=BacktestResponse, summary="백테스팅 결과 생성")
async def run_backtest(request: BacktestRequest):
    condition = request.condition
    response_data = run_backtest_api(
        n_stocks=condition.n_stock,
        min_dividend=condition.min_dividend,
        max_volatility=request.max_volatility,  # 여기서 max_volatility에 접근
        target_return=request.target_return,  # target_return에 접근
        # 다른 필요한 인자들 추가
    )

    if response_data:
        return response_data
    else:
        raise HTTPException(status_code=500, detail="백테스트 실행 중 오류가 발생했습니다.")
