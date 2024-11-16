import os
import sqlite3
from typing import List
from fastapi import APIRouter, HTTPException

stocks_router = APIRouter()

DB_PATH = os.getenv("DB_PATH")
DATABASE_URL = os.getenv("DATABASE_URL")

# 데이터베이스 쿼리 함수
def query_db(query: str, params: tuple = ()) -> List[dict]:
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # 결과를 딕셔너리 형태로 변환
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()

        if rows:
            return [dict(row) for row in rows]
        else:
            return []  # 결과가 없으면 빈 리스트 반환
    except Exception as e:
        print(f"Database error: {e}")
        return []  # 예외 발생 시 빈 리스트 반환


# 종목 검색 API
@stocks_router.get("/stocks/search/{name}")
async def search_stocks(name: str):
    """사용자가 입력한 종목명에 맞는 종목 목록을 반환하는 API"""
    name = name.strip()

    if not name:
        raise HTTPException(status_code=400, detail="종목명을 입력해 주세요.")

    query = """
        SELECT * FROM stock_analysis WHERE name LIKE ?
    """

    # 검색할 때 입력된 이름을 포함하는 종목들을 검색
    results = query_db(query, (f"%{name}%",))

    if results:
        return {"stocks": results}
    else:
        raise HTTPException(status_code=404, detail=f"'{name}'에 해당하는 종목을 찾을 수 없습니다.")


@stocks_router.get("/stocks/all", response_model=List[str], summary="모든 종목명 반환")
async def get_all_stocks():
    """데이터베이스에 존재하는 모든 종목명을 반환하는 API"""

    query = "SELECT DISTINCT name FROM stock_analysis;"

    results = query_db(query)

    if results:
        stock_names = [stock['name'] for stock in results]
        return stock_names
    else:
        raise HTTPException(status_code=404, detail="종목을 찾을 수 없습니다.")

