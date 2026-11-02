import zigpy.types as t
from typing import Final
from zigpy.zcl import ClusterType
from zigpy.zcl.foundation import (
    ZCLAttributeDef,
    BaseAttributeDefs,
)
from zigpy.zcl.clusters.security import IasZone
from zigpy.zcl.clusters.general import KeepAlive
from zigpy.quirks import CustomCluster
from zigpy.quirks.v2 import QuirkBuilder


class IlluminationStatus(t.enum8):
    Dark = 0x00
    Light = 0x01


class OccupancySensitivity(t.enum8):
    Low = 0x01  # 2.5m
    Medium = 0x02  # 3.5m
    High = 0x03  # 4m


class SonoffIlluminanceCluster(CustomCluster):
    cluster_id: Final[t.uint16_t] = 0xFC11
    ep_attribute = "sonoff_manufacturer"

    class AttributeDefs(BaseAttributeDefs):
        last_illumination_state: Final = ZCLAttributeDef(
            id=0x2001,
            type=IlluminationStatus,
            manufacturer_code=None,
        )


# class SonoffOccupancyCluster(CustomCluster):
#
#     cluster_id: Final[t.uint16_t] = OccupancySensing.cluster_id
#     name: Final = OccupancySensing.name
#     ep_attribute: Final = OccupancySensing.ep_attribute
#
#     class AttributeDefs(BaseAttributeDefs):
#         occupancy: Final = ZCLAttributeDef(
#             id=OccupancySensing.AttributeDefs.occupancy.id,
#             type=Occupancy,
#             access="r",  # NOTE: report unsupported
#         )
#         occupancy_sensor_type_bitmap: Final = ZCLAttributeDef(
#             id=OccupancySensing.AttributeDefs.occupancy_sensor_type_bitmap.id,
#             type=OccupancySensorTypeBitmap,
#             access="r",
#         )
#         ultrasonic_o_to_u_delay: Final = ZCLAttributeDef(
#             id=OccupancySensing.AttributeDefs.ultrasonic_o_to_u_delay.id,
#             type=t.uint16_t,
#             access="rw"
#         )
#         ultrasonic_u_to_o_threshold: Final = ZCLAttributeDef(
#             id=OccupancySensing.AttributeDefs.ultrasonic_u_to_o_threshold.id,
#             type=t.uint8_t,
#             access="rw"
#         )
#
#     # def __init__(self, *args, **kwargs):
#     #     super().__init__(*args, **kwargs)
#     #     self.on_event(AttributeReadEvent.event_type, self._log_on_event)
#     #     self.on_event(AttributeReportedEvent.event_type, self._log_on_event)
#     #     self.on_event(AttributeUpdatedEvent.event_type, self._log_on_event)
#     #
#     # def _log_on_event(
#     #     self,
#     #     event: AttributeReadEvent | AttributeUpdatedEvent | AttributeReportedEvent
#     # ) -> None:
#     #     self.info(
#     #         f"[simonvic] SonoffOccupancyCluster::on_event() event={event}"
#     #     )


(
    QuirkBuilder("SONOFF", "SNZB-06P")
    .removes(IasZone.cluster_id)
    .replaces(SonoffIlluminanceCluster)
    # .replaces(SonoffOccupancyCluster)
    .adds(KeepAlive, cluster_type=ClusterType.Client, endpoint_id=1)
    # .sensor(
    #     cluster_id=SonoffIlluminanceCluster.cluster_id,
    #     attribute_name=SonoffIlluminanceCluster.AttributeDefs.last_illumination_state.name,
    #     device_class=SensorDeviceClass.ENUM,
    #     translation_key="last_illumination_state",
    #     fallback_name="Last illumination state",
    # )
    # .enum(
    #     cluster_id=SonoffIlluminanceCluster.cluster_id,
    #     attribute_name=SonoffIlluminanceCluster.AttributeDefs.illumination.name,
    #     enum_class=IlluminationStatus,
    #     entity_type=EntityType.STANDARD,
    #     entity_platform=EntityPlatform.SENSOR,
    #     translation_key="last_illumination_state",
    #     fallback_name="Last illumination state",
    # )
    # .number(
    #     attribute_name=OccupancySensing.AttributeDefs.ultrasonic_o_to_u_delay.name,
    #     cluster_id=OccupancySensing.cluster_id,
    #     min_value=15,
    #     max_value=60,
    #     unit=UnitOfTime.SECONDS,
    #     device_class=NumberDeviceClass.DURATION,
    #     translation_key="occupancy_timeout",
    #     fallback_name="Occupancy timeout",
    # )
    # .enum(
    #     attribute_name=OccupancySensing.AttributeDefs.ultrasonic_u_to_o_threshold.name,
    #     enum_class=OccupancySensitivity,
    #     cluster_id=OccupancySensing.cluster_id,
    #     translation_key="occupancy_sensitivity",
    #     fallback_name="Occupancy sensitivity",
    # )
    # .skip_configuration()
    .add_to_registry()
)
