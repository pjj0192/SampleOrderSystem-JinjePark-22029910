# SampleOrderSystem — 반도체 시료 생산주문관리 시스템

가상의 반도체 회사 "S-Semi"의 시료(Sample) 생산·주문·재고·출고를 관리하는 콘솔 기반
애플리케이션입니다.

- 전체 요구사항: [PRD.md](./PRD.md)
- 구현 계획: [Plan.md](./Plan.md)
- 작업 가이드(Harness): [CLAUDE.md](./CLAUDE.md)

## 요구 사항

- Python 3.11+

## 설치

```bash
pip install -r requirements.txt
```

## 실행

```bash
PYTHONPATH=src python -m app.main
```

(Windows PowerShell의 경우: `$env:PYTHONPATH="src"; python -m app.main`)

실행하면 시료 관리 / 시료 주문 / 주문 승인·거절 / 모니터링 / 생산라인 조회 / 출고 처리
6개 메뉴가 있는 콘솔 화면이 표시됩니다. 데이터는 `data/samples.json`,
`data/orders.json`, `data/production_queue.json`에 저장되며, 앱을 다시 실행해도
유지됩니다 (생산 큐까지 영속화되므로, 생산 중이던 주문도 재시작 후 안전하게 이어집니다).

## 주요 기능

메인 메뉴에는 항상 시스템 시간, 등록 시료 수, 총 재고, 전체 주문 건수, 생산라인 대기
건수, 그리고 승인/출고 대기 건수가 요약되어 표시됩니다. 각 서브 메뉴는 진입하자마자
현재 상태를 보여주므로, 굳이 하위 메뉴를 한 번 더 선택하지 않아도 됩니다.

### 1. 시료 관리
- 시료 등록 / 전체 목록 / 이름 검색
- 목록은 8건씩 페이지 단위로 표시되며 `N`을 입력하면 다음 페이지로 넘어갑니다.
- 등록 중 어느 입력 단계에서든 `0`을 입력하면 등록을 취소하고 메뉴로 돌아갑니다.

### 2. 시료 주문 (예약)
- 메뉴 진입 시 주문 가능한 시료 목록(재고 포함)과 현재 승인 대기 건수를 자동으로
  보여줍니다.
- 시료 ID / 고객명 / 수량 입력 중 `0`을 입력하면 주문을 취소합니다.

### 3. 주문 승인 / 거절
- 접수된(RESERVED) 주문 목록을 진입 시 자동으로 보여줍니다.
- 승인/거절 결정을 내리기 전에 주문량, 현재 재고, 부족분, 예상 실생산량, 예상
  생산시간을 미리 계산해서 보여줍니다 (재고가 충분하면 "생산 없이 즉시 승인 가능"으로
  안내).
- 결정 후에는 `RESERVED -> CONFIRMED / PRODUCING / REJECTED`처럼 상태 변화를 명시적으로
  보여줍니다.

### 4. 모니터링
- 주문량 확인: 상태별(`RESERVED`/`CONFIRMED`/`PRODUCING`/`RELEASED`) 주문 건수
  (`REJECTED`는 집계 제외).
- 재고량 확인: 시료ID/시료명/재고(ea)/여유·부족·고갈 상태/잔여율(%)에 더해 잔여율을
  막대(bar)로도 시각화합니다.

### 5. 생산라인 조회
- 메뉴 진입 시 현재 FIFO 큐의 맨 앞 작업에 대해 주문량, 현재 재고, 부족분, 실생산량,
  완료까지 남은 시간(초), 진행률 막대를 기본으로 보여줍니다.
- **실시간 보기(`[3]`)**: 화면을 1초마다 자동으로 새로 그려 생산 진행 상황을 실시간으로
  볼 수 있습니다. `Enter`를 누르면 즉시 종료됩니다.
- 실제 경과 시간이 다 된 작업은 이 메뉴뿐 아니라 메인 메뉴에 진입할 때도 자동으로
  `PRODUCING -> CONFIRMED`로 완료 처리되므로, 별도로 "생산 완료 처리"를 누르지 않아도
  됩니다 (필요하면 `[2]`로 수동 확인도 가능).

### 6. 출고 처리
- 출고 가능한(`CONFIRMED`) 주문 목록 확인 및 출고(`RELEASED`) 처리.
- 주문 번호 입력 중 `0`을 입력하면 출고 처리를 취소합니다.

### 더미 데이터로 빠르게 시작하기 (선택)

빈 상태로 메뉴를 하나씩 테스트하기보다 데이터가 채워진 상태로 둘러보고 싶다면:

```bash
PYTHONPATH=src python -m app.tools.seed_samples --count 10 --seed 42
```

`data/samples.json`에 유효한 더미 시료 10개를 생성해 저장합니다 (재고/생산 로직
검증에는 영향 없는 개발 편의 도구이며 채점 대상 기능은 아닙니다).

## 테스트

```bash
pytest
```

## 구조

```
src/app/
├── models/           # Sample, Order(+OrderStatus), ProductionJob
├── repositories/     # JSON CRUD Repository (Sample/Order/ProductionJob 큐)
├── services/         # SampleService, OrderService, ProductionService, MonitoringService
├── controllers/      # 메뉴별 Controller (View 프로토콜에만 의존)
├── views/            # 콘솔 입출력
│   ├── console_format.py       # 표/배너 공통 포맷팅 (CJK 폭 계산, 박스 표)
│   ├── live_refresh.py         # 생산라인 실시간 보기용 화면 갱신/키 입력 대기
│   ├── progress_bar.py         # 진행률/잔여율 막대 렌더링
│   └── input_helpers.py        # 입력 검증/재입력, 0=취소 프롬프트 헬퍼
├── tools/                  # seed_samples.py (더미 데이터 시드 스크립트, 선택 도구)
└── main.py                 # 진입점 (조립 + 메인 메뉴 루프)
tests/
data/                       # 런타임 JSON 데이터 (git에 커밋하지 않음)
```

의존 방향: `controllers` → `services` → `repositories`/`models`, `controllers` → `views`.
자세한 설계와 핵심 도메인 규칙(주문 상태 전이, 생산 완료 후 잉여 재고 처리 등)은
[PRD.md](./PRD.md)와 [CLAUDE.md](./CLAUDE.md)를 참고하세요.

## 핵심 규칙 요약

- **재고 차감은 승인(`CONFIRMED` 전환) 시점**에 이루어집니다.
- **생산 완료 시 실 생산량은 전량 재고에 입고된 뒤 주문 수량만큼만 차감**되어, 남는
  차이는 잉여 재고로 남습니다. (예: 주문 16, 수율 0.8 → 실생산량 20 입고 → 16 차감 →
  재고 4 잉여)
- 생산 큐는 **단일 라인 FIFO**입니다.
- 모니터링은 `REJECTED` 주문을 집계에서 제외하며, 재고 상태는 `stock == 0` → 고갈
  (최우선), 잔여율 ≥ 50% → 여유, 그 외 → 부족 순서로 판정합니다.

## 4개 PoC 저장소와의 관계

이 저장소는 아래 PoC 저장소에서 개별 검증한 패턴을 재사용/확장합니다.

- `ConsoleMVC-JinjePark-22029910` — MVC 계층 분리, Fake View 테스트 패턴
- `DataPersistence-JinjePark-22029910` — JSON 파일 Repository (CRUD, 원자적 쓰기)
- `DummyDataGenerator-JinjePark-22029910` — 시드 가능한 더미 데이터 생성 패턴
- `DataMonitor-JinjePark-22029910` — 모니터링 집계 로직과 판정 기준
