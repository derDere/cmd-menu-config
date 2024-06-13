"""
Command Config Module

Contains classes used to read a menu structure from a json file.

A menu structure is a dictionary where the keys are the menu items and the values are either strings, objects or lists.
If the value is a string, it is considered a command and could be executed. (e.g. "echo Hello World")
You could end the command with "&read" to set a read flag that should tell the executor wait for a key press before continuing.
(e.g. "echo Hello World&read")

If the value is a list, it is considered a text block and will be printed as is. (e.g. ["Line1", "Line2"])
You could also use a dictionary in the list to execute commands. (e.g. ["Line1", "Line2", {"date": "/t"}])
The dictionary key is the command and the value is the argument. The output of the command should be printed as text.

If the value is a dictionary, it is considered a submenu and the key is the menu items displayname and the value is the submenu.
The submenu is a menu structure itself and again could contain commands, text blocks and submenus.
"""


import os
import json
import subprocess
from abc import ABC, abstractmethod


class CmdConfigBase(ABC):
  """
  Base class for the config

  Used to load and save the config from and to a file.
  You should inherit from this class and implement the _to_json_obj and _from_json_obj methods.

  Args:
    file_path (str): the path to the config file

  Attributes:
    file_path (str): the path to the config file
    root_menu (CmdMenuConfig): the root menu of the config
  """

  file_path:str
  root_menu:'CmdMenuConfig'

  def __init__(self, file_path:str) -> None:
    """Initializes the config

    Args:
      file_path (str): the path to the config file
    """
    self.file_path = file_path
    self.reload()

  @abstractmethod
  def _to_json_obj(self) -> list|str|dict|None:
    """Converts the object to a json object.
    This method should be implemented in the child class
    and should return a json object that represents the object.

    Returns:
      list|str|dict|None: the json object
    """
    return self.root_menu.to_json_obj()[1]

  @abstractmethod
  def _from_json_obj(self, json_obj:list|str|dict|None) -> None:
    """Loads the object from a json object.
    This method should be implemented in the child class
    and should load the object from a json object.

    Args:
      json_obj (dict): the json object

    Raises:
      TypeError: if the json object is not a dict
    """
    if isinstance(json_obj, dict):
      self.root_menu = CmdMenuConfig(None, json_obj)
    else:
      raise TypeError(f"Invalid json object: {json_obj}")

  def reload(self) -> None:
    """Reloads the config from a file
    if the file does not exist, an empty config will be generated
    """
    if (self.file_path is None) or (not os.path.exists(self.file_path)):
      self._generate_empty_config()
      return
    with open(self.file_path, "r", encoding='utf-8') as file:
      data = json.load(file)
      self._from_json_obj(data)

  def loads(self, json_str:str) -> None:
    """Loads the config from a json string
    """
    data = json.loads(json_str)
    self._from_json_obj(data)

  def save(self, indent:int = 2) -> None:
    """Saves the config to a file
    If no file path is specified, a TypeError will be raised.

    Args:
      indent (int, optional): the indentation of the json file. Defaults to 2.

    Raises:
      TypeError: if no file path is specified
    """
    if self.file_path is None:
      raise TypeError("No file path specified")
    with open(self.file_path, "w+", encoding='utf-8') as file:
      json.dump(self._to_json_obj(), file, indent=indent)

  def saves(self, indent:int = 2) -> str:
    """Saves the config to a json string

    Args:
      indent (int, optional): the indentation of the json file. Defaults to 2.
    """
    return json.dumps(self._to_json_obj(), indent=indent)

  def _generate_empty_config(self) -> None:
    """Generates an empty config
    This method should be implemented in the child class
    and should generate an empty config.

    By default, an empty menu will be generated with a text "(No commands configured)"
    """
    self.root_menu = CmdMenuConfig(None, {"T1":"(No commands configured)"})


class ConfigObject(ABC):
  """Base class for the config objects
  Every config object should inherit from this class.

  Attributes:
    key (str|None): the key of the object
  """

  key:str|None

  def __init__(self, key:str|None) -> None:
    """Initializes the object

    Args:
      key (str|None): the key of the object
    """
    self.key = key

  @abstractmethod
  def to_json_obj(self) -> tuple[str|None, dict|list|str|None]:
    """Converts the object to a json object
    This method should be implemented in the child class
    and should return a tuple with the key and the json object.

    Returns:
      tuple[str|None, dict|list|str|None]: the key and the json object
    """
    return self.key, None

  def to_json_str(self, indent:int = 2) -> str:
    """Converts the object to a json string
    This method should not be overridden.

    Args:
      indent (int, optional): the indentation of the json file. Defaults to 2.

    Returns:
      str: the json string
    """
    _, obj = self.to_json_obj()
    return json.dumps(obj, indent=indent)

  @staticmethod
  def from_json_obj(key:str, json_obj:list|str|dict|None) -> 'ConfigObject':
    """Creates a config object from a json object
    The object type is determined by the json object.
    Depending on the type, a different object will be created.
    If the json object is invalid, a TypeError will be raised.
    Its either a CmdEntryConfig, CmdTextConfig or CmdMenuConfig.
    This method should not be overridden.

    Args:
      key (str): the key of the object
      json_obj (list|str|dict|None): the json object

    Returns:
      ConfigObject: the created config object

    Raises:
      TypeError: if the json object is invalid
    """
    if isinstance(json_obj, str):
      return CmdEntryConfig(key, json_obj)

    if isinstance(json_obj, list):
      return CmdTextConfig(key, json_obj)

    if isinstance(json_obj, dict):
      return CmdMenuConfig(key, json_obj)

    raise TypeError(f"Invalid json object: {json_obj}")


