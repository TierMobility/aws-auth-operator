from typing import List
from lib.constants import CRD_GROUP, CRD_VERSION, PROTECTED_MAPPING


def build_aws_auth_mapping(mappings: List) -> dict:
    return {
        "apiVersion": CRD_GROUP + "/" + CRD_VERSION,
        "kind": "AwsAuthRoleMapping",
        "metadata": {"annotations": {}, "labels": {}, "name": PROTECTED_MAPPING,},
        "spec": {"mappings": mappings},
    }
