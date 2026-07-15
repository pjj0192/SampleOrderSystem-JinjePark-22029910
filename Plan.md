# Plan.md — SampleOrderSystem 구현 계획

전체 요구사항은 [PRD.md](./PRD.md), 작업 원칙(TDD/커밋 컨벤션 등)은
[CLAUDE.md](./CLAUDE.md)를 참고한다. 이 문서는 "어떤 순서로, 어떻게 만들 것인가"에
집중한다.

## 목적 (Purpose)

PRD.md의 전체 기능 명세(시료 관리, 시료 주문, 주문 승인/거절, 모니터링, 생산 라인,
출고 처리)를 콘솔 애플리케이션으로 구현한다. 4개 PoC 저장소에서 개별 검증한 패턴을
재사용하여 중복 검증을 줄이고, 이 프로젝트에서 처음 등장하는 로직(주문 상태 전이,
생산 큐, 잉여 재고 처리 등)은 TDD로 새로 검증한다.

## 범위 (Scope)

### In-Scope

PRD.md §6 메인 메뉴의 6개 기능 전체: 시료 관리 / 시료 주문 / 주문 승인·거절 /
모니터링 / 생산 라인 조회 / 출고 처리.

### Out-of-Scope

- 역할별 로그인/권한 분리 (PRD.md §2 참고 — 범위 밖)
- 다중 생산 라인 (PRD.md §8 확정: 단일 라인)
- 동시 다중 사용자/프로세스 (콘솔 단일 사용자 전제)

## 4개 PoC 저장소 재사용 전략

| 재사용 대상 | 원본 PoC | 이 저장소에서의 처리 방식 |
|---|---|---|
| `Sample` 모델 + `JsonSampleRepository` | `DataPersistence` | **그대로 이식** (chore 커밋, 기존 테스트 포함) — 이미 CRUD 전체가 검증됨 |
| `SampleService`(register/list/search) + Controller/View 패턴 | `ConsoleMVC` | **패턴 이식 후 어댑팅** (chore/feat 혼합) — Fake View 기반 Controller 테스트 방식 그대로 채용 |
| 더미 데이터 생성 패턴 | `DummyDataGenerator` | **선택적 재사용** — 수동 테스트/시연용 시드 스크립트로 활용 (In-Scope 핵심 기능은 아님) |
| `MonitoringService` 집계 로직 + 판정 기준 | `DataMonitor` | **로직 이식 후 실제 Repository로 교체** — PoC는 읽기 전용 Repository였지만, 여기서는 CRUD Repository의 조회 메서드를 그대로 사용 |
| Order 모델 + 읽기 전용 Repository | `DataMonitor` | **확장** — `customer_name`/타임스탬프 추가, 쓰기(Create/Update) 메서드 추가 (이 저장소에서 새로 TDD) |

이식 시 원본 PoC 코드를 복사하되, import 경로/패키지 구조를 이 저장소의
`src/app/...` 레이아웃에 맞게 조정한다.

## 설계 (Design)

```
SampleOrderSystem-JinjePark-22029910/
├── PRD.md
├── Plan.md
├── CLAUDE.md
├── README.md
├── requirements.txt
├── pytest.ini
├── src/app/
│   ├── models/
│   │   ├── sample.py                  # DataPersistence에서 이식
│   │   ├── order.py                   # DataMonitor 확장 (customer_name, timestamps)
│   │   └── production_job.py          # 신규
│   ├── repositories/
│   │   ├── sample_repository.py       # DataPersistence에서 이식
│   │   ├── order_repository.py        # DataMonitor 확장 (CRUD 전체)
│   │   └── production_job_repository.py  # 신규 (생산 큐 상태 저장, 선택적 영속화)
│   ├── services/
│   │   ├── sample_service.py          # ConsoleMVC에서 이식
│   │   ├── order_service.py           # 신규 (reserve/approve/reject/ship — 핵심 로직)
│   │   ├── production_service.py      # 신규 (enqueue/advance/current_and_queue)
│   │   └── monitoring_service.py      # DataMonitor에서 이식+교체
│   ├── controllers/
│   │   ├── main_menu_controller.py
│   │   ├── sample_controller.py
│   │   ├── order_reservation_controller.py
│   │   ├── order_approval_controller.py
│   │   ├── production_controller.py
│   │   ├── monitoring_controller.py
│   │   └── shipment_controller.py
│   ├── views/                          # 각 controller에 대응하는 콘솔 View
│   └── main.py                         # 진입점 (조립 + 메인 메뉴 루프)
└── tests/                               # 각 모듈에 대응
```

