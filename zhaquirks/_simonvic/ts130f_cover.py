from typing import Final

import zigpy.types as t

from zigpy.zcl.clusters.closures import WindowCovering
from zigpy.zcl.foundation import ZCLAttributeDef
from zigpy.quirks import CustomCluster
from zigpy.quirks.v2 import SensorDeviceClass
from zigpy.quirks.v2.homeassistant import UnitOfTime
from zigpy.quirks.v2.homeassistant.number import NumberDeviceClass

from zhaquirks.tuya.builder import TuyaQuirkBuilder


class MotorMode(t.enum8):
    STRONG_MOTOR = 0x00
    WEAK_MOTOR = 0x01


class MovingState(t.enum8):
    OPENING = 0x00
    IDLE = 0x01
    CLOSING = 0x02


class TuyaCoveringCluster(CustomCluster, WindowCovering):
    """TuyaSmartCurtainWindowCoveringCluster: Allow to setup Window covering tuya devices."""

    class AttributeDefs(WindowCovering.AttributeDefs):
        """Attribute definitions."""

        tuya_motor_mode: Final = ZCLAttributeDef(id=0x8000, type=MotorMode)
        tuya_moving_state: Final = ZCLAttributeDef(id=0xF000, type=MovingState)
        tuya_calibrated: Final = ZCLAttributeDef(id=0xF001, type=t.enum8)
        tuya_motor_reversal: Final = ZCLAttributeDef(id=0xF002, type=t.enum8)
        tuya_calibration_time: Final = ZCLAttributeDef(id=0xF003, type=t.uint16_t)

    # async def write_attributes(
    #     self,
    #     attributes: dict[str | int | foundation.ZCLAttributeDef, Any],
    #     manufacturer: int | UndefinedType | None = UNDEFINED,
    #     **kwargs,
    # ) -> list[list[foundation.WriteAttributesStatusRecord]]:
    #     self.debug(f"[simonvic] write_attributes attributes={attributes}")
    #     result = await super().write_attributes(attributes, manufacturer, **kwargs)
    #     self.debug(f"[simonvic] write_attributes result={result}")
    #     return result

    def _update_attribute(self, attrid, value):
        # self.debug(f"[simonvic] _update_attribute attrid={attrid} value={value}")
        if attrid == WindowCovering.AttributeDefs.current_position_lift_percentage.id:
            value = 100 - value
        super()._update_attribute(attrid, value)

    async def command(
        self, command_id, *args, manufacturer=None, expect_reply=True, tsn=None
    ):
        """Override default command to invert percent lift value."""
        # self.debug(f"[simonvic] command command_id={command_id} args={args} expect_reply={expect_reply} tsn={tsn}")
        if command_id == WindowCovering.ServerCommandDefs.go_to_lift_percentage.id:
            v = (100 - args[0],)
            return await super().command(
                command_id,
                *v,
                manufacturer=manufacturer,
                expect_reply=expect_reply,
                tsn=tsn
            )
        return await super().command(
            command_id,
            *args,
            manufacturer=manufacturer,
            expect_reply=expect_reply,
            tsn=tsn,
        )


(
    # TODO: use QuirkBuilder instead?
    TuyaQuirkBuilder("_TZ3210_dwytrmda", "TS130F")
    .replaces(TuyaCoveringCluster)
    .number(
        attribute_name=TuyaCoveringCluster.AttributeDefs.tuya_calibration_time.name,
        cluster_id=TuyaCoveringCluster.cluster_id,
        min_value=1,
        max_value=1500,  # A sensible max?
        step=1,
        unit=UnitOfTime.SECONDS,
        device_class=NumberDeviceClass.DURATION,
        translation_key="calibration_vertical_run_time_up",
        fallback_name="Calibration vertical run time up",
    )
    .switch(
        attribute_name=TuyaCoveringCluster.AttributeDefs.tuya_motor_reversal.name,
        cluster_id=TuyaCoveringCluster.cluster_id,
        translation_key="reverse",
        fallback_name="Reverse",
    )
    .switch(
        attribute_name=TuyaCoveringCluster.AttributeDefs.tuya_calibrated.name,
        cluster_id=TuyaCoveringCluster.cluster_id,
        translation_key="calibrated",
        fallback_name="Calibrated",
    )
    .sensor(
        attribute_name=TuyaCoveringCluster.AttributeDefs.tuya_moving_state.name,
        cluster_id=TuyaCoveringCluster.cluster_id,
        device_class=SensorDeviceClass.ENUM,
        attribute_converter=lambda x: {
            MovingState.OPENING: "Opening",
            MovingState.IDLE: "Idle",
            MovingState.CLOSING: "Closing"
        }[x],
        # state_class=SensorStateClass.MEASUREMENT,
        fallback_name="Moving state"
    )
    # .skip_configuration()
    .add_to_registry()
)
