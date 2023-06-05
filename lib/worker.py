from lib.mappings import AuthMappingList
from lib import get_config_map, update_config_map, write_config_map, write_last_handled_mapping
from kubernetes.client.rest import ApiException
from enum import Enum
from dataclasses import dataclass

class EventType(Enum):
    CREATE = 0
    UPDATE = 1
    DELETE = 2


@dataclass
class Event:
    event_type: EventType
    mappings: AuthMappingList
    old_mappings: AuthMappingList = None


def create_mapping(event: Event, logger):
    pass
    try:
        auth_config_map = get_config_map()
        current_config_mapping = AuthMappingList(data=auth_config_map.data)
        # save current config before change
        write_last_handled_mapping(logger, current_config_mapping.get_values())
        # add new roles
        current_config_mapping.merge_mappings(mappings_new)
        auth_config_map = update_config_map(
            auth_config_map, current_config_mapping.get_data()
        )
        response = write_config_map(auth_config_map)
        response_data = AuthMappingList(data=response.data)
        if mappings_new not in response_data:
            logger.error("Add Roles failed")
    except ApiException as e:
        logger.error(f"Exception: {e}")


def update_mapping(event: Event, logger):
    pass


def delete_mapping(event: Event, logger):
    pass
