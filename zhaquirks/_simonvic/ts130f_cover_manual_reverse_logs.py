from typing import Final, Any

import zigpy.types as t
from zigpy.typing import UNDEFINED, UndefinedType

from zigpy.zcl.clusters.closures import WindowCovering
from zigpy.zcl import foundation, AttributeReadEvent, AttributeReportedEvent, AttributeUpdatedEvent
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
    100=open; therefore the percentage value is inverted when reading/writing
    it from/to the device, and when sending the go_to_lift_percentage command
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.on_event(
            AttributeReadEvent.event_type,
            self._log_on_event
        )
        self.on_event(
            AttributeReportedEvent.event_type,
            self._handle_on_report_event
        )
        self.on_event(
            AttributeUpdatedEvent.event_type,
            self._log_on_event
        )

    def _log_on_event(
        self,
        event: AttributeReadEvent | AttributeUpdatedEvent
    ) -> None:
        self.info(f"[simonvic] on_event() event={event}")

    def _handle_on_report_event(
        self,
        event: AttributeReportedEvent
    ) -> None:
        """
        When the device report `tuya_moving_state` as `IDLE`, it means it has
        completed its movement; we write the lift percentage back to the device
        """
        self.info(f"[simonvic] on_event() event={event}")
        if (
            event.attribute_id == self.AttributeDefs.tuya_moving_state.id
            and event.value == MovingState.IDLE
        ):
            self.info(
                "[simonvic] on_event() \t writing lift percentage on device")
            cached_value = self._attr_cache.get(CURRENT_LIFT_PERC_ATTR_ID)
            self.info(f"[simonvic] on_event() \t cached_value={cached_value}")
            if cached_value is None:
                self.info("[simonvic] on_event() \t\t cache miss. Ignoring")
            else:
                self.info(f"[simonvic] on_event() \t\t cache hit. Writing 100 - {
                          cached_value} = {100 - cached_value}")
                self.create_catching_task(
                    self.write_attributes(
                        attributes={
                            "current_position_lift_percentage": 100 - cached_value
                        },
                        update_cache=False
                    )
                )

    async def read_attributes_raw(
        self,
        attributes,
        manufacturer=None,
        **kwargs
    ):
        """
        When we try to read the current_position_lift_percentage from the
        device, we invert the result and write back the value to the device.
        """
        self.info(
            f"[simonvic] read_attributes_raw() attributes={attributes} manufacturer={manufacturer}")
        self.info(
            f"[simonvic] read_attributes_raw() \t cached percent={self._attr_cache.get(CURRENT_LIFT_PERC_ATTR_ID)}")
        read_records = await super().read_attributes_raw(attributes, manufacturer, **kwargs)
        self.info(
            f"[simonvic] read_attributes_raw() \t read_records={read_records}")
        self.info(
            f"[simonvic] read_attributes_raw() \t cached percent={self._attr_cache.get(CURRENT_LIFT_PERC_ATTR_ID)}")
        for record in read_records.status_records:
            if record.attrid == CURRENT_LIFT_PERC_ATTR_ID:
                self.info(
                    "[simonvic] read_attributes_raw() \t CURRENT_LIFT_PERC_ATTR_ID found")
                self.info(
                    f"[simonvic] read_attributes_raw() \t read {record.value.value} but inverting it to {100 - record.value.value}")
                cached_value = self._attr_cache.get(CURRENT_LIFT_PERC_ATTR_ID)
                if cached_value is None:
                    # If we don't have a cached value, we can only return the
                    # value (inverted) read from the device (hoping it is not
                    # stale)
                    self.info(
                        f"[simonvic] read_attributes_raw() \t\t cache miss. Returning inverted remote value 100 - {record.value.value} = {100 - record.value.value}")
                    record.value.value = 100 - record.value.value
                else:
                    self.info(
                        f"[simonvic] read_attributes_raw() \t\t cache hit {cached_value}")
                    # If a cached value is present set it as result, which is
                    # supposedly correct since it has been previously updated
                    # when the device reported it (e.g. during a movement)
                    record.value.value = 100 - cached_value
                break
        self.info(
            f"[simonvic] read_attributes_raw() \t read_records={read_records}")
        return read_records

    async def write_attributes(
        self,
        attributes: dict[str | int | foundation.ZCLAttributeDef, Any],
        manufacturer: int | UndefinedType | None = UNDEFINED,
        **kwargs,
    ) -> list[list[foundation.WriteAttributesStatusRecord]]:
        self.info(
            f"[simonvic] write_attributes attributes={attributes}")
        self.info(
            f"[simonvic] write_attributes \t cached percent={self._attr_cache.get(CURRENT_LIFT_PERC_ATTR_ID)}")
        result = await super().write_attributes(attributes, manufacturer, **kwargs)
        self.info(
            f"[simonvic] write_attributes \t result={result}")
        self.info(
            f"[simonvic] write_attributes \t cached percent={self._attr_cache.get(CURRENT_LIFT_PERC_ATTR_ID)}")
        return result

    def _update_attribute(self, attrid, value):
        self.info(
            f"[simonvic] _update_attribute attrid={attrid} value={value}")
        self.info(
            f"[simonvic] _update_attribute \t cached percent={self._attr_cache.get(CURRENT_LIFT_PERC_ATTR_ID)}")
        if attrid == CURRENT_LIFT_PERC_ATTR_ID:
            self.info(
                f"[simonvic] _update_attribute \t inverting value from {value} to {100 - value}")
            value = 100 - value
        super()._update_attribute(attrid, value)
        self.info(
            f"[simonvic] _update_attribute \t cached percent={self._attr_cache.get(CURRENT_LIFT_PERC_ATTR_ID)}")

    async def command(
        self,
        command_id,
        *args,
        manufacturer=None,
        expect_reply=True,
        tsn=None
    ):
        self.info(
            f"[simonvic] command command_id={command_id} args={args} expect_reply={expect_reply} tsn={tsn}")
        self.info(
            f"[simonvic] command \t cached percent={self._attr_cache.get(CURRENT_LIFT_PERC_ATTR_ID)}")
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
                self.info(f"[simonvic] command \t is_reversed={is_reversed}")
                if is_reversed:
                    if command_id == WindowCovering.ServerCommandDefs.up_open.id:
                        command_id = WindowCovering.ServerCommandDefs.down_close.id
                    else:
                        command_id = WindowCovering.ServerCommandDefs.up_open.id
                    self.info(
                        f"[simonvic] command \t\t new command_id={command_id}")
            except KeyError:
                self.info(
                    "[simonvic] \terror when reading tuya_motor_reversal")
        if command_id == WindowCovering.ServerCommandDefs.go_to_lift_percentage.id:
            self.info(
                f"[simonvic] command \t Inverting percentage command from {args[0]} to {100 - args[0]}")
            v = (100 - args[0],)
            return await super().command(
                command_id,
                *v,
                manufacturer=manufacturer,
                expect_reply=expect_reply,
                tsn=tsn
            )
        result = await super().command(
            command_id,
            *args,
            manufacturer=manufacturer,
            expect_reply=expect_reply,
            tsn=tsn,
        )
        self.info(
            f"[simonvic] command \t cached percent={self._attr_cache.get(CURRENT_LIFT_PERC_ATTR_ID)}")
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
