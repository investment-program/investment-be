from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost",                 # 로컬 개발 환경
    "http://localhost:3000",            # 프론트엔드의 특정 포트
    "https://www.investment-up.shop"    # 배포된 프론트엔드
]

def add_cors_middleware(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,         # 정의된 origins 리스트를 사용
        allow_credentials=True,        # 쿠키와 인증 정보 허용
        allow_methods=["*"],           # 모든 HTTP 메서드를 허용
        allow_headers=["*"],           # 모든 HTTP 헤더 허용
    )
