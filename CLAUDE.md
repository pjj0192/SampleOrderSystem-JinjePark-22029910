# CLAUDE.md — SampleOrderSystem

이 파일은 이 저장소에서 작업하는 Claude Code(및 기타 에이전트)를 위한 가이드입니다.
전체 요구사항은 [PRD.md](./PRD.md), 구현 계획은 [Plan.md](./Plan.md)를 참고하세요.

## 프로젝트 개요

반도체 시료 생산주문관리 콘솔 애플리케이션. 시료 등록/조회, 주문 접수, 승인/거절,
모니터링, 생산 라인(FIFO), 출고 처리까지 전체 기능 명세를 구현하는 최종 제출물이다.
4개 PoC 저장소(`ConsoleMVC`, `DataPersistence`, `DummyDataGenerator`, `DataMonitor`)의
검증된 패턴을 재사용한다 ([Plan.md](./Plan.md) "PoC 저장소 재사용 전략" 참고).

## 기술 스택

- **언어**: Python 3.11+
- **아키텍처**: MVC + Service/Repository 계층 분리 (`src/app/` 하위)
- **데이터 저장**: JSON 파일, 원자적 쓰기(temp + `os.replace`)
- **테스트**: `pytest`
- **콘솔 출력**: Python 표준 라이브러리만 사용, UTF-8 강제 설정(Windows 콘솔 인코딩 대응)
- **의존성**: `requirements.txt`에 `pytest`만 포함

## 디렉터리 구조

```
src/app/
├── models/         # Sample, Order(+OrderStatus), ProductionJob
├── repositories/    # JSON CRUD Repository (Sample/Order), ProductionJob 큐 저장
├── services/        # SampleService, OrderService, ProductionService, MonitoringService
├── controllers/      # 메뉴별 Controller (View 프로토콜에만 의존)
├── views/             # 콘솔 입출력
└── main.py             # 진입점 (조립 + 메인 메뉴 루프)
tests/
data/                   # 런타임 JSON 데이터 (git에 커밋하지 않음)
```

의존 방향: `controllers` → `services` → `repositories`/`models`, `controllers` → `views`.
`OrderService`와 `ProductionService` 간 의존은 단방향 — 상태 전이는 항상
`OrderService`를 통해서만 일어난다 (Plan.md "설계" 절 참고).

## 핵심 도메인 규칙 (반드시 지킬 것)

1. **주문 상태 전이는 `OrderService` 한 곳에서만 처리**한다 (PRD.md §5). Controller나
   View에서 직접 `order.status`를 바꾸지 않는다.
2. **재고 차감은 승인(`CONFIRMED` 전환) 시점**에 이루어진다 — 재고 충분/부족 두 경로
   모두 동일 규칙.
3. **생산 완료 후 재고 처리 (가장 실수하기 쉬운 규칙, PRD.md §7.5)**:
   - 실 생산량(`actual_quantity`)은 **전량** 재고에 입고된다 (수율은 불량 폐기가
     아니라 필요 생산량을 역산하는 계수).
   - 그 다음 주문 수량만큼만 차감해 `CONFIRMED`로 전환한다.
   - 남는 차이(`actual_quantity - shortage`)는 잉여 재고로 남는다.
   - 검증 예시: 주문 16, 수율 0.8 → 실생산량 20 입고 → 16 차감 → 재고에 4 잉여.
     이 수치를 그대로 테스트 케이스로 사용한다.
4. **생산 큐는 FIFO**, 생산 라인은 **단일 라인**이다.
5. **모니터링 집계에서 `REJECTED`는 제외**하고, 재고 상태 판정은
   `stock == 0` → 고갈(최우선) / `잔여율 >= 0.5` → 여유 / 그 외 → 부족 순서로 판정한다.

## 작업 원칙

- **TDD (Red-Green-Refactor)**: [Plan.md](./Plan.md)의 각 Phase에서 `test`→`feat`로
  표시된 Step은 반드시 테스트를 먼저 작성해 실패를 확인한 뒤 구현한다. `chore`로 표시된
  Step(PoC에서의 이식)은 기존 테스트를 그대로 가져오며 새로 Red 단계를 만들지 않는다.
  View/`main.py` 등 I/O 계층은 가벼운 스모크 테스트 + 수동 실행 확인으로 대체한다.
- **테스트 우선순위** (여러 Phase에 걸친 로직을 다시 만질 때 우선순위 판단 기준):
  1. 주문 상태 전이 규칙
  2. 재고/생산 계산식 (부족분, 실생산량, 총 생산시간)
  3. 재고 차감 시점 및 생산 완료 후 잉여 재고 처리
  4. FIFO 생산 큐
  5. 모니터링 집계
  6. Repository CRUD (영속성 왕복)
  7. View/Controller 흐름
- **Clean Code**: 타입힌트 사용, 매직 넘버 대신 상수/Enum, 함수는 단일 책임.
- **커밋 컨벤션 (Conventional Commits)**: `test:`, `feat:`, `refactor:`, `docs:`, `fix:`,
  `chore:`. Plan.md의 Step 번호를 커밋 메시지 본문에 남겨 추적 가능하게 한다
  (예: "Plan.md Step 5.2").

## 자주 쓰는 명령

```bash
# 테스트 실행
pytest

# 콘솔 앱 실행
PYTHONPATH=src python -m app.main
```
