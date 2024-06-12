"""Contains all components of this libary.
"""


import json
import subprocess


def load_config(file_path:str) -> 'CmdMenuConfig':
  """Loads the config from a file
  """
  with open(file_path, "r", encoding='utf-8') as file:
    data = json.load(file)
    return CmdMenuConfig(None, data)


def loads_config(json_str:str) -> 'CmdMenuConfig':
  """Loads the config from a file
  """
  data = json.loads(json_str)
  return CmdMenuConfig(None, data)


class ConfigObject:
  """Contains basic config functionalities
  """
  def __init__(self) -> None:
    pass

  def to_json_obj(self) -> any:
    """Converts the object to a json object
    """
    return None, None

  def to_json_str(self) -> str:
    """Converts the object to a json string
    """
    _, obj = self.to_json_obj()
    return json.dumps(obj, indent=2)

  @staticmethod
  def from_json_obj(key:str, json_obj:any) -> 'ConfigObject':
    """Converts a json object to the object
    """
    classType = {
      str: CmdEntryConfig,
      list: CmdTextConfig,
      dict: CmdMenuConfig
    }[type(json_obj)]
    return classType(key, json_obj)


class CmdMenuConfig(ConfigObject):
  """Contains the stored config
  """

  def __init__(self, key:str, data:dict) -> None:
    super().__init__()
    self.key:str = key
    self.items:list[ConfigObject] = []
    for ikey in data:
      self.items.append(ConfigObject.from_json_obj(ikey, data[ikey]))

  def to_json_obj(self):
    """Converts the object to a json object
    """
    content = {}
    for item in self.items:
      key, value = item.to_json_obj()
      content[key] = value
    return self.key, content

  def __str__(self):
    return str(self.key)


class CmdTextConfig(ConfigObject):
  """Contains the stored config
  """

  def __init__(self, key:str, data:list[any]) -> None:
    super().__init__()
    self.key:str = key
    self.lines:list[CmdTextLine] = []
    for item in data:
      self.lines.append(CmdTextConfig.listitem_to_textline(item))

  def to_json_obj(self):
    """Converts the object to a json object
    """

    return self.key, list(map(lambda l: l.to_json_obj()[1], self.lines))

  def __str__(self):
    return "\n".join(list(map(str,self.lines)))

  @staticmethod
  def listitem_to_textline(item:any) -> 'CmdTextLine':
    """Converts a list item to a text line.
    If the item is a string, it is returned as is.
    If its a dict, each key will be excecuted as a command with the value as argument and the output will be returned.

    Args:
        item (str,dict[str,str]): the list item that should be converted

    Returns:
        str: the converted text line
    """
    return CmdTextLine(item)


class CmdTextLine(ConfigObject):
  """Contains a line of text.
  """

  def __init__(self, entry:any) -> None:
    self.origin:any = entry
    self.text:list[str] = []
    self.update()

  def update(self) -> None:
    """Updates the text.
    """
    if isinstance(self.origin, str):
      self.text = [self.origin]
    if isinstance(self.origin, dict):
      result = []
      for key in self.origin:
        result.append(subprocess.getoutput(f"{key} {self.origin[key]}"))
      self.text = result

  def to_json_obj(self):
    """Converts the object to a json object
    """
    return None, self.origin

  def __str__(self):
    self.update()
    return "\n".join(self.text)


class CmdEntryConfig(ConfigObject):
  """Contains the stored config
  """

  def __init__(self, key:str, data:str) -> None:
    super().__init__()
    self.key:str = key
    self.cmd:str = data
    if self.cmd.lower()[-5:] == "&read":
      self.cmd = self.cmd[:-5]
      self.read = True
    else:
      self.read = False

  def to_json_obj(self):
    """Converts the object to a json object
    """
    cmd = self.cmd
    if self.read:
      cmd += "&read"
    return self.key, cmd

  def __str__(self):
    return self.key
