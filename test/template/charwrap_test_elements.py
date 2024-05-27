elements = [
    {
        "name": "multi",
        "type": "T",
        "x1": 80,
        "y1": 10,
        "x2": 170,
        "y2": 15,
        "text": "If multiline is False, the text should still not wrap even if wrapmode is specified.",
        "background": 0xEEFFFF,
        "multiline": False,
        "wrapmode": "WORD",
    },
    {
        "name": "multi",
        "type": "T",
        "x1": 80,
        "y1": 40,
        "x2": 170,
        "y2": 45,
        "text": "If multiline is True, and wrapmode is omitted, the text should wrap by word and not "
        + "cause an error due to omission of the wrapmode argument.",
        "background": 0xEEFFFF,
        "multiline": True,
    },
    {
        "name": "multi",
        "type": "T",
        "x1": 80,
        "y1": 70,
        "x2": 170,
        "y2": 75,
        "text": "If multiline is True and the wrapmode argument is provided, it should not cause a "
        + "problem even if using the default wrapmode of 'WORD'.",
        "background": 0xEEFFFF,
        "multiline": True,
        "wrapmode": "WORD",
    },
    {
        "name": "multi",
        "type": "T",
        "x1": 80,
        "y1": 100,
        "x2": 170,
        "y2": 105,
        "text": "If multiline is True and the wrapmode is 'CHAR', it should result in "
        + "wrapping based on characters instead of words, regardless of language (i.e. even though "
        + "this is designed to support scripts like Chinese and Japanese, wrapping long sentences "
        + "like this in English still demonstrates functionality.)",
        "background": 0xEEFFFF,
        "multiline": True,
        "wrapmode": "CHAR",
    },
]
