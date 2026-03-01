import zigpy.types as t
from typing import Final

from zigpy.quirks import CustomCluster
from zigpy.zcl.clusters.homeautomation import ElectricalMeasurement
from zigpy.zcl.foundation import BaseAttributeDefs, ZCLAttributeDef

from zigpy.quirks.v2 import SensorStateClass, SensorDeviceClass, QuirkBuilder
from zigpy.quirks.v2.homeassistant import (
    UnitOfElectricCurrent,
    UnitOfPower,
    UnitOfElectricPotential,
)


class EWeLinkElectricalMeasurement(CustomCluster, ElectricalMeasurement):
    """eWeLink electrical measurement"""

    AC_VOLTAGE_MULTIPLIER = 0x0600
    AC_VOLTAGE_DIVISOR = 0x0601
    AC_CURRENT_MULTIPLIER = 0x0602
    AC_CURRENT_DIVISOR = 0x0603
    AC_POWER_MULTIPLIER = 0x0604
    AC_POWER_DIVISOR = 0x0605

    _CONSTANT_ATTRIBUTES = {
        AC_VOLTAGE_MULTIPLIER: 1,
        AC_VOLTAGE_DIVISOR: 1000,
        AC_CURRENT_MULTIPLIER: 1,
        AC_CURRENT_DIVISOR: 1000,
        AC_POWER_MULTIPLIER: 1,
        AC_POWER_DIVISOR: 1000,
    }

    cluster_id = 0xFC11

    class AttributeDefs(BaseAttributeDefs):
        """Custom eWeLink attributes definitions."""

        # rms_current
        current_reported: Final = ZCLAttributeDef(id=0x7004, type=t.uint16_t)
        # rms_voltage
        voltage_reported: Final = ZCLAttributeDef(id=0x7005, type=t.uint16_t)
        # active_power
        power_reported: Final = ZCLAttributeDef(id=0x7006, type=t.uint16_t)

    def _update_attribute(self, attrid, value):
        super()._update_attribute(attrid, value)
        if attrid == EWeLinkElectricalMeasurement.AttributeDefs.current_reported.id:
            self.endpoint.electrical_measurement._update_attribute(
                ElectricalMeasurement.AttributeDefs.rms_current.id, value
            )
        elif attrid == EWeLinkElectricalMeasurement.AttributeDefs.voltage_reported.id:
            self.endpoint.electrical_measurement._update_attribute(
                ElectricalMeasurement.AttributeDefs.rms_voltage.id, value
            )
        elif attrid == EWeLinkElectricalMeasurement.AttributeDefs.power_reported.id:
            self.endpoint.electrical_measurement._update_attribute(
                ElectricalMeasurement.AttributeDefs.active_power.id, value
            )


(
    QuirkBuilder("eWeLink", "CK-BL702-SWP-01(7020)")
    .adds(EWeLinkElectricalMeasurement, endpoint_id=1)
    # .sensor(
    #     endpoint_id=1,
    #     cluster_id=EWeLinkElectricalMeasurement.cluster_id,
    #     attribute_name=EWeLinkElectricalMeasurement.AttributeDefs.current_reported.name,
    #     state_class=SensorStateClass.MEASUREMENT,
    #     device_class=SensorDeviceClass.CURRENT,
    #     unit=UnitOfElectricCurrent.AMPERE,
    #     divisor=1000,
    #     fallback_name="Current",
    # )
    # .sensor(
    #     endpoint_id=1,
    #     cluster_id=EWeLinkElectricalMeasurement.cluster_id,
    #     attribute_name=EWeLinkElectricalMeasurement.AttributeDefs.voltage_reported.name,
    #     state_class=SensorStateClass.MEASUREMENT,
    #     device_class=SensorDeviceClass.VOLTAGE,
    #     unit=UnitOfElectricPotential.VOLT,
    #     divisor=1000,
    #     fallback_name="Voltage",
    # )
    # .sensor(
    #     endpoint_id=1,
    #     cluster_id=EWeLinkElectricalMeasurement.cluster_id,
    #     attribute_name=EWeLinkElectricalMeasurement.AttributeDefs.power_reported.name,
    #     state_class=SensorStateClass.MEASUREMENT,
    #     device_class=SensorDeviceClass.POWER,
    #     unit=UnitOfPower.WATT,
    #     divisor=1000,
    #     fallback_name="Power",
    # )
    .add_to_registry()
)
