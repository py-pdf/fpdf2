# This is an implementation of the Unicode Standard Annex #9
# Unicode bidirectional algorithm - Revision 48 for Unicode 15.1.0
# https://unicode.org/reports/tr9/

import unicodedata
from collections import deque
from dataclasses import dataclass, replace
from operator import itemgetter
from typing import List, Tuple

from .enums import TextDirection

MAX_DEPTH = 125

# BidiBrackets 15.1.0 2023-01-18
# Loaded from https://www.unicode.org/Public/UNIDATA/BidiBrackets.txt
# This table can be dropped when the information is added on "unicodedata"
BIDI_BRACKETS = {
    "(": {"pair": ")", "type": "o"},
    ")": {"pair": "(", "type": "c"},
    "[": {"pair": "]", "type": "o"},
    "]": {"pair": "[", "type": "c"},
    "{": {"pair": "}", "type": "o"},
    "}": {"pair": "{", "type": "c"},
    "༺": {"pair": "༻", "type": "o"},
    "༻": {"pair": "༺", "type": "c"},
    "༼": {"pair": "༽", "type": "o"},
    "༽": {"pair": "༼", "type": "c"},
    "᚛": {"pair": "᚜", "type": "o"},
    "᚜": {"pair": "᚛", "type": "c"},
    "⁅": {"pair": "⁆", "type": "o"},
    "⁆": {"pair": "⁅", "type": "c"},
    "⁽": {"pair": "⁾", "type": "o"},
    "⁾": {"pair": "⁽", "type": "c"},
    "₍": {"pair": "₎", "type": "o"},
    "₎": {"pair": "₍", "type": "c"},
    "⌈": {"pair": "⌉", "type": "o"},
    "⌉": {"pair": "⌈", "type": "c"},
    "⌊": {"pair": "⌋", "type": "o"},
    "⌋": {"pair": "⌊", "type": "c"},
    "〈": {"pair": "〉", "type": "o"},
    "〉": {"pair": "〈", "type": "c"},
    "❨": {"pair": "❩", "type": "o"},
    "❩": {"pair": "❨", "type": "c"},
    "❪": {"pair": "❫", "type": "o"},
    "❫": {"pair": "❪", "type": "c"},
    "❬": {"pair": "❭", "type": "o"},
    "❭": {"pair": "❬", "type": "c"},
    "❮": {"pair": "❯", "type": "o"},
    "❯": {"pair": "❮", "type": "c"},
    "❰": {"pair": "❱", "type": "o"},
    "❱": {"pair": "❰", "type": "c"},
    "❲": {"pair": "❳", "type": "o"},
    "❳": {"pair": "❲", "type": "c"},
    "❴": {"pair": "❵", "type": "o"},
    "❵": {"pair": "❴", "type": "c"},
    "⟅": {"pair": "⟆", "type": "o"},
    "⟆": {"pair": "⟅", "type": "c"},
    "⟦": {"pair": "⟧", "type": "o"},
    "⟧": {"pair": "⟦", "type": "c"},
    "⟨": {"pair": "⟩", "type": "o"},
    "⟩": {"pair": "⟨", "type": "c"},
    "⟪": {"pair": "⟫", "type": "o"},
    "⟫": {"pair": "⟪", "type": "c"},
    "⟬": {"pair": "⟭", "type": "o"},
    "⟭": {"pair": "⟬", "type": "c"},
    "⟮": {"pair": "⟯", "type": "o"},
    "⟯": {"pair": "⟮", "type": "c"},
    "⦃": {"pair": "⦄", "type": "o"},
    "⦄": {"pair": "⦃", "type": "c"},
    "⦅": {"pair": "⦆", "type": "o"},
    "⦆": {"pair": "⦅", "type": "c"},
    "⦇": {"pair": "⦈", "type": "o"},
    "⦈": {"pair": "⦇", "type": "c"},
    "⦉": {"pair": "⦊", "type": "o"},
    "⦊": {"pair": "⦉", "type": "c"},
    "⦋": {"pair": "⦌", "type": "o"},
    "⦌": {"pair": "⦋", "type": "c"},
    "⦍": {"pair": "⦐", "type": "o"},
    "⦎": {"pair": "⦏", "type": "c"},
    "⦏": {"pair": "⦎", "type": "o"},
    "⦐": {"pair": "⦍", "type": "c"},
    "⦑": {"pair": "⦒", "type": "o"},
    "⦒": {"pair": "⦑", "type": "c"},
    "⦓": {"pair": "⦔", "type": "o"},
    "⦔": {"pair": "⦓", "type": "c"},
    "⦕": {"pair": "⦖", "type": "o"},
    "⦖": {"pair": "⦕", "type": "c"},
    "⦗": {"pair": "⦘", "type": "o"},
    "⦘": {"pair": "⦗", "type": "c"},
    "⧘": {"pair": "⧙", "type": "o"},
    "⧙": {"pair": "⧘", "type": "c"},
    "⧚": {"pair": "⧛", "type": "o"},
    "⧛": {"pair": "⧚", "type": "c"},
    "⧼": {"pair": "⧽", "type": "o"},
    "⧽": {"pair": "⧼", "type": "c"},
    "⸢": {"pair": "⸣", "type": "o"},
    "⸣": {"pair": "⸢", "type": "c"},
    "⸤": {"pair": "⸥", "type": "o"},
    "⸥": {"pair": "⸤", "type": "c"},
    "⸦": {"pair": "⸧", "type": "o"},
    "⸧": {"pair": "⸦", "type": "c"},
    "⸨": {"pair": "⸩", "type": "o"},
    "⸩": {"pair": "⸨", "type": "c"},
    "⹕": {"pair": "⹖", "type": "o"},
    "⹖": {"pair": "⹕", "type": "c"},
    "⹗": {"pair": "⹘", "type": "o"},
    "⹘": {"pair": "⹗", "type": "c"},
    "⹙": {"pair": "⹚", "type": "o"},
    "⹚": {"pair": "⹙", "type": "c"},
    "⹛": {"pair": "⹜", "type": "o"},
    "⹜": {"pair": "⹛", "type": "c"},
    "〈": {"pair": "〉", "type": "o"},
    "〉": {"pair": "〈", "type": "c"},
    "《": {"pair": "》", "type": "o"},
    "》": {"pair": "《", "type": "c"},
    "「": {"pair": "」", "type": "o"},
    "」": {"pair": "「", "type": "c"},
    "『": {"pair": "』", "type": "o"},
    "』": {"pair": "『", "type": "c"},
    "【": {"pair": "】", "type": "o"},
    "】": {"pair": "【", "type": "c"},
    "〔": {"pair": "〕", "type": "o"},
    "〕": {"pair": "〔", "type": "c"},
    "〖": {"pair": "〗", "type": "o"},
    "〗": {"pair": "〖", "type": "c"},
    "〘": {"pair": "〙", "type": "o"},
    "〙": {"pair": "〘", "type": "c"},
    "〚": {"pair": "〛", "type": "o"},
    "〛": {"pair": "〚", "type": "c"},
    "﹙": {"pair": "﹚", "type": "o"},
    "﹚": {"pair": "﹙", "type": "c"},
    "﹛": {"pair": "﹜", "type": "o"},
    "﹜": {"pair": "﹛", "type": "c"},
    "﹝": {"pair": "﹞", "type": "o"},
    "﹞": {"pair": "﹝", "type": "c"},
    "（": {"pair": "）", "type": "o"},
    "）": {"pair": "（", "type": "c"},
    "［": {"pair": "］", "type": "o"},
    "］": {"pair": "［", "type": "c"},
    "｛": {"pair": "｝", "type": "o"},
    "｝": {"pair": "｛", "type": "c"},
    "｟": {"pair": "｠", "type": "o"},
    "｠": {"pair": "｟", "type": "c"},
    "｢": {"pair": "｣", "type": "o"},
    "｣": {"pair": "｢", "type": "c"},
}


