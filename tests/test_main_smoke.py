"""Smoke test for the fully wired console app (Plan.md Step 8.2).

Intentionally light: confirms main() assembles every Repository/
Service/Controller/View and that a full journey through all six
menus (register a sample, reserve an order, approve/reject it,
check monitoring, view the production queue, browse shipment)
works without crashing, rather than exhaustively testing console
formatting.
"""

from datetime import datetime

from app.main import build_main_menu_controller


def test_full_menu_journey_does_not_crash(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    # OrderService.reserve() defaults to datetime.now() for both the
    # timestamp and the order id's date part; predicting the exact id
    # (first order in a fresh repo -> sequence 0001) only requires the
    # date to still match by the time this assertion-free smoke test runs.
    today = datetime.now().strftime("%Y%m%d")
    expected_order_id = f"ORD-{today}-0001"

    inputs = [
        # [1] 시료 관리 -> 등록 -> 뒤로
        "1", "1", "S-001", "실리콘 웨이퍼", "0.5", "0.92", "0",
        # [2] 시료 주문 -> 예약 -> 뒤로 (재고 0, 수량 5 -> 이후 승인 시 부족 경로를 탐)
        "2", "1", "S-001", "고객A", "5", "0",
        # [3] 주문 승인/거절 -> 목록 조회 -> 처리(거절) -> 뒤로
        "3", "1", "2", expected_order_id, "N", "0",
        # [4] 모니터링 -> 주문량 확인 -> 재고량 확인 -> 뒤로
        "4", "1", "2", "0",
        # [5] 생산라인 조회 -> 현황 조회 -> 완료 처리(대기열 비어있음) -> 뒤로
        "5", "1", "2", "0",
        # [6] 출고 처리 -> 목록 조회 -> 뒤로
        "6", "1", "0",
        # 종료
        "0",
    ]
    scripted = iter(inputs)
    monkeypatch.setattr("builtins.input", lambda *_: next(scripted))

    build_main_menu_controller().run()
