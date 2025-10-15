# Tests Directory

All tests for the Hotel Sales AI Agent project.

## Structure

```
tests/
├── unit/              # Unit tests
│   ├── agent/         # Agent core tests (orchestrator, planner, runtime)
│   ├── calendar/      # Calendar tools tests (date resolver, holidays, weekends)
│   ├── pms/           # PMS tools tests
│   └── pms_src/       # PMS abstraction layer tests (minihotel, ezgo)
├── integration/       # Integration tests (multiple components)
└── e2e/              # End-to-end tests (full workflows)
```

## Running Tests

### Run all tests:
```bash
./run_tests.sh
```

### Run specific test pattern:
```bash
./run_tests.sh calendar      # Run all calendar tests
./run_tests.sh orchestrator  # Run orchestrator tests
```

### Run with pytest directly:
```bash
source venv/bin/activate
pytest tests/ -v                    # All tests
pytest tests/unit/calendar/ -v     # Calendar tests only
pytest tests/unit/agent/ -v        # Agent tests only
```

## Test Categories

- **unit/agent**: Tests for orchestrator, planner, runtime, and tool planner
- **unit/calendar**: Tests for date resolver, holiday resolver, weekend checker
- **unit/pms**: Tests for PMS tool wrappers
- **unit/pms_src**: Tests for PMS abstraction layer (MiniHotel, Ezgo APIs)
- **integration**: Tests for multiple components working together
- **e2e**: Full conversation flows and end-to-end scenarios
