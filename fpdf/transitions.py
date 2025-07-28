"""
Usage documentation at: <https://py-pdf.github.io/fpdf2/Presentations.html#transitions>
"""

from abc import ABC


class Transition(ABC):
    def serialize(self, _security_handler=None, _obj_id=None):
        raise NotImplementedError


class SplitTransition(Transition):
    def __init__(self, dimension, direction):
        if dimension not in ("H", "V"):
            raise ValueError(
                f"Unsupported dimension '{dimension}', must be H(horizontal) or V(ertical)"
            )
        self.dimension = dimension
        if direction not in ("I", "O"):
            raise ValueError(
                f"Unsupported direction '{direction}', must be I(nward) or O(utward)"
            )
        self.direction = direction

    def serialize(self, _security_handler=None, _obj_id=None):
        return f"<</Type /Trans /S /Split /DM /{self.dimension} /M /{self.direction}>>"


class BlindsTransition(Transition):
    def __init__(self, dimension):
        if dimension not in ("H", "V"):
            raise ValueError(
                f"Unsupported dimension '{dimension}', must be H(horizontal) or V(ertical)"
            )
        self.dimension = dimension

    def serialize(self, _security_handler=None, _obj_id=None):
        return f"<</Type /Trans /S /Blinds /DM /{self.dimension}>>"


class BoxTransition(Transition):
    def __init__(self, direction):
        if direction not in ("I", "O"):
            raise ValueError(
                f"Unsupported direction '{direction}', must be I(nward) or O(utward)"
            )
        self.direction = direction

    def serialize(self, _security_handler=None, _obj_id=None):
        return f"<</Type /Trans /S /Blinds /M /{self.direction}>>"


class WipeTransition(Transition):
    def __init__(self, direction):
        if direction not in (0, 90, 180, 270):
            raise ValueError(
                f"Unsupported direction '{direction}', must 0, 90, 180 or 270"
            )
        self.direction = direction

    def serialize(self, _security_handler=None, _obj_id=None):
        return f"<</Type /Trans /S /Wipe /Di /{self.direction}>>"


class DissolveTransition(Transition):
    def serialize(self, _security_handler=None, _obj_id=None):
        return "<</Type /Trans /S /Dissolve>>"


class GlitterTransition(Transition):
    def __init__(self, direction):
        if direction not in (0, 270, 315):
            raise ValueError(f"Unsupported direction '{direction}', must 0, 270 or 315")
        self.direction = direction

    def serialize(self, _security_handler=None, _obj_id=None):
        return f"<</Type /Trans /S /Glitter /Di /{self.direction}>>"


class FlyTransition(Transition):
    def __init__(self, dimension, direction=None):
        if dimension not in ("H", "V"):
            raise ValueError(
                f"Unsupported dimension '{dimension}', must be H(horizontal) or V(ertical)"
            )
        self.dimension = dimension
        if direction not in (0, 270, None):
            raise ValueError(
                f"Unsupported direction '{direction}', must 0, 270 or None"
            )
        self.direction = direction

    def serialize(self, _security_handler=None, _obj_id=None):
        return (
            f"<</Type /Trans /S /Glitter /M /{self.dimension} /Di /{self.direction}>>"
        )


class PushTransition(Transition):
    def __init__(self, direction):
        if direction not in (0, 270):
            raise ValueError(f"Unsupported direction '{direction}', must 0 or 270")
        self.direction = direction

    def serialize(self, _security_handler=None, _obj_id=None):
        return f"<</Type /Trans /S /Push /Di /{self.direction}>>"


class CoverTransition(Transition):
    def __init__(self, direction):
        if direction not in (0, 270):
            raise ValueError(f"Unsupported direction '{direction}', must 0 or 270")
        self.direction = direction

    def serialize(self, _security_handler=None, _obj_id=None):
        return f"<</Type /Trans /S /Cover /Di /{self.direction}>>"


class UncoverTransition(Transition):
    def __init__(self, direction):
        if direction not in (0, 270):
            raise ValueError(f"Unsupported direction '{direction}', must 0 or 270")
        self.direction = direction

    def serialize(self, _security_handler=None, _obj_id=None):
        return f"<</Type /Trans /S /Uncover /Di /{self.direction}>>"


class FadeTransition(Transition):
    def serialize(self, _security_handler=None, _obj_id=None):
        return "<</Type /Fade /S /Dissolve>>"
