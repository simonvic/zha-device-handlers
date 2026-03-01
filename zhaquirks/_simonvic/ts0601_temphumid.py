"""Tuya temp and humidity sensors."""

from zigpy.quirks.v2 import EntityType
import zigpy.types as t

from zhaquirks.tuya import TuyaPowerConfigurationCluster2AAA

from zhaquirks.tuya.builder import TuyaQuirkBuilder


class TuyaTempUnitConvert(t.enum8):
    """Tuya temperature unit convert enum."""

    Celsius = 0x00
    Fahrenheit = 0x01


(
    TuyaQuirkBuilder("_TZE284_9ern5sfh", "TS0601")
    .tuya_temperature(dp_id=1, scale=10)
    .tuya_humidity(dp_id=2, scale=10)
    .tuya_battery(dp_id=4)
    .tuya_enum(
        dp_id=9,
        attribute_name="display_unit",
        enum_class=TuyaTempUnitConvert,
        entity_type=EntityType.CONFIG,
        translation_key="display_unit",
        fallback_name="Display unit",
    )
    .adds(TuyaPowerConfigurationCluster2AAA)
    .tuya_enchantment(data_query_spell=True)
    .skip_configuration()
    .add_to_registry()
)
