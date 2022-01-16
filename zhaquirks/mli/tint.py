"""Tint remote."""
import logging

from zigpy.profiles import zha
from zigpy.quirks import CustomCluster, CustomDevice
from zigpy.zcl import foundation
from zigpy.zcl.clusters.general import (
    Basic,
    Groups,
    Identify,
    LevelControl,
    OnOff,
    Ota,
    Scenes,
)
from zigpy.zcl.clusters.lighting import Color
from zigpy.zcl.clusters.lightlink import LightLink

from zhaquirks import Bus, LocalDataCluster
from zhaquirks.const import (
    ARGS,
    ATTRIBUTE_ID,
    ATTRIBUTE_NAME,
    CLUSTER_ID,
    COMMAND,
    COMMAND_ATTRIBUTE_UPDATED,
    COMMAND_MOVE,
    COMMAND_STEP,
    COMMAND_STOP,
    DEVICE_TYPE,
    DIM_DOWN,
    DIM_UP,
    ENDPOINT_ID,
    ENDPOINTS,
    INPUT_CLUSTERS,
    MODELS_INFO,
    OUTPUT_CLUSTERS,
    PROFILE_ID,
    SHORT_PRESS,
    LONG_PRESS,
    LONG_RELEASE,
    VALUE,
)

CHANGE_SCENE = "change_scene"
COMMAND_MOVE_TO_COLOR_TEMP = "move_to_color_temp" # zhaquirks/const.py only knows COMMAND_MOVE_COLOR_TEMP
CURRENT_SCENE = "current_scene"
TINT_SCENE_ATTR = 0x4005

_LOGGER = logging.getLogger(__name__)


class TintRemoteScenesCluster(LocalDataCluster, Scenes):
    """Tint remote cluster."""

    cluster_id = Scenes.cluster_id

    def __init__(self, *args, **kwargs):
        """Init."""
        super().__init__(*args, **kwargs)

        self.endpoint.device.scene_bus.add_listener(self)

    def change_scene(self, value):
        """Change scene attribute to new value."""
        self._update_attribute(self.attridx[CURRENT_SCENE], value)


class TintRemoteBasicCluster(CustomCluster, Basic):
    """Tint remote cluster."""

    cluster_id = Basic.cluster_id

    def __init__(self, *args, **kwargs):
        """Init."""
        super().__init__(*args, **kwargs)

    def handle_cluster_general_request(self, hdr, args, *, dst_addressing=None):
        """Send write_attributes value to TintRemoteSceneCluster."""
        if hdr.command_id != foundation.Command.Write_Attributes:
            return

        attr = args[0][0]
        if attr.attrid != TINT_SCENE_ATTR:
            return

        value = attr.value.value
        self.endpoint.device.scene_bus.listener_event(CHANGE_SCENE, value)