의존 방향: `controllers` → `services` → `repositories`/`models`, `controllers` → `views`.
Service 간 의존은 단방향으로 제한한다: `OrderService`가 재고 부족 시
`ProductionService.enqueue()`를 호출하고(주문 승인 로직 내부에서), `ProductionService`가
생산 완료 시 `OrderService`의 상태 전이 메서드를 호출해 `PRODUCING → CONFIRMED`를
반영한다. (순환 의존을 피하기 위해 두 서비스가 공유하는 상태 전이 로직은
`OrderService.complete_production(order_id, actual_quantity)`처럼 `OrderService` 쪽에
단일 진입점으로 둔다.)

## 구현 계획 (Step-by-step, TDD)

각 Phase는 관련 기능 단위로 묶고, 각 Step은 원칙적으로 `test: ...` → `feat: ...`
커밋 쌍으로 남긴다. 이식(포팅)이 명백한 Step은 `chore: ...` 커밋으로 남기고 새로
테스트를 derive하지 않는다 (원본 PoC에서 이미 검증됨).

### Phase 0 — 스캐폴딩

- 0.1 `chore`: 디렉터리 구조, `pytest.ini`, `requirements.txt`, `.gitignore` 생성

### Phase 1 — 기초 모델/저장소 이식 및 확장

- 1.1 `chore`: `Sample` 모델 + `JsonSampleRepository`를 `DataPersistence`에서 이식 (기존 테스트 포함)
- 1.2 `test`→`feat`: `Order` 모델 확장 — `customer_name`, `created_at`/`updated_at`,
  `OrderStatus` Enum(`RESERVED`/`REJECTED`/`PRODUCING`/`CONFIRMED`/`RELEASED`) 검증
  (예: quantity > 0)
- 1.3 `test`→`feat`: `OrderRepository`(JSON, CRUD 전체) — `DataMonitor`의 읽기 전용
  버전에 `create`/`update` 추가, 재실행 시 데이터 유지까지 검증
- 1.4 `test`→`feat`: `ProductionJob` 모델 — `shortage`/`actual_quantity`/`total_time`
  계산 필드 검증

### Phase 2 — 시료 관리 (메뉴 1)

- 2.1 `chore`: `SampleService`(register/list/search)를 `ConsoleMVC`에서 이식
- 2.2 `test`→`feat`: `SampleController` + Fake View 테스트 — `ConsoleMVC` 패턴을
  이 저장소의 메뉴 체계에 맞게 어댑팅
- 2.3 `feat`: `ConsoleSampleView` 구현 (수동 확인 위주)

### Phase 3 — 시료 주문 접수 (메뉴 2)

- 3.1 `test`→`feat`: `OrderService.reserve(sample_id, customer_name, quantity)` —
  존재하지 않는 `sample_id` 거부, 수량 1 이상 검증, `RESERVED` 상태로 생성
- 3.2 `test`→`feat`: `OrderReservationController` + Fake View

### Phase 4 — 주문 승인/거절 (메뉴 3, 핵심 로직)

- 4.1 `test`→`feat`: `OrderService.approve()` — **재고 충분** 경로: 즉시 `CONFIRMED`
  전환 + `sample.stock -= order.quantity`
- 4.2 `test`→`feat`: `OrderService.approve()` — **재고 부족** 경로: 부족분 계산 후
  `ProductionService.enqueue()` 호출, 주문 상태 `PRODUCING`으로 전환
- 4.3 `test`→`feat`: `OrderService.reject()` — 즉시 `REJECTED`, 재고/생산 큐 영향 없음
- 4.4 `test`→`feat`: `OrderApprovalController` + Fake View — `RESERVED` 목록 표시,
  승인/거절 분기

### Phase 5 — 생산 라인 (메뉴 5)

