"""Smoke tests for register cache fixtures derived from a live GIV-HY5.0 Gen3 inverter."""


def test_fixture_produces_valid_inverter():
    from givenergy_modbus_async.model.inverter import Inverter

    from tests.fixtures.register_data import make_inverter_cache

    cache = make_inverter_cache()
    inv = Inverter(cache)
    assert inv.serial_number == "FA2424G403"
    assert inv.firmware_version == "D0.316-A0.316"
    assert inv.battery_percent == 100
    assert inv.p_pv1 == 1021