class BidiCharacter:
    __slots__ = [
        "character_index",
        "character",
        "bidi_class",
        "original_bidi_class",
        "embedding_level",
        "direction",
    ]

    def __init__(
        self, character_index: int, character: str, embedding_level: str, debug: bool
    ):
        self.character_index = character_index
        self.character = character
        if debug and character.isupper():
            self.bidi_class = "R"
        else:
            self.bidi_class = unicodedata.bidirectional(character)
        self.original_bidi_class = self.bidi_class
        self.embedding_level = embedding_level
        self.direction = None

    def get_direction_from_level(self):
        return "R" if self.embedding_level % 2 else "L"

    def set_class(self, cls):
        self.bidi_class = cls

    def __repr__(self):
        return (
            f"character_index: {self.character_index} character: {self.character}"
            + f" bidi_class: {self.bidi_class} original_bidi_class: {self.original_bidi_class}"
            + f" embedding_level: {self.embedding_level} direction: {self.direction}"
        )


@dataclass
class DirectionalStatus:
    __slots__ = [
        "embedding_level",
        "directional_override_status",
        "directional_isolate_status",
    ]
    embedding_level: int  # between 0 and MAX_DEPTH
    directional_override_status: str  # "N" (Neutral), "L" (Left) or "R" (Right)
    directional_isolate_status: bool


