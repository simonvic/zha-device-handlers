import zigpy.types as t
from zigpy.zcl.foundation import ZCLAttributeDef
from typing import Final
from zigpy.profiles import zha
from zigpy.quirks import CustomDevice
from zhaquirks import LocalDataCluster
from zigpy.zcl.clusters.general import (
    Basic, GreenPowerProxy, Groups, Identify, OnOff, Ota, Scenes, Time
)
from zigpy.zcl.clusters.lightlink import LightLink
from zigpy.zcl.clusters.homeautomation import ElectricalMeasurement
from zhaquirks.const import (
    DEVICE_TYPE, ENDPOINTS, INPUT_CLUSTERS, MODELS_INFO, OUTPUT_CLUSTERS, PROFILE_ID
)


class EWeLinkElectricalMeasurement(LocalDataCluster, ElectricalMeasurement):

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

    class AttributeDefs(ElectricalMeasurement.AttributeDefs):

        # rms_current
        current_reported: Final = ZCLAttributeDef(id=0x7004, type=t.uint16_t)
        # rms_voltage
        voltage_reported: Final = ZCLAttributeDef(id=0x7005, type=t.uint16_t)
        # active_power
        power_reported: Final = ZCLAttributeDef(id=0x7006, type=t.uint16_t)

    def _update_attribute(self, attrid, value):
        super()._update_attribute(attrid, value)
        if attrid == 0x7004:
            self.endpoint.electrical_measurement._update_attribute(
                0x0508,  # ElectricalMeasurement.AttributeDefs.rms_current.id,
                value
            )
        elif attrid == 0x7005:
            self.endpoint.electrical_measurement._update_attribute(
                0x0505,  # ElectricalMeasurement.AttributeDefs.rms_voltage.id,
                value
            )
        elif attrid == 0x7006:
            self.endpoint.electrical_measurement._update_attribute(
                0x050B,  # ElectricalMeasurement.AttributeDefs.active_power.id,
                value
            )


class EWeLinkPlug(CustomDevice):
    signature = {
        MODELS_INFO: [("eWeLink", "CK-BL702-SWP-01(7020)")],
        ENDPOINTS: {
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.MAIN_POWER_OUTLET,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    Identify.cluster_id,
                    Groups.cluster_id,
                    Scenes.cluster_id,
                    OnOff.cluster_id,
                    LightLink.cluster_id,
                    EWeLinkElectricalMeasurement.cluster_id,
                    0xFC57
                ],
                OUTPUT_CLUSTERS: [
                    Time.cluster_id,
                    Ota.cluster_id,
                    ElectricalMeasurement.cluster_id
                ],
            },
            242: {
                PROFILE_ID: 41440,
                DEVICE_TYPE: 97,
                INPUT_CLUSTERS: [],
                OUTPUT_CLUSTERS: [GreenPowerProxy.cluster_id],
            },
        },
    }
    replacement = {
        ENDPOINTS: {
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.SMART_PLUG,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    Identify.cluster_id,
                    Groups.cluster_id,
                    Scenes.cluster_id,
                    OnOff.cluster_id,
                    LightLink.cluster_id,
                    EWeLinkElectricalMeasurement
                ],
                OUTPUT_CLUSTERS: [
                    Ota.cluster_id,
                    Time.cluster_id
                ],
            },
            242: {
                PROFILE_ID: 41440,
                DEVICE_TYPE: 97,
                INPUT_CLUSTERS: [],
                OUTPUT_CLUSTERS: [
                    GreenPowerProxy.cluster_id
                ],
            },
        },
    }