class TintRemote(CustomDevice):
    """Tint remote quirk."""

    def __init__(self, *args, **kwargs):
        """Init."""
        self.scene_bus = Bus()
        super().__init__(*args, **kwargs)

    signature = {
        # endpoint=1 profile=260 device_type=2048 device_version=1 input_clusters=[0, 3, 4096]
        # output_clusters=[0, 3, 4, 5, 8, 25, 768, 4096]
        MODELS_INFO: [("MLI", "ZBT-Remote-ALL-RGBW")],
        ENDPOINTS: {
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.COLOR_CONTROLLER,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,  # 0
                    Identify.cluster_id,  # 3
                    LightLink.cluster_id,  # 4096
                ],
                OUTPUT_CLUSTERS: [
                    Basic.cluster_id,  # 0
                    Identify.cluster_id,  # 3
                    Groups.cluster_id,  # 4
                    OnOff.cluster_id,  # 6
                    LevelControl.cluster_id,  # 8
                    Ota.cluster_id,  # 25
                    Color.cluster_id,  # 768
                    LightLink.cluster_id,  # 4096
                ],
            },
        },
    }

    replacement = {
        ENDPOINTS: {
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.COLOR_CONTROLLER,
                INPUT_CLUSTERS: [
                    TintRemoteBasicCluster,  # 0
                    Identify.cluster_id,  # 3
                    LightLink.cluster_id,  # 4096
                ],
                OUTPUT_CLUSTERS: [
                    Basic.cluster_id,  # 0
                    Identify.cluster_id,  # 3
                    Groups.cluster_id,  # 4
                    TintRemoteScenesCluster,  # 5
                    OnOff.cluster_id,  # 6
                    LevelControl.cluster_id,  # 8
                    Ota.cluster_id,  # 25
                    Color.cluster_id,  # 768
                    LightLink.cluster_id,  # 4096
                ],
            },
        },

    device_automation_triggers = {

        # COLOR TEMPERATURE BUTTONS
        # todo:  validate correct handling for cycling through available values
        # WARMER
        (SHORT_PRESS, "COLOR_TEMP_WARM"): {
            COMMAND: COMMAND_MOVE_TO_COLOR_TEMP,
            CLUSTER_ID: 768,
            ENDPOINT_ID: 1,
            ARGS: [370, 10],
        },
        # COLDER
        (SHORT_PRESS, "COLOR_TEMP_COLD"): {
            COMMAND: COMMAND_MOVE_TO_COLOR_TEMP,
            CLUSTER_ID: 768,
            ENDPOINT_ID: 1,
            ARGS: [153, 10],
        },

        # BRIGHTNESS UP/DOWN BUTTONS
        (SHORT_PRESS, DIM_DOWN): {
            COMMAND: COMMAND_STEP,
            CLUSTER_ID: 8,
            ENDPOINT_ID: 1,
            ARGS: [1, 43, 10],
        },
        (LONG_PRESS, DIM_DOWN): {
            COMMAND: COMMAND_MOVE,
            CLUSTER_ID: 8,
            ENDPOINT_ID: 1,
            ARGS: [1, 100],
        },
        (SHORT_PRESS, DIM_UP): {
            COMMAND: COMMAND_STEP,
            CLUSTER_ID: 8,
            ENDPOINT_ID: 1,
            ARGS: [0, 43, 10],
        },
        (LONG_PRESS, DIM_UP): {
            COMMAND: COMMAND_MOVE,
            CLUSTER_ID: 8,
            ENDPOINT_ID: 1,
            ARGS: [0, 100],
        },
        # todo: check for correct definition, because stop command is being sent for up and down equally """
        (LONG_RELEASE): {
            COMMAND: COMMAND_STOP,
            CLUSTER_ID: 8,
            ENDPOINT_ID: 1,
            ARGS: [],
        },

        # SCENE BUTTONS

        # SCENE: worklight
        (SHORT_PRESS, "worklight"): {
            COMMAND: COMMAND_ATTRIBUTE_UPDATED,
            CLUSTER_ID: 5,
            ENDPOINT_ID: 1,
            ARGS: [{
                ATTRIBUTE_ID: 1,
                ATTRIBUTE_NAME: CURRENT_SCENE,
                VALUE: 3
                }],
        },
        # SCENE: sunset
        (SHORT_PRESS, "sunset"): {
            COMMAND: COMMAND_ATTRIBUTE_UPDATED,
            CLUSTER_ID: 5,
            ENDPOINT_ID: 1,
            ARGS: [{
                ATTRIBUTE_ID: 1,
                ATTRIBUTE_NAME: CURRENT_SCENE,
                VALUE: 1
                }],
        },
        # SCENE: party
        (SHORT_PRESS, "party"): {
            COMMAND: COMMAND_ATTRIBUTE_UPDATED,
            CLUSTER_ID: 5,
            ENDPOINT_ID: 1,
            ARGS: [{
                ATTRIBUTE_ID: 1,
                ATTRIBUTE_NAME: CURRENT_SCENE,
                VALUE: 2
                }],
        },

        # SCENE: nightlight
        (SHORT_PRESS, "nightlight"): {
            COMMAND: COMMAND_ATTRIBUTE_UPDATED,
            CLUSTER_ID: 5,
            ENDPOINT_ID: 1,
            ARGS: [{
                ATTRIBUTE_ID: 1,
                ATTRIBUTE_NAME: CURRENT_SCENE,
                VALUE: 6
                }],
        },
        # SCENE: campfire
        (SHORT_PRESS, "campfire"): {
            COMMAND: COMMAND_ATTRIBUTE_UPDATED,
            CLUSTER_ID: 5,
            ENDPOINT_ID: 1,
            ARGS: [{
                ATTRIBUTE_ID: 1,
                ATTRIBUTE_NAME: CURRENT_SCENE,
                VALUE: 4
                }],
        },
        # SCENE: romance
        (SHORT_PRESS, "romance"): {
            COMMAND: COMMAND_ATTRIBUTE_UPDATED,
            CLUSTER_ID: 5,
            ENDPOINT_ID: 1,
            ARGS: [{
                ATTRIBUTE_ID: 1,
                ATTRIBUTE_NAME: CURRENT_SCENE,
                VALUE: 5
                }],
        },
    }
