# bus117-api

대전 117번 버스의 한밭대학교 방향 도착정보를 조회하기 위한 Vercel용 Python API입니다.

## Environment Variable

Vercel 프로젝트의 Environment Variables에 아래 값을 등록하세요.

```
BUS_API_SERVICE_KEY=공공데이터포털_일반인증키
```

## Endpoints

- `/`
- `/api/health`
- `/api/bus117`

현재 버전은 환경변수 연결 확인 단계입니다. 다음 단계에서 TAGO 실시간 도착정보 조회를 연결합니다.
