from tests.test_operator import DATA_CREATE, DATA_DEFAULT,  build_cm, rename_arn_keys
from lib import create_mapping, AuthMappingList, Event, EventType
from lib.worker import get_config_map, write_config_map
import logging
import lib
import kubernetes
import yaml

def test_create_mapping(mocker):
    mocker.patch("lib.worker.get_config_map")
    mocker.patch("lib.worker.write_config_map")
    mocker.patch("lib.worker.write_last_handled_mapping")
    mocker.patch("lib.worker.update_mapping_status")
    lib.worker.get_config_map.return_value = build_cm()
    lib.worker.write_config_map.return_value = build_cm(extra_data=DATA_CREATE)
    logger = logging.Logger( __name__)
    spec = {"mappings": [DATA_CREATE]}
    mappings_new = AuthMappingList(spec["mappings"])
    event = Event(event_type=EventType.CREATE, object_name="test", mappings=mappings_new)
    create_mapping(event, logger)
    lib.worker.get_config_map.assert_called_once()
    lib.worker.write_config_map.assert_called_once()
    config_map, _ = lib.worker.write_config_map.call_args
   # import pdb; pdb.set_trace()
    assert isinstance(config_map[0], kubernetes.client.V1ConfigMap)
    data = {
        "mapRoles": yaml.dump(
            rename_arn_keys([DATA_DEFAULT, DATA_CREATE]), default_flow_style=False
        )
    }
    assert config_map[0].data == data

def test_update_mapping():
    pass

def test_delete_mapping():
    pass