import os
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from flask import Flask, jsonify

app = Flask(__name__)

CITY_CODE = "25"
ROUTE_NO = "117"
TARGET_DIRECTION = "한밭대학교"

# 공개 정류장 번호(사용자 확인용)
STOPS = {
    "월드컵경기장역": "42250",
    "수정초등학교": "46080",
}


def get_service_key():
    key = os.getenv("BUS_API_SERVICE_KEY")
    if not key:
        raise RuntimeError("BUS_API_SERVICE_KEY 환경변수가 설정되지 않았습니다.")
    return key


@app.route("/")
def root():
    return jsonify({
        "ok": True,
        "service": "bus117-api",
        "message": "대전 117번 버스 조회 API",
        "endpoint": "/api/bus117",
    })


@app.route("/api/bus117")
def bus117():
    # 1단계: 환경변수 연결 확인용.
    # 다음 단계에서 TAGO의 실제 nodeId / routeId를 조회하여
    # 실시간 도착정보를 붙인다.
    try:
        get_service_key()
    except RuntimeError as e:
        return jsonify({
            "ok": False,
            "error": str(e),
        }), 500

    now = datetime.now(ZoneInfo("Asia/Seoul"))

    return jsonify({
        "ok": True,
        "route": ROUTE_NO,
        "direction": TARGET_DIRECTION,
        "updated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "message": "환경변수가 정상적으로 연결되었습니다. 다음 단계에서 실시간 TAGO 조회를 연결합니다.",
        "stops": STOPS,
    })


@app.route("/api/health")
def health():
    return jsonify({"ok": True})
