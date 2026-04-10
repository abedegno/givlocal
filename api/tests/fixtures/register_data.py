"""Sample register caches captured from a live GIV-HY5.0 Gen3 inverter."""

from givenergy_modbus_async.model.register import HR, IR
from givenergy_modbus_async.model.register_cache import RegisterCache


def make_inverter_cache() -> RegisterCache:
    """Return a RegisterCache populated with real inverter data."""
    cache = RegisterCache()
    cache["serial_number"] = "FA2424G403"

    # Holding Registers - config and settings
    hr_data = {
        0: 0x2001,  # device_type_code: Hybrid 5kW
        1: 3,
        2: 3122,  # module
        3: 0x0001,  # num_mppt/phases
        7: 1,  # enable_ammeter
        8: 0x4459,
        9: 0x3232,
        10: 0x3138,
        11: 0x4720,
        12: 0x3031,  # battery serial DY2218G001
        13: 0x4641,
        14: 0x3234,
        15: 0x3234,
        16: 0x4734,
        17: 0x3033,  # inverter serial FA2424G403
        18: 3020,  # first_battery_bms_firmware_version
        19: 316,  # dsp_firmware_version
        20: 0,  # enable_charge_target
        21: 316,  # arm_firmware_version
        27: 1,  # battery_power_mode (eco)
        30: 17,  # modbus_address
        34: 140,  # modbus_version (1.40)
        35: 26,
        36: 4,
        37: 9,
        38: 14,
        39: 13,
        40: 50,  # system_time
        47: 1,  # meter_type
        50: 100,  # active_power_rate
        53: 0x0100,  # enable_inverter=True
        54: 1,  # battery_type lithium
        55: 819,  # battery_nominal_capacity
        56: 800,
        57: 900,  # discharge_slot_1: 08:00-09:00
        59: 0,  # enable_discharge
        94: 2330,
        95: 530,  # charge_slot_1: 23:30-05:30
        96: 1,  # enable_charge
        110: 4,  # battery_soc_reserve
        111: 50,
        112: 50,  # charge/discharge limits
        114: 4,  # battery_discharge_min_power_reserve
        116: 100,  # charge_target_soc
    }
    for reg, val in hr_data.items():
        cache[HR(reg)] = val

    # Input Registers - live sensor data
    ir_data = {
        0: 1,  # status: Normal
        1: 2753,  # v_pv1: 275.3V
        2: 1659,  # v_pv2: 165.9V
        3: 4279,  # v_p_bus
        5: 2459,  # v_ac1: 245.9V
        6: 1,
        7: 18777,  # e_battery_throughput_total
        8: 37,  # i_pv1: 3.7A
        9: 37,  # i_pv2: 3.7A
        10: 64,  # i_ac1: 6.4A
        11: 0,
        12: 57242,  # e_pv_total
        13: 5004,  # f_ac1: 50.04Hz
        17: 48,  # e_pv1_day: 4.8kWh
        18: 1021,  # p_pv1: 1021W
        19: 30,  # e_pv2_day: 3.0kWh
        20: 619,  # p_pv2: 619W
        21: 1,
        22: 6370,  # e_grid_out_total
        24: 1440,  # p_inverter_out
        25: 35,  # e_grid_out_day: 3.5kWh
        26: 53,  # e_grid_in_day: 5.3kWh
        27: 0,
        28: 34172,  # e_inverter_in_total
        30: 1302,  # p_grid_out
        32: 2,
        33: 4216,  # e_grid_in_total
        35: 31,  # e_inverter_in_day
        36: 41,  # e_battery_charge_today: 4.1kWh
        37: 14,  # e_battery_discharge_today: 1.4kWh
        41: 380,  # temp_inverter_heatsink: 38.0C
        42: 138,  # p_load_demand
        43: 1485,  # p_grid_apparent
        44: 70,  # e_inverter_out_day: 7.0kWh
        45: 1,
        46: 13461,  # e_inverter_out_total
        49: 1,  # system_mode
        50: 5379,  # v_battery: 53.79V
        51: 19,  # i_battery: 0.19A
        52: 10,  # p_battery: 10W
        53: 2473,  # v_eps_backup
        54: 5005,  # f_eps_backup
        55: 391,  # temp_charger: 39.1C
        56: 180,  # temp_battery: 18.0C
        58: 601,  # i_grid_port: 6.01A
        59: 100,  # battery_percent: 100%
    }
    for reg, val in ir_data.items():
        cache[IR(reg)] = val

    return cache


def make_battery_cache() -> RegisterCache:
    """Return a RegisterCache populated with real battery data."""
    cache = RegisterCache()
    cache["serial_number"] = "DY2218G001"
    ir_data = {
        60: 3349,
        61: 3351,
        62: 3338,
        63: 3337,
        64: 3338,
        65: 3340,
        66: 3340,
        67: 3353,
        68: 3341,
        69: 3341,
        70: 3341,
        71: 3343,
        72: 3343,
        73: 3340,
        74: 3340,
        75: 3341,
        76: 186,
        77: 180,
        78: 181,
        79: 186,
        80: 53477,
        81: 202,
        82: 0,
        83: 53543,
        84: 0,
        85: 15526,
        86: 0,
        87: 16000,
        88: 0,
        89: 15233,
        96: 570,
        97: 16,
        98: 3020,
        100: 98,
        103: 186,
        104: 180,
        105: 41729,
        106: 42585,
        110: 0x4459,
        111: 0x3232,
        112: 0x3138,
        113: 0x4730,
        114: 0x3031,
    }
    for reg, val in ir_data.items():
        cache[IR(reg)] = val
    return cache
