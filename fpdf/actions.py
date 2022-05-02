# pylint: disable=arguments-differ
from abc import ABC
import warnings

from .util import enclose_in_parens
from .syntax import build_obj_dict, create_dictionary_string


class Action(ABC):
    def __init__(self, next_action=None):
        """
        Args:
            next (PDFObject | str): optional reference to another Action to trigger after this one
        """
        self.next = next_action

    def dict_as_string(self, key_values=None):
        if key_values is None:
            key_values = {}
        if self.next:
            key_values["Next"] = self.next
        obj_dict = build_obj_dict(key_values)
        return create_dictionary_string(obj_dict, field_join=" ")


class NamedAction(Action):
    def __init__(self, action_name, next_action=None):
        super().__init__(next)
        if action_name not in ("NextPage", "PrevPage", "FirstPage", "LastPage"):
            warnings.warn("Non-standard named action added")
        self.action_name = action_name

    def dict_as_string(self):
        return super().dict_as_string({"S": "/Named", "N": f"/{self.action_name}"})


class GoToAction(Action):
    "As of 2022, this does not seem honored by neither Adobe Acrobat nor Sumatra readers."

    def __init__(self, dest, next_action=None):
        super().__init__(next_action)
        self.dest = dest

    def dict_as_string(self):
        return super().dict_as_string({"S": "/GoTo", "D": self.dest})


class GoToRemoteAction(Action):
    def __init__(self, file, dest, next_action=None):
        super().__init__(next_action)
        self.file = file
        self.dest = dest

    def dict_as_string(self):
        return super().dict_as_string(
            {"S": "/GoToR", "F": enclose_in_parens(self.file), "D": self.dest}
        )


class LaunchAction(Action):
    "As of 2022, this does not seem honored by neither Adobe Acrobat nor Sumatra readers."

    def __init__(self, file, next_action=None):
        super().__init__(next_action)
        self.file = file

    def dict_as_string(self):
        return super().dict_as_string(
            {"S": "/Launch", "F": enclose_in_parens(self.file)}
        )


# Annotation & actions that we tested implementing,
# but that revealed not be worth the effort:
# * Popup annotation & Hide action: as of june 2021,
#   do not seem support neither by Adobe Acrobat nor by Sumatra.
#   Moreover, they both use to indirect reference annotations,
#   and hence implementing them would need some consequent refactoring,
#   as annotations are currently defined "inline", not as dedicated PDF objects.