class IsolatingRun:
    __slots__ = ["characters", "previous_direction", "next_direction"]

    def __init__(self, characters: List[BidiCharacter], sos: str, eos: str):
        self.characters = characters
        self.previous_direction = sos
        self.next_direction = eos
        self.resolve_weak_types()
        self.resolve_neutral_types()
        self.resolve_implicit_levels()

    def resolve_weak_types(self) -> None:
        # W1. Examine each nonspacing mark (NSM) in the isolating run sequence, and change the type of the NSM to Other Neutral
        #     if the previous character is an isolate initiator or PDI, and to the type of the previous character otherwise.
        #     If the NSM is at the start of the isolating run sequence, it will get the type of sos.
        for i, bidi_char in enumerate(self.characters):
            if bidi_char.bidi_class == "NSM":
                if i == 0:
                    bidi_char.set_class(self.previous_direction)
                else:
                    bidi_char.set_class(
                        "ON"
                        if self.characters[i - 1].bidi_class
                        in ("LRI", "RLI", "FSI", "PDI")
                        else self.characters[i - 1].bidi_class
                    )

        # W2. Search backward from each instance of a European number until the first strong type (R, L, AL, or sos) is found.
        #     If an AL is found, change the type of the European number to Arabic number.
        # W3. Change all ALs to R.

        last_strong_type = self.previous_direction
        for bidi_char in self.characters:
            if bidi_char.bidi_class in ("R", "L", "AL"):
                last_strong_type = bidi_char.bidi_class
            if bidi_char.bidi_class == "AL":
                bidi_char.set_class("R")
            if bidi_char.bidi_class == "EN" and last_strong_type == "AL":
                bidi_char.set_class("AN")

        # W4. A single European separator between two European numbers changes to a European number.
        #     A single common separator between two numbers of the same type changes to that type.
        for i, bidi_char in enumerate(self.characters):
            if i in (0, len(self.characters) - 1):
                continue
            if (
                bidi_char.bidi_class == "ES"
                and self.characters[i - 1].bidi_class == "EN"
                and self.characters[i + 1].bidi_class == "EN"
            ):
                bidi_char.set_class("EN")

            if (
                bidi_char.bidi_class == "CS"
                and self.characters[i - 1].bidi_class in ("AN", "EN")
                and self.characters[i + 1].bidi_class
                == self.characters[i - 1].bidi_class
            ):
                bidi_char.set_class(self.characters[i - 1].bidi_class)

        # W5. A sequence of European terminators adjacent to European numbers changes to all European numbers.
        # W6. All remaining separators and terminators (after the application of W4 and W5) change to Other Neutral.
        def prev_is_en(i: int) -> bool:
            if i == 0:
                return False
            if self.characters[i - 1].bidi_class == "ET":
                return prev_is_en(i - 1)
            return self.characters[i - 1].bidi_class == "EN"

        def next_is_en(i: int) -> bool:
            if i == len(self.characters) - 1:
                return False
            if self.characters[i + 1].bidi_class == "ET":
                return next_is_en(i + 1)
            return self.characters[i + 1].bidi_class == "EN"

        for i, bidi_char in enumerate(self.characters):
            if bidi_char.bidi_class == "ET":
                if prev_is_en(i) or next_is_en(i):
                    bidi_char.set_class("EN")

            if bidi_char.bidi_class in ("ET", "ES", "CS"):
                bidi_char.set_class("ON")
        # W7. Search backward from each instance of a European number until the first strong type (R, L, or sos) is found.
        #     If an L is found, then change the type of the European number to L.
        last_strong_type = self.previous_direction
        for bidi_char in self.characters:
            if bidi_char.bidi_class in ("R", "L", "AL"):
                last_strong_type = bidi_char.bidi_class
            if bidi_char.bidi_class == "EN" and last_strong_type == "L":
                bidi_char.set_class("L")

    def pair_brackets(self) -> List[Tuple[int, int]]:
        """
        Calculate all the bracket pairs on an isolate run, to be used on rule N0
        How to calculate bracket pairs:
        - Basic definitions 14, 15 and 16: http://www.unicode.org/reports/tr9/#BD14
        - BIDI brackets for dummies: https://www.unicode.org/notes/tn39/
        """
        open_brackets = []
        open_bracket_count = 0
        bracket_pairs = []
        for index, char in enumerate(self.characters):
            if char.character in BIDI_BRACKETS and char.bidi_class == "ON":
                if BIDI_BRACKETS[char.character]["type"] == "o":
                    if open_bracket_count >= 63:
                        return []
                    open_brackets.append((char.character, index))
                    open_bracket_count += 1
                if BIDI_BRACKETS[char.character]["type"] == "c":
                    if open_bracket_count == 0:
                        continue
                    for current_open_bracket in range(open_bracket_count, 0, -1):
                        open_char, open_index = open_brackets[current_open_bracket - 1]
                        if (BIDI_BRACKETS[open_char]["pair"] == char.character) or (
                            BIDI_BRACKETS[open_char]["pair"] in ("〉", "〉")
                            and char.character in ("〉", "〉")
                        ):
                            bracket_pairs.append((open_index, index))
                            open_brackets = open_brackets[: current_open_bracket - 1]
                            open_bracket_count = current_open_bracket - 1
                            break
        return sorted(bracket_pairs, key=itemgetter(0))

    def resolve_neutral_types(self) -> None:
        def previous_strong(index: int):
            if index == 0:
                return self.previous_direction
            if self.characters[index - 1].bidi_class == "L":
                return "L"
            if self.characters[index - 1].bidi_class in ("R", "AN", "EN"):
                return "R"
            return previous_strong(index - 1)

        def next_strong(index: int):
            if index >= len(self.characters) - 1:
                return self.next_direction
            if self.characters[index + 1].bidi_class == "L":
                return "L"
            if self.characters[index + 1].bidi_class in ("R", "AN", "EN"):
                return "R"
            return next_strong(index + 1)

        # N0-N2: Resolving neutral types
        # N0
        brackets = self.pair_brackets()
        if brackets:
            embedding_direction = self.characters[0].get_direction_from_level()
            for b in brackets:
                strong_same_direction = False
                strong_opposite_direction = False
                resulting_direction = None
                for index in range(b[0], b[1]):
                    if (
                        self.characters[index].bidi_class == "L"
                        and embedding_direction == "L"
                    ) or (
                        self.characters[index].bidi_class in ("R", "AN", "EN")
                        and embedding_direction == "R"
                    ):
                        strong_same_direction = True
                        break
                    if (
                        self.characters[index].bidi_class == "L"
                        and embedding_direction == "R"
                    ) or (
                        self.characters[index].bidi_class in ("R", "AN", "EN")
                        and embedding_direction == "L"
                    ):
                        strong_opposite_direction = True
                if strong_same_direction:
                    resulting_direction = embedding_direction
                elif strong_opposite_direction:
                    opposite_direction = "L" if embedding_direction == "R" else "R"
                    if previous_strong(b[0]) == opposite_direction:
                        resulting_direction = opposite_direction
                    else:
                        resulting_direction = embedding_direction
                if resulting_direction:
                    self.characters[b[0]].bidi_class = resulting_direction
                    self.characters[b[1]].bidi_class = resulting_direction
                    if len(self.characters) > b[1] + 1:
                        next_char = self.characters[b[1] + 1]
                        if (
                            next_char.original_bidi_class == "NSM"
                            and next_char.bidi_class == "ON"
                        ):
                            next_char.bidi_class = resulting_direction

        for i, bidi_char in enumerate(self.characters):
            # N1-N2
            if bidi_char.bidi_class in (
                "B",
                "S",
                "WS",
                "ON",
                "FSI",
                "LRI",
                "RLI",
                "PDI",
            ):
                if previous_strong(i) == next_strong(i):
                    bidi_char.bidi_class = previous_strong(i)
                else:
                    bidi_char.bidi_class = bidi_char.get_direction_from_level()

    def resolve_implicit_levels(self) -> None:
        for bidi_char in self.characters:
            # I1. For all characters with an even (left-to-right) embedding level,
            #     those of type R go up one level and those of type AN or EN go up two levels.
            if bidi_char.embedding_level % 2 == 0:
                if bidi_char.bidi_class == "R":
                    bidi_char.embedding_level += 1
                if bidi_char.bidi_class in ("AN", "EN"):
                    bidi_char.embedding_level += 2

            # I2. For all characters with an odd (right-to-left) embedding level, those of type L, EN or AN go up one level.
            else:
                if bidi_char.bidi_class in ("L", "EN", "AN"):
                    bidi_char.embedding_level += 1


