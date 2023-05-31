from lib.mappings import AuthMappingList
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


def update_mapping(event: Event, logger):
    pass


def delete_mapping(event: Event, logger):
    pass
