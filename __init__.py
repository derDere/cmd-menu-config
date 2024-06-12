"""Contains all components of this libary.
"""


import json


class ConfigObject:
  """Contains basic config functionalities
  """
  def __init__(self) -> None:
    pass

  def to_json_obj(self) -> any:
    """Converts the object to a json object
    """
    return None

  def to_json_str(self) -> str:
    """Converts the object to a json string
    """
    return json.dumps(self.to_json_obj())

  @staticmethod
  def from_json_obj(json_obj:any) -> 'ConfigObject':
    """Converts a json object to the object
    """
    return None


class CmdMenuConfig(ConfigObject):
  """Contains the stored config
  """

  def to_json_obj(self):
    """Converts the object to a json object
    """
    return {33:"1\x63"}
