import aws_auth
import kubernetes
import yaml
import copy
import logging
import pytest
import kopf
from unittest.mock import MagicMock
import queue
from lib.mappings import UserType
from lib.worker import EventType

DATA_DEFAULT = {
    "arn": "arn:aws:iam::6666:role/test-role-0",
    "username": "test-role-0",
    "usertype": UserType.Role,
    "groups": ["viewers"],
}

DATA_CREATE = {
    "arn": "arn:aws:iam::6666:role/test-role-1",
    "username": "test-role-1",
    "usertype": UserType.Role,
    "groups": ["viewers"],
}

DATA_UPDATE = {
    "arn": "arn:aws:iam::6666:role/test-role-1",
    "username": "test-role-1",
    "usertype": UserType.Role,
    "groups": ["viewers", "editors"],
}

DATA_NOT_CONTAINED = {
    "arn": "arn:aws:iam::6666:role/test-role-2",
    "username": "test-role-2",
    "usertype": UserType.Role,
    "groups": ["viewers", "editors"],
}

CM_DATA_1 = {
    "rolearn": "arn:aws:iam::6666:role/test-role-1",
    "username": "test-role-1",
    "groups": ["viewers"],
}

CM_DATA_2 = {
    "rolearn": "arn:aws:iam::6666:role/test-role-2",
    "username": "test-role-2",
    "groups": ["viewers", "editors"],
}

TEST_MEMO = kopf.Memo()
TEST_MEMO.event_queue = queue.Queue()
TEST_MEMO.event_thread = MagicMock()

logger = logging.getLogger()


def test_run():
    assert 1 == 1


def test_create(mocker):
    mocker.patch("aws_auth.get_protected_mapping")
    aws_auth.get_protected_mapping.return_value = {
        "spec": {"mappings": [DATA_NOT_CONTAINED]}
    }
    message = aws_auth.create_fn(
        logger,
        spec={"mappings": [DATA_CREATE]},
        meta={},
        name="test",
        memo=TEST_MEMO,
        kwargs={},
    )
    # asserts
    assert "Processing" == message["message"]
    assert not TEST_MEMO.event_queue.empty()
    assert TEST_MEMO.event_queue.get().event_type == EventType.CREATE
    aws_auth.get_protected_mapping.assert_called_once()


def test_delete(mocker):
    mocker.patch("aws_auth.get_protected_mapping")
    mocker.patch("aws_auth.get_config_map")
    message = aws_auth.delete_fn(
        logger,
        spec={"mappings": [DATA_CREATE]},
        meta={},
        name="test",
        memo=TEST_MEMO,
        kwargs={},
    )
    assert "Processing" == message["message"]
    assert not TEST_MEMO.event_queue.empty()
    assert TEST_MEMO.event_queue.get().event_type == EventType.DELETE
    aws_auth.get_protected_mapping.assert_called_once()


def test_update(mocker):
    mocker.patch("aws_auth.get_protected_mapping")
    mocker.patch("aws_auth.get_config_map")
    old = {"spec": {"mappings": [DATA_DEFAULT]}}
    new = {"spec": {"mappings": [DATA_UPDATE]}}
    message = aws_auth.update_fn(
        logger,
        old=old,
        new=new,
        spec={},
        diff={},
        name="test",
        memo=TEST_MEMO,
        kwargs={},
    )
    assert "Processing" == message["message"]
    assert not TEST_MEMO.event_queue.empty()
    assert TEST_MEMO.event_queue.get().event_type == EventType.UPDATE


@pytest.mark.skip(reason="no way of currently testing this")
def test_create_failed(mocker):
    with pytest.raises(kopf.PermanentError) as err:
        # mocker.patch("aws_auth.get_protected_mapping")
        # mocker.patch("aws_auth.get_config_map")
        # mocker.patch("aws_auth.write_config_map")
        # mocker.patch("aws_auth.write_last_handled_mapping")
        # aws_auth.get_config_map.return_value = build_cm()
        # aws_auth.write_config_map.return_value = build_cm(default={})
        aws_auth.create_fn(
            logger,
            spec={"mappings": [DATA_CREATE]},
            meta={},
            name="test",
            memo=TEST_MEMO,
            kwargs={},
        )

    assert "Add Roles failed" in str(err)


@pytest.mark.skip(reason="no way of currently testing this")
def test_update_failed(mocker):
    with pytest.raises(kopf.PermanentError) as err:
        mocker.patch("aws_auth.get_protected_mapping")
        mocker.patch("aws_auth.get_config_map")
        mocker.patch("aws_auth.write_config_map")
        mocker.patch("aws_auth.write_last_handled_mapping")
        aws_auth.get_config_map.return_value = build_cm()
        aws_auth.write_config_map.return_value = build_cm()
        old = {"spec": {"mappings": [DATA_DEFAULT]}}
        new = {"spec": {"mappings": [DATA_UPDATE]}}
        aws_auth.update_fn(
            logger,
            old=old,
            new=new,
            spec={},
            diff={},
            name="test",
            memo=TEST_MEMO,
            kwargs={},
        )

    assert "Update Roles failed" in str(err)


