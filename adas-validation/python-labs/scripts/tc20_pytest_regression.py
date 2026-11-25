import pytest
from common import REPORTS, setup
from tc02_voltage import check, VoltageError

@pytest.fixture
def voltage_validator():
    log = setup("tc20_pytest_regression")
    log.info("Fixture setup")
    yield check
    log.info("Fixture teardown")

@pytest.mark.parametrize("voltage", [9, 12, 16])
def test_valid(voltage_validator, voltage):
    voltage_validator(voltage)

@pytest.mark.parametrize("voltage", [8.99, 16.01])
def test_invalid(voltage_validator, voltage):
    with pytest.raises(VoltageError, match="outside"):
        voltage_validator(voltage)

if __name__ == "__main__":
    setup("tc20_pytest_regression")
    raise SystemExit(pytest.main([__file__, "-v", "--junitxml",
                                 str(REPORTS / "tc20_junit.xml")]))
