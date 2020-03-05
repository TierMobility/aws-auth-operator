from lib.services import *
import pytest
import logging
import kubernetes


logger = logging.getLogger()


def test_write_last_handled_mapping(mocker):
    mocker.patch("lib.services.get_custom_object_api")
    write_last_handled_mapping(logger, {})
