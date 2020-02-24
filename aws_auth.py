import os
import kopf
import yaml
from kubernetes.client.rest import ApiException

from lib import (
    AuthMappingList,
    get_config_map,
    get_protected_mapping,
    update_config_map,
    write_config_map,
    write_protected_mapping,
    get_result_message,
)
from lib.constants import *

check_not_protected = lambda body, **_: body["metadata"]["name"] != PROTECTED_MAPPING
cm_is_aws_auth = lambda body, **_: body["metadata"]["name"] == "aws-auth"
kopf.config.WatchersConfig.watcher_retry_delay = 1

@kopf.on.startup()
def startup(logger, **kwargs):
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
        # add new roles
        current_config_mapping.merge_mappings(mappings_new)
        auth_config_map = update_config_map(
            auth_config_map, current_config_mapping.get_data()
        )
        response = write_config_map(auth_config_map)
        response_data = AuthMappingList(data=response.data)
        if mappings_new not in response_data:
            raise kopf.PermanentError("Add Roles failed")
        else:
            logger.info(response.data)
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
        else:
            logger.info(response.data)
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
        # remove old roles
        current_config_mapping.remove_mappings(mappings_delete)
        auth_config_map = update_config_map(
            auth_config_map, current_config_mapping.get_data()
        )
        response = write_config_map(auth_config_map)
        response_data = AuthMappingList(data=response.data)
        if mappings_delete in response_data:
            raise kopf.PermanentError("Delete Roles failed")
        else:
            logger.info(response.data)
    except ApiException as e:
        raise kopf.PermanentError(f"Exception: {e}")
    return get_result_message("All good")


@kopf.on.update(
    "", "v1", "configmaps", when=cm_is_aws_auth,
)
def log_config_map_change(logger, spec, old, new, diff, **kwargs):
    if "data" in old and "data" in new:
        old_mappings = AuthMappingList(data=old["data"])
        new_mappings = AuthMappingList(data=new["data"])
        change = list(old_mappings.diff(new_mappings))
        logger.info(f"Change to aws-auth configmap: {change}")
    else:
        logger.error(f"Wrong config map spec: {spec}")


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
