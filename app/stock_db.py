import os
from typing import List
from fastapi import APIRouter, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# .env 파일을 로드하여 환경 변수 로딩
load_dotenv()

# FastAPI 라우터 설정
stocks_db_router = APIRouter()

# 환경 변수에서 PostgreSQL URL 가져오기
DATABASE_URL = os.getenv("DATABASE_URL")


class PostgreSQLConnection:
    def __init__(self):
        # PostgreSQL 연결을 위한 SQLAlchemy 엔진 생성
        self.db_url = DATABASE_URL
        print(f"Using PostgreSQL database: {self.db_url}")

        # SQLAlchemy 엔진 생성
        self.engine = create_engine(self.db_url)

        # SQLAlchemy 세션 생성
        self.Session = sessionmaker(bind=self.engine)

    def get_session(self):
        """SQLAlchemy 세션 반환"""
        return self.Session()

    def query_db(self, query: str, params: tuple = ()) -> List[dict]:
        """PostgreSQL에서 쿼리를 실행하고 결과를 반환"""
        try:
            # PostgreSQL에서 SQLAlchemy를 통해 쿼리 실행
            conn = self.engine.connect()
            result = conn.execute(query, params)
            rows = result.fetchall()
            conn.close()

            if rows:
                return [dict(row) for row in rows]  # 결과를 딕셔너리 형태로 반환
            else:
                return []  # 결과가 없으면 빈 리스트 반환
        except Exception as e:
            print(f"Database error: {e}")
            return []  # 예외 발생 시 빈 리스트 반환


# 데이터베이스 연결 객체 생성
db_connection = PostgreSQLConnection()


# 종목 검색 API
@stocks_db_router.get("/db/stocks/search/{name}", summary="서버) 종목 입력")
async def search_stocks(name: str):
    """사용자가 입력한 종목명에 맞는 종목 목록을 반환하는 API"""
    name = name.strip()

    if not name:
        raise HTTPException(status_code=400, detail="종목명을 입력해 주세요.")

    query = """
        SELECT * FROM stock_analysis WHERE name LIKE :name
    """

    # 검색할 때 입력된 이름을 포함하는 종목들을 검색
    results = db_connection.query_db(query, {"name": f"%{name}%"})

    if results:
        return {"stocks": results}
    else:
        raise HTTPException(status_code=404, detail=f"'{name}'에 해당하는 종목을 찾을 수 없습니다.")


# 모든 종목명 반환 API
@stocks_db_router.get("/db/stocks/all", response_model=List[str], summary="서버) 모든 종목명 반환")
async def get_all_stocks():
    """데이터베이스에 존재하는 모든 종목명을 반환하는 API"""

    query = "SELECT DISTINCT name FROM stock_analysis;"

    results = db_connection.query_db(query)

    if results:
        stock_names = [stock['name'] for stock in results]
        return stock_names
    else:
        raise HTTPException(status_code=404, detail="종목을 찾을 수 없습니다.")
