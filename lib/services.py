import kubernetes
import yaml
import kopf
from kubernetes.client.rest import ApiException
from lib.constants import *
from lib.crd import build_aws_auth_mapping


def get_config_map():
    api_instance = kubernetes.client.CoreV1Api()
    return api_instance.read_namespaced_config_map(CM_NAME, NAMESPACE)


def write_config_map(auth_config_map):
    api_instance = kubernetes.client.CoreV1Api()
    return api_instance.patch_namespaced_config_map(
        CM_NAME, NAMESPACE, auth_config_map, pretty="true"
    )


def update_config_map(auth_config_map, data):
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


def login_kubernetes(logger):
    try:
        kubernetes.config.load_incluster_config()  # cluster env vars
        logger.debug("Client is configured in cluster with service account.")
    except kubernetes.config.ConfigException as e1:
        try:
            kubernetes.config.load_kube_config()  # developer's config files
            logger.debug("Client is configured via kubeconfig file.")
        except kubernetes.config.ConfigException as e2:
            raise kopf.PermanentError(
                f"Cannot authenticate client neither in-cluster, nor via kubeconfig."
            )


def get_protected_mapping():
    api_instance = kubernetes.client.CustomObjectsApi()
    try:
        protected_mapping = api_instance.get_cluster_custom_object(
            CRD_GROUP, CRD_VERSION, CRD_NAME, PROTECTED_MAPPING
        )
        return protected_mapping
    except ApiException as e:
        if e.status == 404:
            return None
        else:
            raise Exception("Getting resource failed!", e)


def write_protected_mapping(mappings):
    body = build_aws_auth_mapping(mappings)
    api_instance = kubernetes.client.CustomObjectsApi()
    try:
        api_instance.create_cluster_custom_object(
            CRD_GROUP, CRD_VERSION, CRD_NAME, body, pretty=True
        )
    except ApiException as _:
        pass
