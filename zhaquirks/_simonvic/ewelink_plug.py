import zigpy.types as t

from zhaquirks import LocalDataCluster

from zigpy.quirks.v2 import QuirkBuilder
from zigpy.zcl import ClusterType
from zigpy.zcl.foundation import BaseAttributeDefs, ZCLAttributeDef
from zigpy.zcl.clusters.homeautomation import ElectricalMeasurement


class EWeLinkElectricalMeasurement(LocalDataCluster):
    """Custom eWeLink plug cluster"""

    cluster_id = 0xFC11

    class AttributeDefs(BaseAttributeDefs):
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
                self.endpoint.electrical_measurement._update_attribute(
                    ElectricalMeasurement.AttributeDefs.rms_current.id,
                    value
                )
            case EWeLinkElectricalMeasurement.AttributeDefs.voltage_reported.id:
                self.endpoint.electrical_measurement._update_attribute(
                    ElectricalMeasurement.AttributeDefs.rms_voltage.id,
                    t.uint16_t(value / 1000)
                )
            case EWeLinkElectricalMeasurement.AttributeDefs.power_reported.id:
                self.endpoint.electrical_measurement._update_attribute(
                    ElectricalMeasurement.AttributeDefs.active_power.id,
                    t.uint16_t(value / 1000)
                )


class ElectricalMeasurementCluster(LocalDataCluster, ElectricalMeasurement):

    _CONSTANT_ATTRIBUTES = {
        ElectricalMeasurement.AttributeDefs.ac_current_multiplier.id: 1,
        ElectricalMeasurement.AttributeDefs.ac_current_divisor.id: 100,
        ElectricalMeasurement.AttributeDefs.ac_voltage_multiplier.id: 1,
        ElectricalMeasurement.AttributeDefs.ac_voltage_divisor.id: 1,
        ElectricalMeasurement.AttributeDefs.ac_power_multiplier.id: 1,
        ElectricalMeasurement.AttributeDefs.ac_power_divisor.id: 1,
    }


(
    QuirkBuilder("eWeLink", "CK-BL702-SWP-01(7020)")
    # .firmware_version_filter(min_version=0x00001002)
    .removes(ElectricalMeasurement.cluster_id, cluster_type=ClusterType.Client)
    .adds(ElectricalMeasurementCluster)
    .adds(EWeLinkElectricalMeasurement)
    .add_to_registry()
)
