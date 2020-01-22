import yaml
from typing import List

class AuthMapping:

  arn = ""
  username = ""
  groups = []
  usertype = ""

  def __init__(self, mapping: dict):
    self.arn = mapping['arn']
    self.username = mapping['username']
    self.usertype = mapping['usertype']
    self.groups = mapping['groups']

  def get_mapping(self) -> dict:
    mapping = {
      'username': self.username,
      'groups': self.groups
    }
    if self.usertype == 'Role':
      mapping['rolearn'] = self.arn
    else:
      mapping['userarn'] = self.arn
    return mapping

  def __repr__(self):
    return "arn: {0}, usertype: {1} ".format(self.arn, self.usertype)


class AuthMappingList:

  auth_mappings: List[AuthMapping]

  def __init__(self, mappings: List):
    self.auth_mappings = []
    for mapping in mappings:
      self.auth_mappings.append(AuthMapping(mapping))

  def add_to_roles(self, roles:dict) -> List[dict]:
    mapped_roles = dict()
    for role in roles:
        mapped_roles[role['rolearn']] = role
    for new_role in self.get_roles_dict():
        mapped_roles[new_role['rolearn']] = new_role
    return list(mapped_roles.values())

  def remove_from_roles(self, roles:dict) -> List[dict]:
    mapped_roles = dict()
    for role in roles:
        mapped_roles[role['rolearn']] = role
    for new_role in self.get_roles_dict():
        mapped_roles.pop(new_role['rolearn'], None)
    return list(mapped_roles.values())

  def get_roles_dict(self) -> List[dict]:
    result = []
    for auth_mapping in self.auth_mappings:
      if auth_mapping.usertype == "Role":
        result.append(auth_mapping.get_mapping())
    return result
  
  def __repr__(self):
    return self.auth_mappings.__repr__()

  def check_update(self, response_roles:dict) -> str:
    role_arns = []
    new_role_arns = []
    for role in response_roles:
      role_arns.append(role['rolearn'])
      for role in self.get_roles_dict():
        new_role_arns.append(role['rolearn'])
    return 'success' if all(elem in role_arns for elem in new_role_arns) else 'failed'


  def check_delete(self, response_roles:dict) -> str:
    role_arns = []
    new_role_arns = []
    for role in response_roles:
        role_arns.append(role['rolearn'])
    for role in self.get_roles_dict():
        new_role_arns.append(role['rolearn'])
    return 'failed' if any(elem in role_arns for elem in new_role_arns) else 'success'


