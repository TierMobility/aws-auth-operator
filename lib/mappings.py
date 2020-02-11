from __future__ import annotations
import yaml
from enum import Enum
from typing import List, Dict


class UserType(Enum):
    Role = "Role"
    User = "User"

    @classmethod
    def value_of(cls, object):
        if isinstance(object, UserType):
            return object
        elif object == "Role":
            return UserType.Role
        elif object == "User":
            return UserType.User


class AuthMapping:

    arn: str
    username: str
    groups: List
    usertype: UserType

    def __init__(self, mapping: Dict):

        if "arn" in mapping.keys():
            self.arn = mapping["arn"]
            self.usertype = UserType.value_of(mapping["usertype"])
        elif "rolearn" in mapping.keys():
            self.arn = mapping["rolearn"]
            self.usertype = UserType.Role
        elif "userarn" in mapping.keys():
            self.arn = mapping["userarn"]
            self.usertype = UserType.User

        self.username = mapping["username"]
        self.groups = mapping["groups"]

    def get_mapping(self) -> dict:
        mapping = {"username": self.username, "groups": self.groups}
        if self.usertype == UserType.Role:
            mapping["rolearn"] = self.arn
        else:
            mapping["userarn"] = self.arn
        return mapping

    def __repr__(self):
        return "arn: {0}, usertype: {1}, groups: {2} ".format(
            self.arn, self.usertype, self.groups
        )

    def __hash__(self):
        return hash((self.arn, self.usertype))

    def as_dict(self) -> Dict:
        return {
            "arn": self.arn,
            "username": self.username,
            "groups": self.groups,
            "usertype": self.usertype.name,
        }


class AuthMappingList:

    auth_mappings: Dict[str, AuthMapping]

    def __init__(self, mappings=None, data={}):
        if mappings is None:
            mappings = []
        if "mapRoles" in data.keys():
            mappings.extend(yaml.load(data["mapRoles"], Loader=yaml.FullLoader))
        if "mapUsers" in data.keys():
            mappings.extend(yaml.load(data["mapUsers"], Loader=yaml.FullLoader))
        self.auth_mappings = {}
        for mapping in mappings:
            auth_mapping = AuthMapping(mapping)
            self.auth_mappings[hash(auth_mapping)] = auth_mapping

    def merge_mappings(self, mappings_to_merge: AuthMappingList):
        for new_mapping_arn in mappings_to_merge.auth_mappings.keys():
            self.auth_mappings[new_mapping_arn] = mappings_to_merge.auth_mappings[
                new_mapping_arn
            ]

    def remove_mappings(self, mappings_to_remove: AuthMappingList):
        for new_mapping_arn in mappings_to_remove.auth_mappings.keys():
            if new_mapping_arn in self.auth_mappings.keys():
                del self.auth_mappings[new_mapping_arn]

    def get_roles_dict(self) -> List[Dict]:
        result = []
        for auth_mapping in self.auth_mappings.values():
            if auth_mapping.usertype == UserType.Role:
                result.append(auth_mapping.get_mapping())
        return result

    def get_user_dict(self) -> List[Dict]:
        result = []
        for auth_mapping in self.auth_mappings.values():
            if auth_mapping.usertype == UserType.User:
                result.append(auth_mapping.get_mapping())
        return result

    def get_values(self) -> List[Dict]:
        result = []
        for auth_mapping in self.auth_mappings.values():
            result.append(auth_mapping.as_dict())
        return result

    def get_data(self) -> Dict:
        data = {}
        roles = self.get_roles_dict()
        if len(roles) > 0:
            data["mapRoles"] = roles
        users = self.get_user_dict()
        if len(users) > 0:
            data["mapUsers"] = users
        return data

    def __repr__(self):
        return self.auth_mappings.__repr__()

    def __eq__(self, other: AuthMappingList):
        own_keys = set(self.auth_mappings.keys())
        other_keys = set(other.auth_mappings.keys())
        return len(own_keys.intersection(other_keys)) == len(own_keys)

    def __contains__(self, other: AuthMappingList):
        own_keys = set(self.auth_mappings.keys())
        other_keys = set(other.auth_mappings.keys())
        return len(own_keys.intersection(other_keys)) > 0

    def __len__(self):
        return len(self.auth_mappings)

    def check_update(self, response_roles: Dict) -> str:
        role_arns = []
        new_role_arns = []
        for role in response_roles:
            role_arns.append(role["rolearn"])
            for role in self.get_roles_dict():
                new_role_arns.append(role["rolearn"])
        return (
            "success" if all(elem in role_arns for elem in new_role_arns) else "failed"
        )

    def check_delete(self, response_roles: Dict) -> str:
        role_arns = []
        new_role_arns = []
        for role in response_roles:
            role_arns.append(role["rolearn"])
        for role in self.get_roles_dict():
            new_role_arns.append(role["rolearn"])
        return (
            "failed" if any(elem in role_arns for elem in new_role_arns) else "success"
        )