def auto_detect_base_direction(
    string: str, stop_at_pdi: bool = False, debug: bool = False
) -> TextDirection:
    """
    This function applies rules P2 and P3 to detect the direction of a paragraph, retuning
    the first strong direction and skipping over isolate sequences.
    P1 must be applied before calling this function (breaking into paragraphs)
    stop_at_pdi can be set to True to get the direction of a single isolate sequence
    """
    # Auto-LTR (standard BIDI) uses the first L/R/AL character, and is LTR if none is found.
    isolate = 0
    for char in string:
        bidi_class = unicodedata.bidirectional(char)
        if debug and bidi_class.isupper():
            bidi_class = "R"
        if bidi_class == "PDI" and isolate == 0 and stop_at_pdi:
            return TextDirection.LTR
        if bidi_class in ("LRI", "RLI", "FSI"):
            isolate += 1
        if bidi_class == "PDI" and isolate > 0:
            isolate -= 1
        if bidi_class in ("R", "AL") and isolate == 0:
            return TextDirection.RTL
        if bidi_class == "L" and isolate == 0:
            return TextDirection.LTR
    return TextDirection.LTR


def calculate_isolate_runs(paragraph: List[BidiCharacter]) -> List[IsolatingRun]:
    # BD13 and X10
    level_run = []
    lr = []
    lr_embedding_level = paragraph[0].embedding_level

    for bidi_char in paragraph:
        if bidi_char.embedding_level != lr_embedding_level:
            level_run.append(
                {"level": lr_embedding_level, "text": lr, "complete": False}
            )
            lr = []
            lr_embedding_level = bidi_char.embedding_level
        lr.append(bidi_char)
    level_run.append({"level": lr_embedding_level, "text": lr, "complete": False})

    def level_to_direction(level: int) -> str:
        if level % 2 == 0:
            return "L"
        return "R"

    # compute sos, eos for each level run
    for index, lr in enumerate(level_run):
        if lr["complete"]:
            continue
        if index == 0:
            sos = level_to_direction(lr["level"])
        else:
            sos = level_to_direction(max(lr["level"], level_run[index - 1]["level"]))
        if index == len(level_run) - 1:
            eos = level_to_direction(lr["level"])
        else:
            if lr["text"][-1].original_bidi_class in ("LRI", "RLI", "FSI"):
                # X10 - last char is an isolator without matching PDI - set EOS to embedding level
                eos = level_to_direction(lr["level"])
            else:
                eos = level_to_direction(
                    max(lr["level"], level_run[index + 1]["level"])
                )
        lr["sos"] = sos
        lr["eos"] = eos

    # combine levels runs to create isolate runs
    isolate_runs = []
    for index, lr in enumerate(level_run):
        if lr["complete"]:
            continue
        sos = lr["sos"]
        eos = lr["eos"]
        ir_chars = lr["text"]
        lr["complete"] = True
        if lr["text"][-1].original_bidi_class in ("LRI", "RLI", "FSI"):
            for nlr in level_run[index + 1 :]:
                if (
                    nlr["level"] == lr["level"]
                    and nlr["text"][0].original_bidi_class == "PDI"
                ):
                    lr["text"] += nlr["text"]
                    nlr["complete"] = True
                    eos = nlr["eos"]
                    if nlr["text"][-1].original_bidi_class not in ("LRI", "RLI", "FSI"):
                        break
        isolate_runs.append(IsolatingRun(characters=ir_chars, sos=sos, eos=eos))

    return isolate_runs


