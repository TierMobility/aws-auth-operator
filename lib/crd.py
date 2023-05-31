from typing import List, Dict
from lib.constants import CRD_GROUP, CRD_VERSION, CRD_KIND


def build_aws_auth_mapping(mappings: List, name: str) -> Dict:
    return {
        "apiVersion": CRD_GROUP + "/" + CRD_VERSION,
        "kind": CRD_KIND,
        "metadata": {
            "annotations": {},
            "labels": {},
            "name": name,
        },
        "spec": {"mappings": mappings},
    }
