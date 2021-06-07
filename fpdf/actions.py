from abc import ABC
import warnings

from .util import enclose_in_parens


class Action(ABC):
    def dict_as_string(self):
        raise NotImplementedError


class NamedAction(Action):
    def __init__(self, action_name):
        if action_name not in ("NextPage", "PrevPage", "FirstPage", "LastPage"):
            warnings.warn("Non-standard named action added")
        self.action_name = action_name

    def dict_as_string(self):
        return f"/S /Named /N /{self.action_name}"


class GoToAction(Action):
    def __init__(self, dest):
        self.dest = dest

    def dict_as_string(self):
        return f"/S /GoTo /D {self.dest}"


class GoToRemoteAction(Action):
    def __init__(self, file, dest):
        self.file = file
        self.dest = dest

    def dict_as_string(self):
        return f"/S /GoToR /F {enclose_in_parens(self.file)} /D {self.dest}"


class LaunchAction(Action):
    def __init__(self, file):
        self.file = file

    def dict_as_string(self):
        return f"/S /Launch /F {enclose_in_parens(self.file)}"
