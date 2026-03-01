import zigpy.types as t

from zhaquirks import LocalDataCluster

from zigpy.quirks.v2 import QuirkBuilder
from zigpy.quirks.v2.homeassistant import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfPower,
)
from zigpy.quirks.v2.homeassistant.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)
from zigpy.zcl import ClusterType
from zigpy.zcl.foundation import BaseAttributeDefs, ZCLAttributeDef
from zigpy.zcl.clusters.homeautomation import ElectricalMeasurement


class EWeLinkElectricalMeasurement(LocalDataCluster, ElectricalMeasurement):
    """Custom eWeLink plug cluster"""

    cluster_id = 0xFC11

    _CONSTANT_ATTRIBUTES = {
        ElectricalMeasurement.AttributeDefs.ac_current_multiplier.id: 1,
        ElectricalMeasurement.AttributeDefs.ac_current_divisor.id: 100,
        ElectricalMeasurement.AttributeDefs.ac_voltage_multiplier.id: 1,
        ElectricalMeasurement.AttributeDefs.ac_voltage_divisor.id: 1000,
        ElectricalMeasurement.AttributeDefs.ac_power_multiplier.id: 1,
        ElectricalMeasurement.AttributeDefs.ac_power_divisor.id: 1000,
    }

    class AttributeDefs(ElectricalMeasurement.AttributeDefs):
        """Custom eWeLink attributes"""

        current_reported = ZCLAttributeDef(
            id=0x7004,
            type=t.uint16_t,
            is_manufacturer_specific=True
        )

        voltage_reported = ZCLAttributeDef(
            id=0x7005,
            type=t.uint32_t,
            is_manufacturer_specific=True,
        )

        power_reported = ZCLAttributeDef(
            id=0x7006,
            type=t.uint32_t,
            is_manufacturer_specific=True,
        )

    def _update_attribute(self, attrid, value):
        super()._update_attribute(attrid, value)
        match attrid:
            case EWeLinkElectricalMeasurement.AttributeDefs.current_reported.id:
                self._update_attribute(
                    ElectricalMeasurement.AttributeDefs.rms_current.id,
                    value
                )
            case EWeLinkElectricalMeasurement.AttributeDefs.voltage_reported.id:
                self._update_attribute(
                    ElectricalMeasurement.AttributeDefs.rms_voltage.id, value
                )
            case EWeLinkElectricalMeasurement.AttributeDefs.power_reported.id:
                self._update_attribute(
                    ElectricalMeasurement.AttributeDefs.active_power.id,
                    value
                )


(
    QuirkBuilder("eWeLink", "CK-BL702-SWP-01(7020)")
    .firmware_version_filter(min_version=0x00001002)
    .removes(ElectricalMeasurement.cluster_id, cluster_type=ClusterType.Client)
    .adds(EWeLinkElectricalMeasurement)
    .sensor(
        endpoint_id=1,
        cluster_id=EWeLinkElectricalMeasurement.cluster_id,
        attribute_name=EWeLinkElectricalMeasurement.AttributeDefs.current_reported.name,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.CURRENT,
        unit=UnitOfElectricCurrent.AMPERE,
        divisor=100,
        fallback_name="Current",
    )
    .sensor(
        endpoint_id=1,
        cluster_id=EWeLinkElectricalMeasurement.cluster_id,
        attribute_name=EWeLinkElectricalMeasurement.AttributeDefs.voltage_reported.name,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.VOLTAGE,
        unit=UnitOfElectricPotential.VOLT,
        divisor=1000,
        fallback_name="Voltage",
    )
    .sensor(
        endpoint_id=1,
        cluster_id=EWeLinkElectricalMeasurement.cluster_id,
        attribute_name=EWeLinkElectricalMeasurement.AttributeDefs.power_reported.name,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        unit=UnitOfPower.WATT,
        divisor=1000,
        fallback_name="Power",
    )
    .add_to_registry()
)
