from tests.test_operator import DATA_CREATE, DATA_DEFAULT, DATA_UPDATE, build_cm, rename_arn_keys
from lib import create_mapping, delete_mapping, update_mapping, AuthMappingList, Event, EventType
from lib.worker import get_config_map, write_config_map, update_mapping_status
from unittest.mock import MagicMock
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
    mappings = AuthMappingList(spec["mappings"])
    event = Event(event_type=EventType.CREATE, object_name="test", mappings=mappings)
    create_mapping(event, logger)
    lib.worker.get_config_map.assert_called_once()
    lib.worker.write_config_map.assert_called_once()
    lib.worker.update_mapping_status.assert_called_once()
    config_map, _ = lib.worker.write_config_map.call_args
   # import pdb; pdb.set_trace()
    assert isinstance(config_map[0], kubernetes.client.V1ConfigMap)
    data = {
        "mapRoles": yaml.dump(
            rename_arn_keys([DATA_DEFAULT, DATA_CREATE]), default_flow_style=False
        )
    }
    assert config_map[0].data == data

def test_update_mapping(mocker):
    mocker.patch("lib.worker.get_config_map")
    mocker.patch("lib.worker.write_config_map")
    mocker.patch("lib.worker.write_last_handled_mapping")
    mocker.patch("lib.worker.update_mapping_status")
    lib.worker.get_config_map.return_value = build_cm()
    lib.worker.write_config_map.return_value = build_cm(default=DATA_UPDATE)
    old_spec = {"mappings": [DATA_DEFAULT]}
    new_spec = {"mappings": [DATA_UPDATE]}
    logger = logging.Logger( __name__)
    mappings = AuthMappingList(new_spec["mappings"])
    mappings_old = AuthMappingList(old_spec["mappings"])
    event = Event(event_type=EventType.DELETE, object_name="test", mappings=mappings, old_mappings=mappings_old)
    update_mapping(event, logger)
    lib.worker.update_mapping_status.assert_called_once()
    lib.worker.get_config_map.assert_called_once()
    lib.worker.write_config_map.assert_called_once()
    config_map, _ = lib.worker.write_config_map.call_args
    assert isinstance(config_map[0], kubernetes.client.V1ConfigMap)
    data = {
        "mapRoles": yaml.dump(rename_arn_keys([DATA_UPDATE]), default_flow_style=False)
    }
    assert config_map[0].data == data

def test_delete_mapping(mocker):
    mocker.patch("lib.worker.get_config_map")
    mocker.patch("lib.worker.write_config_map")
    mocker.patch("lib.worker.write_last_handled_mapping")
    lib.worker.get_config_map.return_value = build_cm(extra_data=DATA_CREATE)
    lib.worker.write_config_map.return_value = build_cm()
    logger = logging.Logger( __name__)
    spec = {"mappings": [DATA_CREATE]}
    mappings = AuthMappingList(spec["mappings"])
    event = Event(event_type=EventType.DELETE, object_name="test", mappings=mappings)
    delete_mapping(event, logger)
    lib.worker.get_config_map.assert_called_once()
    lib.worker.write_config_map.assert_called_once()
    config_map, _ = lib.worker.write_config_map.call_args
    assert isinstance(config_map[0], kubernetes.client.V1ConfigMap)
    data = {
        "mapRoles": yaml.dump(rename_arn_keys([DATA_DEFAULT]), default_flow_style=False)
    }
    assert config_map[0].data == data

def test_create_mapping_failed(mocker):
    mocker.patch("lib.worker.get_config_map")
    mocker.patch("lib.worker.write_config_map")
    mocker.patch("lib.worker.write_last_handled_mapping")
    mocker.patch("lib.worker.update_mapping_status")
    lib.worker.get_config_map.return_value = build_cm()
    lib.worker.write_config_map.return_value = build_cm(default={})
    logger = MagicMock()
    spec = {"mappings": [DATA_CREATE]}
    mappings = AuthMappingList(spec["mappings"])
    event = Event(event_type=EventType.CREATE, object_name="test", mappings=mappings)
    create_mapping(event, logger)
    logger.error.assert_called_once_with("Add Roles failed")
    lib.worker.update_mapping_status.assert_called_once()