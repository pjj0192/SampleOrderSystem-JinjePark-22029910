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
`data/orders.json`에 저장되며, 앱을 다시 실행해도 유지됩니다.

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
├── models/          # Sample, Order(+OrderStatus), ProductionJob
├── repositories/     # JSON CRUD Repository (Sample/Order)
├── services/          # SampleService, OrderService, ProductionService, MonitoringService
├── controllers/        # 메뉴별 Controller (View 프로토콜에만 의존)
├── views/                # 콘솔 입출력
├── tools/                 # seed_samples.py (더미 데이터 시드 스크립트, 선택 도구)
└── main.py                 # 진입점 (조립 + 메인 메뉴 루프)
tests/
data/                        # 런타임 JSON 데이터 (git에 커밋하지 않음)
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
