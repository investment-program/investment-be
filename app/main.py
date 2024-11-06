from fastapi import FastAPI
from app.condition import condition_router
from app.run_backtest import backtest_router

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

app.include_router(condition_router)

app.include_router(backtest_router)