import os
import kopf
import yaml
import queue
import time
from kubernetes.client.rest import ApiException

from lib import (
    AuthMappingList,
    get_config_map,
    get_protected_mapping,
    update_config_map,
    write_config_map,
    write_protected_mapping,
    write_last_handled_mapping,
    get_last_handled_mapping,
    get_result_message,
)
from lib.constants import *

check_not_protected = lambda body, **_: body["metadata"]["name"] not in SYSTEM_MAPPINGS
cm_is_aws_auth = lambda body, **_: body["metadata"]["name"] == "aws-auth"
# kopf.config.WatchersConfig.watcher_retry_delay = 1

event_queue = queue.Queue()

@kopf.on.startup()
def startup(logger, settings: kopf.OperatorSettings, **kwargs):
    # set api watching delay to 1s
    settings.watching.reconnect_backoff = 1 
    if os.getenv(USE_PROTECTED_MAPPING) == "true":
        kopf.login_via_client(logger=logger, **kwargs)
        pm = get_protected_mapping()
        if pm is None:
            # get current configmap and save values in protected mapping
            auth_config_map = get_config_map()
            role_mappings = AuthMappingList(data=auth_config_map.data)
            logger.info(role_mappings)
            write_protected_mapping(logger, role_mappings.get_values())
        logger.info("Startup: {0}".format(pm))
    event_queue.put("Starting Operator ...")


@kopf.on.create(CRD_GROUP, CRD_VERSION, CRD_NAME, when=check_not_protected)
def create_fn(logger, spec, meta, **kwargs):
    logger.info(f"And here we are! Creating: {spec}")
    if not spec or "mappings" not in spec:
        return get_result_message(f"invalid schema {spec}")
    mappings_new = AuthMappingList(spec["mappings"])
    if overwrites_protected_mapping(logger, mappings_new):
        return get_result_message("overwriting protected mapping not possible")
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
            raise kopf.PermanentError("Add Roles failed")
    except ApiException as e:
        raise kopf.PermanentError(f"Exception: {e}")
    return get_result_message("All good")


@kopf.on.update(CRD_GROUP, CRD_VERSION, CRD_NAME, when=check_not_protected)
def update_fn(logger, spec, old, new, diff, **kwargs):
    if not new or "spec" not in new:
        return get_result_message(f"invalid schema {new}")
    if "mappings" not in new["spec"]:
        new_role_mappings = AuthMappingList()
    else:
        new_role_mappings = AuthMappingList(new["spec"]["mappings"])
    if not old or "spec" not in old or "mappings" not in old["spec"]:
        old_role_mappings = AuthMappingList()
    else:
        old_role_mappings = AuthMappingList(old["spec"]["mappings"])

    if overwrites_protected_mapping(logger, new_role_mappings):
        return get_result_message("overwriting protected mapping not possible")
    try:
        auth_config_map = get_config_map()
        current_config_mapping = AuthMappingList(data=auth_config_map.data)
        # save current config before change
        write_last_handled_mapping(logger, current_config_mapping.get_values())

        # remove old stuff first
        current_config_mapping.remove_mappings(old_role_mappings)
        # add new values
        current_config_mapping.merge_mappings(new_role_mappings)
        auth_config_map = update_config_map(
            auth_config_map, current_config_mapping.get_data()
        )
        response = write_config_map(auth_config_map)
        response_data = AuthMappingList(data=response.data)
        if len(new_role_mappings) > 0 and new_role_mappings not in response_data:
            raise kopf.PermanentError("Update Roles failed")
    except ApiException as e:
        raise kopf.PermanentError(f"Exception: {e}")
    return get_result_message("All good")


@kopf.on.delete(CRD_GROUP, CRD_VERSION, CRD_NAME, when=check_not_protected)
def delete_fn(logger, spec, meta, **kwarg):
    logger.info(f"DELETING: {spec}")
    if not spec or "mappings" not in spec:
        return get_result_message(f"invalid schema {spec}")
    mappings_delete = AuthMappingList(spec["mappings"])
    if overwrites_protected_mapping(logger, mappings_delete):
        kopf.PermanentError("Overwriting protected mapping not possible!")
    try:
        auth_config_map = get_config_map()
        current_config_mapping = AuthMappingList(data=auth_config_map.data)

        # save current config before change
        write_last_handled_mapping(logger, current_config_mapping.get_values())
        # remove old roles
        current_config_mapping.remove_mappings(mappings_delete)
        auth_config_map = update_config_map(
            auth_config_map, current_config_mapping.get_data()
        )
        response = write_config_map(auth_config_map)
        response_data = AuthMappingList(data=response.data)
        if mappings_delete in response_data:
            raise kopf.PermanentError("Delete Roles failed")
    except ApiException as e:
        raise kopf.PermanentError(f"Exception: {e}")
    return get_result_message("All good")


@kopf.on.event(
    "", "v1", "configmaps", when=cm_is_aws_auth,
)
def log_config_map_change(logger, body, **kwargs):
    lm = get_last_handled_mapping()
    if lm is not None:
        old_mappings = AuthMappingList(lm["spec"]["mappings"])
        new_mappings = AuthMappingList(data=body["data"])
        change = list(old_mappings.diff(new_mappings))
        logger.info(f"Change to aws-auth configmap: {change}")
    else:
        logger.error(f"last mapping not found: {body}")

@kopf.daemon(CRD_GROUP, CRD_VERSION, CRD_NAME)
def change_handler(stopped: kopf.DaemonStopped, spec, logger, retry, patch, **_):
    print("start")
    started = time.time()
    while not stopped and time.time() - started <= 30:
        logger.info(f"Something")        
        if not queue.empty():
            print(queue.get())
        stopped.wait(5.0)

    print("We are done. Bye.")


def overwrites_protected_mapping(logger, check_mapping: AuthMappingList) -> bool:
    if os.getenv(USE_PROTECTED_MAPPING) == "true":
        pm = get_protected_mapping()
        logger.info(f"Protected mapping: {pm}")
        if pm is not None:
            protected_mapping = AuthMappingList(pm["spec"]["mappings"])
            if check_mapping in protected_mapping:
                logger.error("Overiding protected Entries not allowed!")
                return True
    return False
