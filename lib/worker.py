from lib.mappings import AuthMappingList
from lib import get_config_map, update_config_map, write_config_map, write_last_handled_mapping, update_mapping_status
from kubernetes.client.rest import ApiException
from enum import Enum
from dataclasses import dataclass
import queue
import threading
import time
import datetime;

class EventType(Enum):
    CREATE = 0
    UPDATE = 1
    DELETE = 2


@dataclass
class Event:
    object_name: str
    event_type: EventType
    mappings: AuthMappingList
    old_mappings: AuthMappingList = None

class Worker(threading.Thread):
 
    def __init__(self,event_queue: queue.Queue, logger):
        threading.Thread.__init__(self)
 
        # The shutdown_flag is a threading.Event object that
        # indicates whether the thread should be terminated.
        self.shutdown_flag = threading.Event()
        self.event_queue = event_queue
        self.logger = logger
 
        # ... Other thread setup code here ...
 
    def run(self):
        self.logger.info('Worker Thread #%s started' % self.ident)
 
        while not self.shutdown_flag.is_set():
            if not self.event_queue.empty():
                event = self.event_queue.get()
                if isinstance(event, Event):
                    self.logger.info(f"Got event: {event.event_type}")
                    match event.event_type:
                        case EventType.CREATE:
                            create_mapping(event, self.logger)
                        case EventType.UPDATE:
                            update_mapping(event, self.logger)
                        case EventType.DELETE:
                            delete_mapping(event, self.logger)
                        case _: 
                            self.logger.error(f"Got unknown event type: {event.event_type}")
                else:
                    self.logger.info(event)
            time.sleep(1)   
 
        # ... Clean shutdown code here ...
        self.logger.info('Worker #%s stopped' % self.ident)


def create_mapping(event: Event, logger):
    pass
    try:
        auth_config_map = get_config_map()
        current_config_mapping = AuthMappingList(data=auth_config_map.data)
        # save current config before change
        write_last_handled_mapping(logger, current_config_mapping.get_values())
        # add new roles
        current_config_mapping.merge_mappings(event.mappings)
        auth_config_map = update_config_map(
            auth_config_map, current_config_mapping.get_data()
        )
        response = write_config_map(auth_config_map)
        response_data = AuthMappingList(data=response.data)
        if event.mappings not in response_data:
            logger.error("Add Roles failed")
        else:
            update_mapping_status(logger, event.object_name, {"status":{"create_fn": {"message":"All good","timestamp": datetime.datetime.now()}}})
    except ApiException as e:
        logger.error(f"Exception: {e}")


def update_mapping(event: Event, logger):
    pass


def delete_mapping(event: Event, logger):
    pass
