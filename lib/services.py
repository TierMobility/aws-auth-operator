import kubernetes
import yaml
import kopf
from kubernetes.client.rest import ApiException
from kubernetes.client import V1ConfigMap
from lib.constants import *
from lib.crd import build_aws_auth_mapping
from typing import Dict, List


def get_config_map() -> V1ConfigMap:
    api_instance = kubernetes.client.CoreV1Api()
    return api_instance.read_namespaced_config_map(CM_NAME, NAMESPACE)


def write_config_map(auth_config_map: V1ConfigMap) -> V1ConfigMap:
    api_instance = kubernetes.client.CoreV1Api()
    return api_instance.patch_namespaced_config_map(
        CM_NAME, NAMESPACE, auth_config_map, pretty="true"
    )


def update_config_map(auth_config_map: V1ConfigMap, data: Dict):
    if "mapRoles" in data:
        auth_config_map.data["mapRoles"] = yaml.dump(
            data["mapRoles"], default_flow_style=False
        )
    if "mapUsers" in data:
        auth_config_map.data["mapUsers"] = yaml.dump(
            data["mapUsers"], default_flow_style=False
        )
    auth_config_map.metadata.namespace = None
    auth_config_map.metadata.uid = None
    auth_config_map.metadata.annotations = None
    auth_config_map.metadata.resource_version = None
    return auth_config_map


def get_protected_mapping() -> Dict:
    return get_mapping(PROTECTED_MAPPING)


def write_protected_mapping(logger, mappings: Dict):
    create_mapping(logger, PROTECTED_MAPPING, mappings)


def get_last_handled_mapping() -> Dict:
    return get_mapping(LAST_HANDLED_MAPPING)


def write_last_handled_mapping(logger, mappings: List):
    lm = get_mapping(LAST_HANDLED_MAPPING)
    if lm is None:
        create_mapping(logger, LAST_HANDLED_MAPPING, mappings)
    else:
        update_mapping(logger, LAST_HANDLED_MAPPING, mappings)


def get_mapping(name: str) -> Dict:
    api_instance = get_custom_object_api()
    try:
        protected_mapping = api_instance.get_cluster_custom_object(
            CRD_GROUP, CRD_VERSION, CRD_NAME, name
        )
        return protected_mapping
    except ApiException as e:
        if e.status == 404:
            return None
        else:
            raise Exception("Getting resource failed!", e)


def create_mapping(logger, name: str, mappings: Dict):
    body = build_aws_auth_mapping(mappings, name)
    api_instance = get_custom_object_api()
    try:
        pm = api_instance.create_cluster_custom_object(
            CRD_GROUP, CRD_VERSION, CRD_NAME, body, pretty=True
        )
        print(pm)
    except ApiException as e:
        logger.error(e)


def update_mapping(logger, name: str, mappings: Dict):
    body = build_aws_auth_mapping(mappings, name)
    api_instance = get_custom_object_api()
    try:
        pm = api_instance.patch_cluster_custom_object(
            CRD_GROUP, CRD_VERSION, CRD_NAME, name, body
        )
        print(pm)
    except ApiException as e:
        logger.error(e)

def update_mapping_status(logger, name: str, status_update: Dict):
    body = build_aws_auth_mapping(mappings, name)
    api_instance = get_custom_object_api()
    try:
        pm = api_instance.patch_cluster_custom_object_status(
            CRD_GROUP, CRD_VERSION, CRD_NAME, name, status_update
        )
        logger.debug(pm)
    except ApiException as e:
        logger.error(e)

def get_custom_object_api() -> kubernetes.client.CustomObjectsApi:
    return kubernetes.client.CustomObjectsApi()