class CmdMenuConfig(ConfigObject):
  """Represents a menu structure
  This class will be created from a json object.
  Each key will be a menu items displayname and the value will be a command, text block or submenu.

  Args:
    key (str|None): the key of the menu
    data (dict): the data of the menu

  Attributes:
    key (str|None): the key of the menu
    items (list[ConfigObject]): the items of the menu
  """

  def __init__(self, key:str|None, data:dict) -> None:
    """Initializes the menu

    Args:
      key (str | None): the key of the menu
      data (dict): the data of the menu

    Raises:
      TypeError: if the data type is not a dict
    """
    super().__init__(key)
    self.items:list[ConfigObject] = []
    if isinstance(data, dict):
      for ikey in data:
        self.items.append(ConfigObject.from_json_obj(ikey, data[ikey]))
    else:
      raise TypeError(f"Invalid data type: {type(data)}")

  def to_json_obj(self) -> tuple[str|None, dict]:
    """Converts the object to a json object
    Each item will be converted to a json object and added to the content.

    Returns:
      tuple[str|None, dict]: the key and the json object
    """
    content:dict = {}
    for item in self.items:
      key, value = item.to_json_obj()
      content[key] = value
    return self.key, content

  def __str__(self) -> str:
    """Converts the object to a string

    Returns:
      str: The objects key (displayname)
    """
    return str(self.key)


class CmdTextConfig(ConfigObject):
  """Represents a text block
  This class will be created from a json list.
  Each item in the list will be a line of text.
  If the item is a string, it will be printed as is.
  If the item is a dict, each key will be executed as a command with the value as argument and the output will be printed.

  Args:
    key (str): the key of the text block
    data (list[str|dict]): the data of the text block

  Attributes:
    key (str): the key of the text block
    lines (list[CmdTextLine]): the lines of the text block
  """

  def __init__(self, key:str, data:list[str|dict]) -> None:
    super().__init__(key)
    self.lines:list[CmdTextLine] = []
    for item in data:
      self.lines.append(CmdTextConfig.listitem_to_textline(item))

  def line_count(self) -> int:
    """Returns the count of lines in the text block

    Returns:
      int: the count of lines
    """
    return len(str(self).split("\n"))

  def to_json_obj(self) -> tuple[str|None, dict|list|str|None]:
    """Converts the object to a json object
    """
    return self.key, list(map(lambda l: l.to_json_obj()[1], self.lines))

  def __str__(self) -> str:
    """Converts the object to a string

    Returns:
      str: the text of the text block
    """
    return "\n".join(list(map(str,self.lines)))

  @staticmethod
  def listitem_to_textline(item:str|dict) -> 'CmdTextLine':
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
  """Represents a text line
  This class will be created from a json string or a json object.
  If the object is a string, it will be printed as is.
  If the object is a dict, each key will be executed as a command with the value as argument and the output will be printed.
  You can retrigger the command execution by calling the update method.

  Args:
    entry (str|dict): the entry of the text line

  Attributes:
    origin (str|dict): the original entry
    text (list[str]): the text of the line
  """

  def __init__(self, entry:str|dict) -> None:
    """Initializes the text line

    Args:
      entry (str | dict): the entry of the text line
    """
    super().__init__(None)
    self.origin:str|dict = entry
    self.text:list[str] = []
    self.update()

  def update(self) -> None:
    """Updates the text of the line
    If the origin is a string, the text will be set to the origin.
    If the origin is a dict, each key will be executed as a command with the value as argument and the output will be set as text.
    This method should be called to update the text after the object was created.
    """
    if isinstance(self.origin, str):
      self.text = [self.origin]
    if isinstance(self.origin, dict):
      result = []
      for key in self.origin:
        result.append(subprocess.getoutput(f"{key} {self.origin[key]}"))
      self.text = result

  def to_json_obj(self) -> tuple[str|None, dict|list|str|None]:
    """Converts the object to a json object
    """
    return None, self.origin

  def __str__(self) -> str:
    """Converts the object to a string

    Returns:
      str: the text of the lines
    """
    self.update()
    return "\n".join(self.text)


class CmdEntryConfig(ConfigObject):
  """Represents a command entry
  This class will be created from a json string.
  The command could be executed.
  If the command ends with "&read", the executor should wait for a key press before continuing.

  Args:
    key (str): the key of the command
    data (str): the command

  Attributes:
    key (str): the key of the command
    cmd (str): the command
    read (bool): the read flag
  """

  def __init__(self, key:str, data:str) -> None:
    """Initializes the command entry

    Args:
      key (str): the key of the command
      data (str): the command
    """
    super().__init__(key)
    self.cmd:str = data
    if self.cmd.lower()[-5:] == "&read":
      self.cmd = self.cmd[:-5]
      self.read = True
    else:
      self.read = False

  def to_json_obj(self) -> tuple[str|None, dict|list|str|None]:
    """Converts the object to a json object
    """
    cmd = self.cmd
    if self.read:
      cmd += "&read"
    return self.key, cmd

  def __str__(self) -> str:
    """Converts the object to a string

    Returns:
      str: the key (displayname) of the command
    """
    return str(self.key)
