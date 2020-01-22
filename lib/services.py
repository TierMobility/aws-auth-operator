import kubernetes
import yaml
from lib.constants import CM_NAME, NAMESPACE


def get_config_map():
    api_instance = kubernetes.client.CoreV1Api()
    return api_instance.read_namespaced_config_map(CM_NAME, NAMESPACE)


def write_config_map(auth_config_map):
    api_instance = kubernetes.client.CoreV1Api()
    return api_instance.patch_namespaced_config_map(
        CM_NAME, NAMESPACE, auth_config_map, pretty="true"
    )


def update_config_map(auth_config_map, roles_list):
    auth_config_map.data["mapRoles"] = yaml.dump(roles_list, default_flow_style=False)
    auth_config_map.metadata.namespace = None
    auth_config_map.metadata.uid = None
    auth_config_map.metadata.annotations = None
    auth_config_map.metadata.resource_version = None
    return auth_config_map
