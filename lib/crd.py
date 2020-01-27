from typing import List, Dict
from lib.constants import CRD_GROUP, CRD_VERSION, CRD_KIND, PROTECTED_MAPPING


def build_aws_auth_mapping(mappings: List) -> Dict:
    return {
        "apiVersion": CRD_GROUP + "/" + CRD_VERSION,
        "kind": CRD_KIND,
        "metadata": {"annotations": {}, "labels": {}, "name": PROTECTED_MAPPING,},
        "spec": {"mappings": mappings},
    }
