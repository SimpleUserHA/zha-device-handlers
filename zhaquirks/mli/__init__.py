"""Mueller Licht International."""
from zhaquirks import PowerConfigurationCluster


class PowerConfiguration2AAACluster(PowerConfigurationCluster):
    """Updating Power attributes 2 AAA."""

    BATTERY_SIZES = 0x0031
    BATTERY_QUANTITY = 0x0033
    BATTERY_RATED_VOLTAGE = 0x0034

    _CONSTANT_ATTRIBUTES = {
        BATTERY_SIZES: 4,
        BATTERY_QUANTITY: 2,
        BATTERY_RATED_VOLTAGE: 15,
    }
