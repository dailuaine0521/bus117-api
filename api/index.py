import json
import os
from datetime import datetime
from urllib.parse import unquote
from zoneinfo import ZoneInfo

import requests
from flask import Flask, Response, jsonify

app = Flask(__name__)
app.json.ensure_ascii = False

CITY_CODE = "25"
ROUTE_NO = "117"
TARGET_DIRECTION = "수통골입구 방향"

TAGO_ARRIVAL_URL = (
    "https://apis.data.go.kr/1613000/ArvlInfoInqireService/"
    "getSttnAcctoArvlPrearngeInfoList"
)

# 사용자가 실제로 타는 방향:
# 월드컵경기장역(42220) -> 수정초등학교(46070)
# -> 운암네오미아/신협연수원(41750) -> 삼성화재연수원(41710)
# -> 한밭대학교(41680) -> 수통골입구(45760)
STOPS = {
    "월드컵경기장역": {
        "stop_no": "42220",
        "node_id": "DJB8002376",
    },
    "수정초등학교": {
        "stop_no": "46070",
        "node_id": "DJB8070043",
    },
}

ROUTE_SEQUENCE = [
    {"name": "월드컵경기장역", "stop_no": "42220"},
    {"name": "수정초등학교", "stop_no": "46070"},
    {"name": "운암네오미아/신협연수원", "stop_no": "41750"},
    {"name": "삼성화재연수원", "stop_no": "41710"},
    {"name": "한밭대학교", "stop_no": "41680"},
    {"name": "수통골입구", "stop_no": "45760"},
]


def pretty_json(payload, status=200):
    return Response(
        json.dumps(payload, ensure_ascii=False, indent=2),
        status=status,
        mimetype="application/json",
    )


def get_service_key():
    key = os.getenv("BUS_API_SERVICE_KEY")
    if not key:
        raise RuntimeError("BUS_API_SERVICE_KEY 환경변수가 설정되지 않았습니다.")
    return unquote(key.strip())


def normalize_items(data):
    try:
        items = data["response"]["body"]["items"]["item"]
    except (KeyError, TypeError):
        return []

    if isinstance(items, dict):
        return [items]
    if isinstance(items, list):
        return items
    return []


def fetch_arrivals(stop_name, stop):
    params = {
        "serviceKey": get_service_key(),
        "pageNo": 1,
        "numOfRows": 50,
        "_type": "json",
        "cityCode": CITY_CODE,
        "nodeId": stop["node_id"],
    }

    response = requests.get(TAGO_ARRIVAL_URL, params=params, timeout=8)

    if response.status_code != 200:
        raise RuntimeError(
            f"TAGO HTTP {response.status_code}: {response.text[:200]}"
        )

    try:
        data = response.json()
    except ValueError:
        raise RuntimeError(
            "TAGO가 JSON이 아닌 응답을 반환했습니다: "
            + response.text[:300]
        )

    header = data.get("response", {}).get("header", {})
    result_code = str(header.get("resultCode", ""))

    if result_code and result_code not in ("00", "0"):
        raise RuntimeError(
            f"TAGO 오류 {result_code}: {header.get('resultMsg', '알 수 없는 오류')}"
        )

    arrivals = []

    for item in normalize_items(data):
        if str(item.get("routeno", "")).strip() != ROUTE_NO:
            continue

        try:
            seconds = int(item.get("arrtime", 0))
        except (TypeError, ValueError):
            seconds = 0

        try:
            remaining_stops = int(item.get("arrprevstationcnt", 0))
        except (TypeError, ValueError):
            remaining_stops = None

        arrival_minutes = (seconds + 59) // 60 if seconds > 0 else 0

        arrivals.append({
            "도착분": arrival_minutes,
            "도착초": seconds,
            "남은정류장": remaining_stops,
            "차량유형": item.get("vehicletp"),
            "경로ID": item.get("routeid"),
        })

    arrivals.sort(key=lambda x: x["도착초"])

    return {
        "이름": stop_name,
        "정류장번호": stop["stop_no"],
        "노드ID": stop["node_id"],
        "도착": arrivals[:2],
    }


@app.route("/")
def root():
    return pretty_json({
        "ok": True,
        "서비스": "bus117-api",
        "message": "대전 117번 버스 실시간 도착정보 API",
        "엔드포인트": "/api/bus117",
    })


@app.route("/api/bus117")
def bus117():
    now = datetime.now(ZoneInfo("Asia/Seoul"))

    try:
        results = {
            name: fetch_arrivals(name, stop)
            for name, stop in STOPS.items()
        }
    except RuntimeError as e:
        return pretty_json({
            "ok": False,
            "route": ROUTE_NO,
            "direction": TARGET_DIRECTION,
            "업데이트시간": now.strftime("%Y-%m-%d %H:%M:%S"),
            "error": str(e),
        }, 502)
    except requests.RequestException as e:
        return pretty_json({
            "ok": False,
            "route": ROUTE_NO,
            "direction": TARGET_DIRECTION,
            "업데이트시간": now.strftime("%Y-%m-%d %H:%M:%S"),
            "error": f"TAGO 요청 실패: {e}",
        }, 502)

    return pretty_json({
        "ok": True,
        "route": ROUTE_NO,
        "direction": TARGET_DIRECTION,
        "source": "국토교통부 TAGO 버스도착정보",
        "업데이트시간": now.strftime("%Y-%m-%d %H:%M:%S"),
        "노선순서": ROUTE_SEQUENCE,
        "정류장": results,
    })


@app.route("/api/health")
def health():
    return pretty_json({"ok": True})