@pytest.mark.skip(reason="no way of currently testing this")
def test_delete_failed(mocker):
    with pytest.raises(kopf.PermanentError) as err:
        mocker.patch("aws_auth.get_protected_mapping")
        mocker.patch("aws_auth.get_config_map")
        mocker.patch("aws_auth.write_config_map")
        mocker.patch("aws_auth.write_last_handled_mapping")
        aws_auth.get_config_map.return_value = build_cm(extra_data=DATA_CREATE)
        aws_auth.write_config_map.return_value = build_cm(extra_data=DATA_CREATE)
        aws_auth.delete_fn(
            logger,
            spec={"mappings": [DATA_CREATE]},
            meta={},
            name="test",
            memo=TEST_MEMO,
            kwargs={},
        )

    assert "Delete Roles failed" in str(err)


def test_create_invalid_spec():
    message = aws_auth.create_fn(
        logger,
        spec={},
        meta={"object": {"name": "test"}},
        name="test",
        memo=TEST_MEMO,
        kwargs={},
    )
    assert "invalid schema {}" == message["message"]


def test_update_invalid_spec():
    old = {"spec": {"mappings": [DATA_DEFAULT]}}
    new = {}
    message = message = aws_auth.update_fn(
        logger,
        old=old,
        new=new,
        spec={},
        diff={},
        name="test",
        memo=TEST_MEMO,
        kwargs={},
    )
    assert "invalid schema {}" == message["message"]


def test_delete_invalid_spec():
    message = aws_auth.delete_fn(
        logger, spec={}, meta={}, name="test", memo=TEST_MEMO, kwargs={}
    )
    assert "invalid schema {}" == message["message"]


def test_startup(mocker):
    settings = kopf.OperatorSettings()
    mocker.patch("aws_auth.kopf.login_via_client")
    mocker.patch("aws_auth.get_protected_mapping")
    mocker.patch("aws_auth.get_config_map")
    mocker.patch("aws_auth.write_protected_mapping")
    mocker.patch("aws_auth.Worker")
    aws_auth.get_protected_mapping.return_value = None
    aws_auth.startup(logger, settings=settings, memo=TEST_MEMO)
    aws_auth.get_protected_mapping.assert_called_once()
    aws_auth.get_config_map.assert_called_once()
    aws_auth.write_protected_mapping.assert_called_once()
    assert not TEST_MEMO.event_queue.empty()
    assert TEST_MEMO.event_queue.get() == "Starting Operator ..."


def test_create_overwrite_protected_mapping(mocker):
    mocker.patch("aws_auth.get_protected_mapping")
    mocker.patch("aws_auth.get_config_map")
    mocker.patch("aws_auth.write_config_map")
    aws_auth.get_protected_mapping.return_value = {"spec": {"mappings": [DATA_CREATE]}}
    aws_auth.get_config_map.return_value = build_cm()
    aws_auth.write_config_map.return_value = build_cm(extra_data=DATA_CREATE)
    message = aws_auth.create_fn(
        logger,
        spec={"mappings": [DATA_CREATE]},
        meta={},
        name="test",
        memo=TEST_MEMO,
        kwargs={},
    )
    assert "overwriting protected mapping not possible" == message["message"]
    # asserts
    aws_auth.get_config_map.assert_not_called()
    aws_auth.write_config_map.assert_not_called()
    aws_auth.get_protected_mapping.assert_called_once()


def test_log_config_map_change(mocker):
    mocker.patch("aws_auth.get_last_handled_mapping")
    aws_auth.get_last_handled_mapping.return_value = {
        "spec": {"mappings": [DATA_CREATE]}
    }
    aws_auth.log_config_map_change(logger, {"data": CM_DATA_2})


def build_cm(default=DATA_DEFAULT, extra_data=None):
    data = [default]
    if extra_data is not None:
        data.append(extra_data)
    cm = kubernetes.client.V1ConfigMap(
        data={"mapRoles": yaml.dump(rename_arn_keys(data), default_flow_style=False)}
    )
    cm.metadata = kubernetes.client.V1ObjectMeta()
    return cm


def rename_arn_keys(mappings):
    result = []
    if not mappings[0]:
        return result
    for mapping_orig in mappings:
        mapping = copy.copy(mapping_orig)
        if mapping["usertype"] == UserType.Role:
            mapping["rolearn"] = mapping.pop("arn")
        else:
            mapping["userarn"] = mapping.pop("arn")
        mapping.pop("usertype")
        result.append(mapping)
    return result
