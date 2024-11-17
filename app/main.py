from fastapi import FastAPI

from app.condition import condition_router
from app.config import add_cors_middleware
from app.run_backtest import backtest_router
from app.specific_backtest import specific_router
from app.stock_db import stocks_db_router
from app.stocks import stocks_router

app = FastAPI()
add_cors_middleware(app)
@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

app.include_router(condition_router)

app.include_router(backtest_router)

app.include_router(specific_router)

app.include_router(stocks_router)

app.include_router(stocks_db_router)