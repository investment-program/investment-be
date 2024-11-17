import os
import sqlite3
from datetime import datetime
from typing import Optional, List

import FinanceDataReader as fdr
import pandas as pd
from dotenv import load_dotenv
from pykrx import stock
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backtest.portfolio import Portfolio

load_dotenv()


class DataLoader:
    def __init__(self, db_path=None):
        """초기화 메서드: 데이터베이스 경로 설정 및 SQLAlchemy 엔진 생성"""
        # 환경변수에서 DB 경로를 읽거나 인자로 전달된 경로를 사용
        self.db_path = db_path or os.getenv("DATABASE_URL") or os.getenv("DB_PATH")

        if not self.db_path:
            raise ValueError("DATABASE_URL 또는 DB_PATH 환경 변수가 설정되지 않았으며, db_path 인자도 제공되지 않았습니다.")

        # DB 경로를 SQLAlchemy 형식으로 변환
        if self.db_path.startswith("postgresql://"):
            # PostgreSQL 경로는 그대로 사용
            pass
        elif self.db_path.endswith(".db") or self.db_path.startswith("/"):
            # SQLite 경로는 SQLAlchemy에서 인식 가능한 형식으로 변환
            self.db_path = f"sqlite:///{self.db_path}"
        elif self.db_path.startswith("sqlite:///"):
            # 이미 SQLAlchemy 형식이면 그대로 사용
            pass
        else:
            raise ValueError(f"지원되지 않는 DB 경로 형식: {self.db_path}")

        print(f"DB 경로: {self.db_path}")

        # SQLAlchemy 엔진 및 세션 생성
        try:
            self.engine = create_engine(self.db_path)
            self.Session = sessionmaker(bind=self.engine)
        except Exception as e:
            raise ValueError(f"DB 연결 실패: {str(e)}")

    def load_stock_data(
            self,
            portfolio: Portfolio,
            n_stocks: int = 5,
            stock_codes: List[str] = None,
            min_dividend: float = 2.0,
            min_liquidity: float = 500,
            max_volatility: float = 40.0,
    ) -> None:
        """주식 데이터 로드"""

        if stock_codes:
            if "/Users/" in self.db_path:
                self.db_path = "/Users/daeun/toyproject/stock_investment/data/stock_data.db"
            stock_data = self._load_specific_stocks(stock_codes)

        else:
            stock_data = self._load_db_data(
                limit=n_stocks,
                min_dividend=min_dividend,
                min_liquidity=min_liquidity,
                max_volatility=max_volatility,
            )

        # 주가 데이터 수집
        valid_stocks = {}
        for _, row in stock_data.iterrows():
            try:
                df = self._fetch_stock_price(row["code"], portfolio)

                if df is not None and not df.empty and not df["Close"].isna().any():
                    valid_stocks[row["code"]] = df["Close"]
                    print(f"[성공] {row['code']} ({row['name']})")
                    print(f"       배당수익률: {row['dividend_yield']:.1f}%")
                    print(f"       일평균거래대금: {row['liquidity'] / 1_000_000:.0f}백만원")
                    print(f"       변동성: {row['volatility']:.1f}%")
                else:
                    print(f"[제외] {row['code']} ({row['name']}): 유효하지 않은 데이터")

            except Exception as e:
                print(f"[제외] {row['code']} ({row['name']}): {str(e)}")

        if not valid_stocks:
            raise ValueError("유효한 주가 데이터가 없습니다")

        # 데이터 저장
        portfolio.stock_prices = pd.DataFrame(valid_stocks)
        portfolio.stock_info = stock_data[stock_data["code"].isin(valid_stocks.keys())]
        portfolio.benchmark = self._fetch_benchmark_data(portfolio)

    def _load_specific_stocks(self, stock_codes: List[str]) -> pd.DataFrame:
        """특정 종목들의 데이터를 DB에서 로드"""
        if self.engine:  # PostgreSQL 또는 SQLAlchemy 엔진이 제공된 경우
            try:
                placeholders = ", ".join([f":code_{i}" for i in range(len(stock_codes))])
                query = text(f"""
                    SELECT 
                        code, 
                        name, 
                        annual_return, 
                        volatility, 
                        dividend_yield, 
                        liquidity
                    FROM stock_analysis
                    WHERE code IN ({placeholders})
                """)

                # 매개변수를 딕셔너리로 준비
                params = {f"code_{i}": code for i, code in enumerate(stock_codes)}

                with self.engine.connect() as conn:
                    df = pd.read_sql(query, conn, params=params)

                if df.empty:
                    raise ValueError(f"지정된 종목 코드에 대한 데이터를 찾을 수 없습니다: {stock_codes}")

                print(f"Loaded DataFrame:\n{df}")
                return df

            except Exception as e:
                print(f"PostgreSQL 로드 중 오류 발생: {str(e)}")
                raise

        elif self.db_path:  # SQLite를 사용하는 경우
            try:
                with sqlite3.connect(self.db_path) as conn:
                    placeholders = ",".join(["?" for _ in stock_codes])
                    query = f"""
                        SELECT 
                            code, 
                            name, 
                            annual_return, 
                            volatility, 
                            dividend_yield, 
                            liquidity
                        FROM stock_analysis
                        WHERE code IN ({placeholders})
                    """
                    print(f"Executing query: {query}")
                    print(f"With params: {stock_codes}")

                    # 데이터 로드
                    df = pd.read_sql(query, conn, params=stock_codes)

                if df.empty:
                    raise ValueError(f"지정된 종목 코드에 대한 데이터를 찾을 수 없습니다: {stock_codes}")

                print(f"\n=== 선택된 종목 ({len(df)}개) ===")
                for _, row in df.iterrows():
                    print(f"{row['code']} ({row['name']}):")
                    print(f"  배당수익률: {row['dividend_yield']:.1f}%")
                    print(f"  일평균거래대금: {row['liquidity'] / 1_000_000:.0f}백만원")
                    print(f"  변동성: {row['volatility']:.1f}%")

                return df

            except Exception as e:
                print(f"SQLite 로드 중 오류 발생: {str(e)}")
                raise

        else:
            raise ValueError("데이터베이스 경로 또는 엔진이 설정되지 않았습니다.")


    def _load_db_data(
            self,
            limit: int,
            min_dividend: float,
            min_liquidity: float,
            max_volatility: float,
    ) -> pd.DataFrame:
        """DB에서 조건을 만족하는 종목 로드"""
        query = text("""
                SELECT 
                    code, 
                    name, 
                    annual_return, 
                    volatility, 
                    dividend_yield, 
                    liquidity
                FROM stock_analysis
                WHERE dividend_yield >= :min_dividend
                    AND liquidity >= :min_liquidity
                    AND volatility <= :max_volatility
                ORDER BY annual_return DESC
                LIMIT :limit
                """)

        # SQLAlchemy 엔진을 사용하여 쿼리 실행
        with self.engine.connect() as conn:
            df = pd.read_sql(
                query,
                conn,
                params={
                    "min_dividend": min_dividend,
                    "min_liquidity": min_liquidity * 1_000_000,  # 백만원 → 원
                    "max_volatility": max_volatility,
                    "limit": limit,
                },
            )

        if df.empty:
            raise ValueError(
                f"조건을 만족하는 종목이 없습니다.\n"
                f"- 최소 배당수익률: {min_dividend}%\n"
                f"- 최소 거래대금: {min_liquidity}백만원\n"
                f"- 최대 변동성: {max_volatility}%"
            )

        print(f"\n=== 조회된 종목 ({len(df)}개) ===")
        for _, row in df.iterrows():
            print(f"{row['code']} ({row['name']}):")
            print(f"  배당수익률: {row['dividend_yield']:.1f}%")
            print(f"  일평균거래대금: {row['liquidity'] / 1_000_000:.0f}백만원")
            print(f"  변동성: {row['volatility']:.1f}%")

        return df

    def _fetch_stock_price(
            self, code: str, portfolio: Portfolio
    ) -> Optional[pd.DataFrame]:
        """개별 종목 주가 데이터 수집"""
        try:
            formatted_code = str(code).zfill(6)
            df = fdr.DataReader(
                formatted_code, portfolio.start_date, portfolio.end_date
            )
            return df
        except Exception as e:
            print(f"주가 데이터 수집 실패 ({code}): {str(e)}")
            return None

    def _fetch_benchmark_data(self, portfolio: Portfolio) -> pd.Series:
        """벤치마크(KOSPI) 데이터 수집"""
        start = datetime.strptime(portfolio.start_date, "%Y-%m-%d")
        end = datetime.strptime(portfolio.end_date, "%Y-%m-%d")

        kospi = stock.get_index_ohlcv_by_date(
            start.strftime("%Y%m%d"), end.strftime("%Y%m%d"), "1001"
        )

        if kospi.empty:
            raise ValueError("벤치마크 데이터를 찾을 수 없습니다")

        return kospi["종가"]
