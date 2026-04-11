# ShopERP — Testing Standards

## Test Pyramid

```
       /   E2E   \       → Few: critical user flows
      /    API    \      → Medium: every endpoint
     / Unit Tests  \     → Many: every service method
    /________________\
```

## Tools

| Tool | Purpose |
|------|---------|
| pytest | Test runner, fixtures |
| pytest-asyncio | Async test support |
| pytest-cov | Coverage |
| httpx | FastAPI test client |

## Directory Structure

```
tests/
├── conftest.py               → Shared fixtures, DB setup, factories
├── unit/modules/<module>/
│   ├── test_service.py       → Every service method
│   └── test_schemas.py       → Validation edge cases
├── api/
│   └── test_<module>_api.py  → Every endpoint
└── fixtures/
    └── <module>_fixtures.py  → Test data factories
```

## Test Naming

```python
def test_<action>_<scenario>_<expected>():
    # Arrange — set up test data
    # Act — call the function
    # Assert — verify the result
```

## Rules

- Each test tests ONE thing.
- Arrange-Act-Assert structure, visually separated.
- Use fixtures and factories for test data.
- Every service method: one happy-path test + one error test minimum.
- Money tests verify exact integer amounts.
- Tests must be deterministic. No random data.

## Running

```bash
pytest                                        # All
pytest tests/unit/                            # Unit only
pytest tests/api/                             # API only
pytest --cov=src --cov-report=term-missing    # Coverage
```

## Coverage Targets

- Service layer: 90%+
- API layer: 80%+
- Overall: 80%+
