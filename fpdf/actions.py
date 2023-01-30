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

    def serialize(self):
        raise NotImplementedError

    def _serialize(self, key_values=None, security_handler=None, obj_id=0):
        if key_values is None:
            key_values = {}
        if self.next:
            key_values["Next"] = self.next
        obj_dict = build_obj_dict(key_values)
        if security_handler:
            obj_dict = self._encrypt_obj_dict(obj_dict, security_handler, obj_id)
        return create_dictionary_string(obj_dict, field_join=" ")

    def _encrypt_obj_dict(self, obj_dict, security_handler, obj_id):
        """Encrypt the strings present in the object dictionary"""
        for key in obj_dict:
            string = obj_dict[key]
            if (
                isinstance(string, str)
                and string.startswith("(")
                and string.endswith(")")
            ):
                obj_dict[key] = security_handler.encrypt(string[1:-1], obj_id)
        return obj_dict


class URIAction(Action):
    def __init__(self, uri, next_action=None):
        super().__init__(next)
        self.uri = uri

    def serialize(self, security_handler, obj_id):
        return super()._serialize(
            {"s": "/URI", "u_r_i": enclose_in_parens(self.uri)},
            security_handler,
            obj_id,
        )


class NamedAction(Action):
    def __init__(self, action_name, next_action=None):
        super().__init__(next)
        if action_name not in ("NextPage", "PrevPage", "FirstPage", "LastPage"):
            warnings.warn("Non-standard named action added")
        self.action_name = action_name

    def serialize(self, security_handler=None, obj_id=None):
        return super()._serialize(
            {"s": "/Named", "n": f"/{self.action_name}"},
            security_handler=security_handler,
            obj_id=obj_id,
        )


class GoToAction(Action):
    "As of 2022, this does not seem honored by neither Adobe Acrobat nor Sumatra readers."

    def __init__(self, dest, next_action=None):
        super().__init__(next_action)
        self.dest = dest

    def serialize(self, security_handler=None, obj_id=None):
        return super()._serialize(
            {"s": "/GoTo", "d": self.dest},
            security_handler=security_handler,
            obj_id=obj_id,
        )


class GoToRemoteAction(Action):
    def __init__(self, file, dest, next_action=None):
        super().__init__(next_action)
        self.file = file
        self.dest = dest

    def serialize(self, security_handler=None, obj_id=None):
        return super()._serialize(
            {"s": "/GoToR", "f": enclose_in_parens(self.file), "d": self.dest},
            security_handler=security_handler,
            obj_id=obj_id,
        )


class LaunchAction(Action):
    "As of 2022, this does not seem honored by neither Adobe Acrobat nor Sumatra readers."

    def __init__(self, file, next_action=None):
        super().__init__(next_action)
        self.file = file

    def serialize(self, security_handler=None, obj_id=None):
        return super()._serialize(
            {"s": "/Launch", "f": enclose_in_parens(self.file)},
            security_handler=security_handler,
            obj_id=obj_id,
        )


# Annotation & actions that we tested implementing,
# but that revealed not be worth the effort:
# * Popup annotation & Hide action: as of june 2021,
#   do not seem support neither by Adobe Acrobat nor by Sumatra.
#   Moreover, they both use to indirect reference annotations,
#   and hence implementing them would need some consequent refactoring,
#   as annotations are currently defined "inline", not as dedicated PDF objects.
