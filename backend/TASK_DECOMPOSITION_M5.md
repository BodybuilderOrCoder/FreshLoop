# M5 — Real-time Inventory SSE

## Objective

Provide a Server-Sent Events (SSE) endpoint so frontend clients
can receive inventory changes for a selected active warehouse.

The first implementation uses periodic database snapshot comparison.
It detects persisted state changes with bounded polling latency.

## M5.0 — Task decomposition

- Define scope, event contracts, acceptance criteria and test plan.
- Preserve existing inventory GET endpoints.
- Keep each implementation checkpoint independently testable.

## M5.1 — SSE endpoint

- Add GET /api/warehouses/{warehouse_id}/inventory/events.
- Validate that the warehouse exists and is active.
- Send an initial inventory snapshot.
- Detect added, removed and changed inventory records.
- Scope all data to the requested warehouse.

Acceptance criteria:
- Existing warehouse and product endpoints remain unchanged.
- SSE messages use valid event/data framing.
- Event payloads contain product and stock identifiers and quantities.
- No update event is emitted when the observed stock state is unchanged.

## M5.2 — Stream lifecycle

- Validate the polling interval.
- Send periodic heartbeat comments.
- Stop processing when the client disconnects.
- Handle a warehouse becoming inactive during a stream.
- Avoid holding a database session for the entire stream lifetime.

Acceptance criteria:
- Database sessions are closed after each snapshot read.
- Disconnected clients do not keep polling indefinitely.
- Errors do not expose database credentials or internal exception details.

## M5.3 — Tests

- Test SSE event serialization.
- Test initial snapshots and stock-change detection.
- Test unchanged stock produces no update event.
- Test invalid/inactive warehouse handling.
- Test disconnect and stream lifecycle.
- Run relevant backend regression tests.

Acceptance criteria:
- Tests are repeatable and do not modify the development database.
- Integration tests use an isolated test database when required.

## M5.4 — Integration and documentation

- Document the SSE endpoint, event names and payload examples.
- Verify the stream against a running backend and database.
- Confirm existing inventory APIs still pass their tests.
- Record results and commit each completed checkpoint separately.

## Constraints

- Do not use test or mock stock values in the running endpoint.
- Do not change existing inventory response schemas unnecessarily.
- The initial implementation uses a configurable polling interval.
- SSE updates reflect persisted database state; polling can miss
  transient changes that occur and revert between snapshots.
- Authentication remains consistent with the existing inventory API
  until the project's authentication milestone is completed.
