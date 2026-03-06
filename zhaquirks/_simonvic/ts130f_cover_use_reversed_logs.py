from typing import Final, Any

import zigpy.types as t
from zigpy.typing import UNDEFINED, UndefinedType

from zigpy.zcl.clusters.closures import WindowCovering
from zigpy.zcl import foundation
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


CURRENT_LIFT_PERC_ATTR_ID = WindowCovering.AttributeDefs.current_position_lift_percentage.id


class TuyaCoveringCluster(CustomCluster, WindowCovering):
    """
    Tuya covering cluster that manually writes the
    current_position_lift_percentage back to the device.
    While for home assistant 0=open and 100=closed, for the device 0=closed and
    100=open; therefore tuya_motor_reversal should be set to true so the device
    will report correct values.
    """

    class AttributeDefs(WindowCovering.AttributeDefs):
        tuya_motor_mode: Final = ZCLAttributeDef(
            id=0x8000,
            type=MotorMode,
        )
        tuya_moving_state: Final = ZCLAttributeDef(
            id=0xF000,
            type=MovingState,
        )
        tuya_calibrated: Final = ZCLAttributeDef(
            id=0xF001,
            type=t.enum8,
        )
        tuya_motor_reversal: Final = ZCLAttributeDef(
            id=0xF002,
            type=t.enum8,
        )
        tuya_calibration_time: Final = ZCLAttributeDef(
            id=0xF003,
            type=t.uint16_t,
        )

    async def read_attributes_raw(
        self,
        attributes,
        manufacturer=None,
        **kwargs
    ):
        """
        When we try to read the current_position_lift_percentage from the
        device, if a cached value is present, which is supposedly correct since
        it has been previously updated when the device reported it e.g. during
        a movement, it is written back to the device.
        """
        self.debug(
            f"[simonvic] read_attributes_raw() attributes={attributes} manufacturer={manufacturer}")
        self.debug(
            f"[simonvic] \t cached percent={self._attr_cache.get(CURRENT_LIFT_PERC_ATTR_ID)}")
        read_records = await super().read_attributes_raw(attributes, manufacturer, **kwargs)
        self.debug(
            f"[simonvic] \t read_records={read_records}")
        self.debug(
            f"[simonvic] \t cached percent={self._attr_cache.get(CURRENT_LIFT_PERC_ATTR_ID)}")
        for record in read_records.status_records:
            if record.attrid == CURRENT_LIFT_PERC_ATTR_ID:
                self.debug("[simonvic] \t CURRENT_LIFT_PERC_ATTR_ID found")
                cached_value = self._attr_cache.get(CURRENT_LIFT_PERC_ATTR_ID)
                if cached_value is None:
                    self.debug(
                        "[simonvic] \t\t cache miss. Returning remote value")
                else:
                    self.debug(f"[simonvic] \t\t cache hit {cached_value}")
                    if record.value.value != cached_value:
                        self.debug(
                            f"[simonvic] \t\t record.value.value {record.value.value} != {cached_value} cached_value")
                        self.debug(
                            f"[simonvic] \t\t Writing {cached_value} to remote")
                        write_result = await self.write_attributes({
                            "current_position_lift_percentage": cached_value
                        })  # TODO: pass manufacturer?
                        # TODO: invoking write_attributes causes _update_attributes to be invoked twice; eventually replace with a lower level write
                        self.debug(f"[simonvic] \t\t\twrite_result={
                                   write_result}")
                        self.debug(f"[simonvic] \t\t\tUpdating read record.value.value from {
                                   record.value.value} to cached_value {cached_value}")
                        record.value.value = cached_value
                break
        return read_records

    async def write_attributes(
        self,
        attributes: dict[str | int | foundation.ZCLAttributeDef, Any],
        manufacturer: int | UndefinedType | None = UNDEFINED,
        **kwargs,
    ) -> list[list[foundation.WriteAttributesStatusRecord]]:
        self.debug(f"[simonvic] write_attributes attributes={attributes}")
        self.debug(
            f"[simonvic] \t cached percent={self._attr_cache.get(CURRENT_LIFT_PERC_ATTR_ID)}")
        result = await super().write_attributes(attributes, manufacturer, **kwargs)
        self.debug(f"[simonvic] \t result={result}")
        self.debug(
            f"[simonvic] \t cached percent={self._attr_cache.get(CURRENT_LIFT_PERC_ATTR_ID)}")
        return result

    def _update_attribute(self, attrid, value):
        self.debug(
            f"[simonvic] _update_attribute attrid={attrid} value={value}")
        self.debug(
            f"[simonvic] \t cached percent={self._attr_cache.get(CURRENT_LIFT_PERC_ATTR_ID)}")
        super()._update_attribute(attrid, value)
        self.debug(
            f"[simonvic] \t cached percent={self._attr_cache.get(CURRENT_LIFT_PERC_ATTR_ID)}")

    async def command(
        self,
        command_id,
        *args,
        manufacturer=None,
        expect_reply=True,
        tsn=None
    ):
        self.debug(
            f"[simonvic] command command_id={command_id} args={args} expect_reply={expect_reply} tsn={tsn}")
        self.debug(
            f"[simonvic] \t cached percent={self._attr_cache.get(CURRENT_LIFT_PERC_ATTR_ID)}")
        if (
            command_id == WindowCovering.ServerCommandDefs.up_open.id
            or command_id == WindowCovering.ServerCommandDefs.down_close.id
        ):
            success, _ = await self.read_attributes(
                (self.AttributeDefs.tuya_motor_reversal.id,),
                manufacturer=manufacturer
            )
            try:
                is_reversed = success[self.AttributeDefs.tuya_motor_reversal.id]
                self.debug(f"[simonvic] \tis_reversed={is_reversed}")
                if is_reversed:
                    if command_id == WindowCovering.ServerCommandDefs.up_open.id:
                        command_id = WindowCovering.ServerCommandDefs.down_close.id
                    else:
                        command_id = WindowCovering.ServerCommandDefs.up_open.id
                    self.debug(f"[simonvic] \t\tnew command_id={command_id}")
            except KeyError:
                self.debug(
                    "[simonvic] \terror when reading tuya_motor_reversal")
        result = await super().command(
            command_id,
            *args,
            manufacturer=manufacturer,
            expect_reply=expect_reply,
            tsn=tsn,
        )
        self.debug(
            f"[simonvic] \t cached percent={self._attr_cache.get(CURRENT_LIFT_PERC_ATTR_ID)}")
        return result


(
    # TODO: use QuirkBuilder instead?
    TuyaQuirkBuilder("_TZ3210_dwytrmda", "TS130F")
    .replaces(TuyaCoveringCluster)
    .number(
        attribute_name=TuyaCoveringCluster.AttributeDefs.tuya_calibration_time.name,
        cluster_id=TuyaCoveringCluster.cluster_id,
        min_value=1,
        max_value=1500,  # A sensible max?
        step=0.1,
        multiplier=0.1,
        unit=UnitOfTime.SECONDS,
        device_class=NumberDeviceClass.DURATION,
        translation_key="calibration_vertical_run_time_up",
        fallback_name="Calibration vertical run time up",
        # initially_disabled=True,
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
        # initially_disabled=True,
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
        fallback_name="Moving state"
        # initially_disabled=True,
    )
    # .skip_configuration()
    .add_to_registry()
)
