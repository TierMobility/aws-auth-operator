from tests.test_operator import (
    DATA_CREATE,
    DATA_DEFAULT,
    DATA_UPDATE,
    DATA_NOT_CONTAINED,
)
from lib.mappings import AuthMappingList
from typing import Dict


def test_mapping_equality():
    mapping1 = AuthMappingList([DATA_DEFAULT])
    mapping2 = AuthMappingList([DATA_DEFAULT])

    assert mapping1 == mapping2


def test_mapping_inequality():
    mapping1 = AuthMappingList([DATA_DEFAULT])
    mapping2 = AuthMappingList([DATA_CREATE])

    assert mapping1 != mapping2


def test_mapping_merge():
    mapping1 = AuthMappingList([DATA_DEFAULT])
    mapping2 = AuthMappingList([DATA_CREATE])
    mapping1.merge_mappings(mapping2)
    print(mapping1.auth_mappings.values())
    print([DATA_DEFAULT, DATA_CREATE])
    assert mapping1 == AuthMappingList([DATA_DEFAULT, DATA_CREATE])


def test_mapping_remove():
    mapping1 = AuthMappingList([DATA_DEFAULT, DATA_CREATE])
    mapping2 = AuthMappingList([DATA_CREATE])
    mapping1.remove_mappings(mapping2)
    print(mapping1.auth_mappings.values())
    print([DATA_DEFAULT, DATA_CREATE])
    assert mapping1 == AuthMappingList([DATA_DEFAULT])


def test_contains():
    mapping1 = AuthMappingList([DATA_DEFAULT, DATA_CREATE])
    mapping2 = AuthMappingList([DATA_CREATE])

    assert mapping2 in mapping1


def test_not_contains():
    mapping1 = AuthMappingList([DATA_DEFAULT, DATA_CREATE])
    mapping2 = AuthMappingList([DATA_NOT_CONTAINED])

    assert mapping2 not in mapping1


def test_mapping_with_string_usertype():
    data_default = DATA_DEFAULT.copy()
    data_default["usertype"] = "Role"
    mapping1 = AuthMappingList([data_default])
    mapping2 = AuthMappingList([DATA_DEFAULT])
    print(mapping1.auth_mappings)
    print(mapping2.auth_mappings)
    assert mapping1 == mapping2


def test_get_values():
    mapping1 = AuthMappingList([DATA_DEFAULT, DATA_CREATE])
    value_dict = mapping1.get_values()
    assert len(value_dict) == 2
    assert isinstance(value_dict[0], Dict)
    assert isinstance(value_dict[1], Dict)
    assert "arn" in value_dict[0] and value_dict[0]["arn"] == DATA_DEFAULT["arn"]
    assert (
        "usertype" in value_dict[0]
        and value_dict[0]["usertype"] == DATA_DEFAULT["usertype"].name
    )
