import kopf
import yaml
from lib import AuthMappingList, update_config_map, get_config_map, write_config_map
from kubernetes.client.rest import ApiException


@kopf.on.create("tier.app", "v1", "awsauthrolemappings")
def create_fn(spec, meta, **kwargs):
    print(f"And here we are! Creating: {spec}")
    mappings = AuthMappingList(spec["mappings"])
    try:
        auth_config_map = get_config_map()
        roles = yaml.load(auth_config_map.data["mapRoles"], Loader=yaml.FullLoader)
        # add new roles
        roles_list = mappings.add_to_roles(roles)
        auth_config_map = update_config_map(auth_config_map, roles_list)
        response = write_config_map(auth_config_map)
        response_roles = yaml.load(
            response.data.get("mapRoles"), Loader=yaml.FullLoader
        )
        if mappings.check_update(response_roles) == "failed":
            raise kopf.PermanentError("Add Roles failed")
        else:
            print(response)
    except ApiException as e:
        raise kopf.PermanentError(f"Exception: {e}")
    return {"Message": "All good"}


@kopf.on.update("tier.app", "v1", "awsauthrolemappings")
def update_fn(spec, old, new, diff, **kwargs):
    old_roles = AuthMappingList(old["spec"]["mappings"])
    new_roles = AuthMappingList(new["spec"]["mappings"])
    try:
        auth_config_map = get_config_map()
        roles = yaml.load(auth_config_map.data["mapRoles"], Loader=yaml.FullLoader)
        # remove old stuff first
        roles_list = old_roles.remove_from_roles(roles)
        # add new values
        roles_list = new_roles.add_to_roles(roles_list)
        auth_config_map = update_config_map(auth_config_map, roles_list)
        response = write_config_map(auth_config_map)
        response_roles = yaml.load(
            response.data.get("mapRoles"), Loader=yaml.FullLoader
        )
        if new_roles.check_update(response_roles) == "failed":
            print(new_roles.get_roles_dict())
            raise kopf.PermanentError("Update Roles failed")
        else:
            print(response)
    except ApiException as e:
        raise kopf.PermanentError(f"Exception: {e}")
    return {"Message": "All good"}


@kopf.on.delete("tier.app", "v1", "awsauthrolemappings")
def delete_fn(spec, meta, **kwarg):
    print(f"And here we are! DELETING: {spec}")
    mappings = AuthMappingList(spec["mappings"])
    try:
        auth_config_map = get_config_map()
        roles = yaml.load(auth_config_map.data["mapRoles"], Loader=yaml.FullLoader)
        # remove old roles
        roles_list = mappings.remove_from_roles(roles)
        auth_config_map = update_config_map(auth_config_map, roles_list)
        response = write_config_map(auth_config_map)
        response_roles = yaml.load(
            response.data.get("mapRoles"), Loader=yaml.FullLoader
        )
        if mappings.check_delete(response_roles) == "failed":
            raise kopf.PermanentError("Delete Roles failed")
        else:
            print(response)
    except ApiException as e:
        raise kopf.PermanentError(f"Exception: {e}")
    return {"Message": "All good"}