- 5.1 `test`→`feat`: `ProductionService.enqueue(order, shortage)` — `actual_quantity
  = ceil(shortage / yield_rate)`, `total_time = avg_production_time * actual_quantity`
  계산 후 FIFO 큐(`collections.deque`)에 `ProductionJob` 추가
- 5.2 `test`→`feat`: **생산 완료 처리 (`OrderService.complete_production`)** —
  PRD.md §7.5의 잉여 재고 규칙을 정확히 구현:
  1. `sample.stock += actual_quantity` (전량 입고)
  2. `sample.stock -= order.quantity` (주문 수량 차감)
  3. `order.status: PRODUCING -> CONFIRMED`
  - 테스트 필수 케이스: 주문 16 / 수율 0.8 → 실생산량 20 → 최종 재고 잉여 4로 남는
    시나리오를 정확한 수치로 검증 (PRD.md 예시와 동일 값)
- 5.3 `test`→`feat`: `ProductionService.current_and_queue()` — 현재 처리 중 작업 +
  대기 큐(FIFO 순서) 조회
- 5.4 `test`→`feat`: `ProductionController` + Fake View

### Phase 6 — 모니터링 (메뉴 4)

- 6.1 `chore`/`feat`: `MonitoringService.order_status_summary()` —
  `DataMonitor`에서 이식, 실제 `OrderRepository`와 연동되도록 교체
- 6.2 `chore`/`feat`: `MonitoringService.stock_summary()` — `DataMonitor`에서 이식,
  잔여율 경계값(0%, 50%) 테스트 포함
- 6.3 `test`→`feat`: `MonitoringController` + Fake View

### Phase 7 — 출고 처리 (메뉴 6)

- 7.1 `test`→`feat`: `OrderService.ship(order_id)` — `CONFIRMED`가 아닌 주문 출고
  시도 시 예외, 정상 시 `RELEASED` 전환 (재고 추가 차감 없음)
- 7.2 `test`→`feat`: `ShipmentController` + Fake View

### Phase 8 — 메인 메뉴 통합 (사용자 진입점)

- 8.1 `test`→`feat`: `MainMenuController` — 요약 정보 조합(등록 시료 수/총 재고/전체
  주문 수/생산라인 대기 건수), 메뉴 선택에 따라 하위 Controller로 라우팅
- 8.2 `feat`: `main.py` — 전체 Repository/Service/Controller/View 조립, UTF-8 콘솔
  강제(Windows 인코딩 이슈 대응, 기존 PoC들과 동일 패턴) + 스모크 테스트
- 8.3 `chore` (선택): `DummyDataGenerator` 패턴을 참고한 시드 스크립트 — 수동 테스트용
  초기 데이터 채우기

### Phase 9 — 마무리

- 9.1 `docs`: README (설치/실행/테스트 방법)
- 9.2 전체 테스트 재실행 + DoD 체크리스트 확인
- 9.3 GitHub push

## 완료 기준 (DoD)

- [x] PRD.md의 6개 메뉴 기능이 모두 콘솔에서 동작 — `tests/test_main_smoke.py` +
      수동 실행으로 등록→주문→승인(생산 경로)→모니터링→생산 완료(잉여 재고 반영)→
      출고까지 전체 여정 확인
- [x] 애플리케이션 재시작 후에도 시료/주문 데이터가 유지됨 —
      `JsonSampleRepository`/`JsonOrderRepository`의 재실행 지속성 테스트 +
      수동 실행 시 `data/*.json` 내용 확인
- [x] 주문 상태 전이 규칙(§5)과 생산 완료 후 잉여 재고 규칙(§7.5)이 테스트로 정확히
      검증됨 — `tests/test_order_service_complete_production.py`가 PRD.md 예시
      수치(주문 16/수율 0.8→실생산량 20→재고 4)를 그대로 검증
- [x] 모니터링 판정 기준(잔여율 50% 경계, `REJECTED` 제외)이 테스트로 검증됨 —
      `tests/test_monitoring_service_stock_summary.py`/`test_monitoring_service_order_summary.py`
- [x] `pytest` 전체 통과 — 134개 전부 통과
- [x] 커밋 로그가 Phase/Step 순서의 test→feat(→chore) 쌍으로 구성 — `git log --oneline` 확인
- [x] README에 실행 방법 명시, GitHub Public 저장소에 push 완료
