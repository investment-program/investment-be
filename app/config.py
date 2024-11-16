from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost",
    "https://www.investment-up.shop"
]

def add_cors_middleware(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],       # origins 리스트에 있는 도메인만 허용
        allow_credentials=True,      # 쿠키를 사용하는 경우 True로 설정
        allow_methods=["*"],         # 모든 HTTP 메서드를 허용
        allow_headers=["*"],         # 모든 HTTP 헤더 허용
    )