class BidiParagraph:
    __slots__ = (
        "text",
        "base_direction",
        "debug",
        "base_embedding_level",
        "characters",
    )

    def __init__(
        self, text: str, base_direction: TextDirection = None, debug: bool = False
    ):
        self.text = text
        self.base_direction = (
            auto_detect_base_direction(self.text, debug)
            if not base_direction
            else base_direction
        )
        self.debug = debug
        self.base_embedding_level = (
            0 if self.base_direction == TextDirection.LTR else 1
        )  # base level
        self.characters: List[BidiCharacter] = []
        self.get_bidi_characters()

    def get_characters(self) -> List[BidiCharacter]:
        return self.characters

    def get_characters_with_embedding_level(self) -> List[BidiCharacter]:
        # Calculate embedding level for each character after breaking isolating runs.
        # Only used on conformance testing
        self.reorder_resolved_levels()
        return self.characters

    def get_reordered_characters(self) -> List[BidiCharacter]:
        return self.reorder_resolved_levels()

    def get_all(self):
        return self.characters, self.reorder_resolved_levels()

    def get_reordered_string(self):
        "Used for conformance validation"
        return "".join(c.character for c in self.reorder_resolved_levels())

    def get_bidi_fragments(self):
        return self.split_bidi_fragments()

    def get_bidi_characters(self) -> List[BidiCharacter]:
        # Explicit levels and directions. Rule X1

        stack: List[DirectionalStatus] = deque()
        current_status = DirectionalStatus(
            embedding_level=self.base_embedding_level,
            directional_override_status="N",
            directional_isolate_status=False,
        )
        stack.append(replace(current_status))
        overflow_isolate_count = 0
        overflow_embedding_count = 0
        valid_isolate_count = 0
        results = []

        # Explicit embeddings. Process each character individually applying rules X2 through X8
        for index, char in enumerate(self.text):
            bidi_char = BidiCharacter(
                index, char, current_status.embedding_level, self.debug
            )
            new_bidi_class = None

            if bidi_char.bidi_class == "FSI":
                bidi_char.bidi_class = (
                    "LRI"
                    if auto_detect_base_direction(
                        self.text[index + 1 :], stop_at_pdi=True, debug=self.debug
                    )
                    == TextDirection.LTR
                    else "RLI"
                )

            if bidi_char.bidi_class in ("RLE", "LRE", "RLO", "LRO", "RLI", "LRI"):
                # X2 - X5: calculate explicit embeddings and explicit overrides
                if bidi_char.bidi_class[0] == "R":
                    new_embedding_level = (
                        current_status.embedding_level + 1
                    ) | 1  # least greater odd
                else:
                    new_embedding_level = (
                        current_status.embedding_level + 2
                    ) & ~1  # least greater even
                if (
                    bidi_char.bidi_class[2] == "I"
                    and current_status.directional_override_status != "N"
                ):
                    new_bidi_class = current_status.directional_override_status
                if (
                    new_embedding_level <= MAX_DEPTH
                    and overflow_isolate_count == 0
                    and overflow_embedding_count == 0
                ):
                    current_status.embedding_level = new_embedding_level
                    current_status.directional_override_status = (
                        bidi_char.bidi_class[0]
                        if bidi_char.bidi_class[2] == "O"
                        else "N"
                    )
                    if bidi_char.bidi_class[2] == "I":
                        valid_isolate_count += 1
                        current_status.directional_isolate_status = True
                    else:
                        current_status.directional_isolate_status = False
                    stack.append(replace(current_status))
                else:
                    if bidi_char.bidi_class[2] == "I":
                        overflow_isolate_count += 1
                    else:
                        if overflow_isolate_count == 0:
                            overflow_embedding_count += 1

            if bidi_char.bidi_class not in (
                "B",
                "BN",
                "RLE",
                "LRE",
                "RLO",
                "LRO",
                "PDF",
                "FSI",
                "PDI",
            ):  # X6
                if current_status.directional_override_status != "N":
                    new_bidi_class = current_status.directional_override_status

            if bidi_char.bidi_class == "PDI":  # X6a
                if overflow_isolate_count > 0:
                    overflow_isolate_count -= 1
                elif valid_isolate_count > 0:
                    overflow_embedding_count = 0
                    while True:
                        if not stack[-1].directional_isolate_status:
                            stack.pop()
                            continue
                        break
                    stack.pop()
                    current_status = replace(stack[-1])
                    valid_isolate_count -= 1
                assert isinstance(current_status, DirectionalStatus)
                bidi_char.embedding_level = current_status.embedding_level
                if current_status.directional_override_status != "N":
                    new_bidi_class = current_status.directional_override_status

            if bidi_char.bidi_class == "PDF":  # X7
                if overflow_isolate_count == 0:
                    if overflow_embedding_count > 0:
                        overflow_embedding_count -= 1
                    else:
                        if (
                            not current_status.directional_isolate_status
                            and len(stack) > 1
                        ):
                            stack.pop()
                            current_status = replace(stack[-1])

            if new_bidi_class:
                bidi_char.bidi_class = new_bidi_class
            if bidi_char.bidi_class not in (
                "RLE",
                "LRE",
                "RLO",
                "LRO",
                "PDF",
                "BN",
            ):  # X9
                if bidi_char.bidi_class == "B":
                    bidi_char.embedding_level = self.base_embedding_level
                elif bidi_char.original_bidi_class not in ("LRI", "RLI", "FSI"):
                    bidi_char.embedding_level = current_status.embedding_level
                results.append(bidi_char)

        if not results:
            self.characters = []
            return
        self.characters = results
        calculate_isolate_runs(results)

    def split_bidi_fragments(self):
        bidi_fragments = []
        if len(self.characters) == 0:
            return ()
        current_fragment = ""
        current_direction = ""
        for c in self.characters:
            if c.get_direction_from_level() != current_direction:
                if current_fragment:
                    bidi_fragments.append(
                        (
                            current_fragment,
                            (
                                TextDirection.RTL
                                if current_direction == "R"
                                else TextDirection.LTR
                            ),
                        )
                    )
                current_fragment = ""
                current_direction = c.get_direction_from_level()
            current_fragment += c.character
        if current_fragment:
            bidi_fragments.append(
                (
                    current_fragment,
                    (
                        TextDirection.RTL
                        if current_direction == "R"
                        else TextDirection.LTR
                    ),
                )
            )
        return tuple(bidi_fragments)

    def reorder_resolved_levels(self):
        before_separator = True
        end_of_line = True
        max_level = 0
        min_odd_level = 999
        for bidi_char in reversed(self.characters):
            # Rule L1. Reset the embedding level of segment separators, paragraph separators,
            # and any adjacent whitespace.
            if bidi_char.original_bidi_class in ("S", "B"):
                bidi_char.embedding_level = self.base_embedding_level
                before_separator = True
            elif bidi_char.original_bidi_class in (
                "BN",
                "WS",
                "FSI",
                "LRI",
                "RLI",
                "PDI",
            ):
                if before_separator or end_of_line:
                    bidi_char.embedding_level = self.base_embedding_level
            else:
                before_separator = False
                end_of_line = False

            if bidi_char.embedding_level > max_level:
                max_level = bidi_char.embedding_level
            if (
                bidi_char.embedding_level % 2 != 0
                and bidi_char.embedding_level < min_odd_level
            ):
                min_odd_level = bidi_char.embedding_level

        # Rule L2. From the highest level found in the text to the lowest odd level on each line,
        # reverse any contiguous sequence of characters that are at that level or higher.
        reordered_paragraph = self.characters.copy()
        for level in range(max_level, min_odd_level - 1, -1):
            temp_results = []
            rev = []
            for bidi_char in reordered_paragraph:
                if bidi_char.embedding_level >= level:
                    rev.append(bidi_char)
                else:
                    if rev:
                        rev.reverse()
                        temp_results += rev
                        rev = []
                    temp_results.append(bidi_char)
            if rev:
                rev.reverse()
                temp_results += rev
            reordered_paragraph = temp_results
        return tuple(reordered_paragraph)
