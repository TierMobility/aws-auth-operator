import kopf
import yaml
from lib import (
    AuthMappingList,
    update_config_map,
    get_config_map,
    write_config_map,
    get_protected_mapping,
    write_protected_mapping,
    login_kubernetes,
)
from kubernetes.client.rest import ApiException
from lib.constants import CRD_GROUP, CRD_VERSION, CRD_NAME, PROTECTED_MAPPING

check_not_protected = lambda body, **_: body["metadata"]["name"] != PROTECTED_MAPPING


@kopf.on.startup()
def startup(logger, **kwargs):
    login_kubernetes(logger)
    pm = get_protected_mapping()
    if pm is None:
        # get current configmap and save values in protected mapping
        auth_config_map = get_config_map()
        role_mappings = AuthMappingList(data=auth_config_map.data)
        logger.info(role_mappings)
        write_protected_mapping(role_mappings.get_roles_dict())
    logger.info("Startup: {0}".format(pm))


@kopf.on.create(CRD_GROUP, CRD_VERSION, CRD_NAME, when=check_not_protected)
def create_fn(logger, spec, meta, **kwargs):
    logger.info(f"And here we are! Creating: {spec}")
    mappings_new = AuthMappingList(spec["mappings"])
    try:
        auth_config_map = get_config_map()
        current_config_mapping = AuthMappingList(data=auth_config_map.data)
        # add new roles
        current_config_mapping.merge_mappings(mappings_new)
        auth_config_map = update_config_map(
            auth_config_map, current_config_mapping.get_data()
        )
        response = write_config_map(auth_config_map)
        response_roles = yaml.load(
            response.data.get("mapRoles"), Loader=yaml.FullLoader
        )
        if mappings_new.check_update(response_roles) == "failed":
            raise kopf.PermanentError("Add Roles failed")
        else:
            logger.info(response)
    except ApiException as e:
        raise kopf.PermanentError(f"Exception: {e}")
    return {"Message": "All good"}


@kopf.on.update(CRD_GROUP, CRD_VERSION, CRD_NAME, when=check_not_protected)
def update_fn(logger, spec, old, new, diff, **kwargs):
    old_role_mappings = AuthMappingList(old["spec"]["mappings"])
    new_role_mappings = AuthMappingList(new["spec"]["mappings"])
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
        response_roles = yaml.load(
            response.data.get("mapRoles"), Loader=yaml.FullLoader
        )
        if new_role_mappings.check_update(response_roles) == "failed":
            logger.info(new_role_mappings.get_roles_dict())
            raise kopf.PermanentError("Update Roles failed")
        else:
            logger.info(response)
    except ApiException as e:
        raise kopf.PermanentError(f"Exception: {e}")
    return {"Message": "All good"}


@kopf.on.delete(CRD_GROUP, CRD_VERSION, CRD_NAME, when=check_not_protected)
def delete_fn(logger, spec, meta, **kwarg):
    logger.info(f"And here we are! DELETING: {spec}")
    mappings_delete = AuthMappingList(spec["mappings"])
    try:
        auth_config_map = get_config_map()
        current_config_mapping = AuthMappingList(data=auth_config_map.data)
        # remove old roles
        current_config_mapping.remove_mappings(mappings_delete)
        auth_config_map = update_config_map(
            auth_config_map, current_config_mapping.get_data()
        )
        response = write_config_map(auth_config_map)
        response_roles = yaml.load(
            response.data.get("mapRoles"), Loader=yaml.FullLoader
        )
        if mappings_delete.check_delete(response_roles) == "failed":
            raise kopf.PermanentError("Delete Roles failed")
        else:
            logger.info(response)
    except ApiException as e:
        raise kopf.PermanentError(f"Exception: {e}")
    return {"Message": "All good"}
