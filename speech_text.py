#!/usr/bin/env python
# -*- coding: utf-8 -*-
#MIA - MIA Is not an Assistant
#Copyright (C) 2017  Stefan Reiterer

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
What MIA's voice says: the text of an answer without the marks of markdown and without stage directions.

  *smiles and waves*       one asterisk on each side: an expression or action, never spoken (MIA's rule, see communicator.EMOTION_QUESTION)
  **strong**, __strong__   emphasis does not work in speech: the words stay, the marks go
  # headings, > quotes, - lists, `code`, ~~strike~~, [text](link), tables: marks removed, link texts kept, links and images dropped

The chat page still shows the full text (the actions in italics); only the voice gets the filtered one.
While an answer is still being written (final=False) an action that is not closed yet is cut as well, so that "*smiles" is not
spoken before the closing asterisk arrives.
"""
import re

FENCE = re.compile(r"```.*?```", re.S)
BULLET = re.compile(r"^[ \t]*[-+*][ \t]+", re.M)
HEADING = re.compile(r"^[ \t]{0,3}#{1,6}[ \t]*", re.M)
QUOTE = re.compile(r"^[ \t]*>+[ \t]?", re.M)
TABLE_RULE = re.compile(r"^[ \t]*\|?[ \t]*:?-{2,}:?[ \t]*(\|[ \t]*:?-{2,}:?[ \t]*)*\|?[ \t]*$", re.M)
RULE = re.compile(r"^[ \t]*([-*_=][ \t]*){3,}$", re.M)
IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
URL = re.compile(r"https?://\S+")
# *action*: not part of ** and not inside a word, no blank after the opening and none before the closing asterisk, one paragraph
ACTION = re.compile(r"(?<![\*\w])\*(?![\*\s])(?:[^*\n]|\n(?!\n))+?(?<![\s\*])\*(?![\*\w])")
OPEN_ACTION = re.compile(r"(?<![\*\w])\*(?!\*)(?:[^*\n]|\n(?!\n))*\Z")
STRONG = re.compile(r"(\*\*|__)(.+?)\1", re.S)
UNDERSCORE = re.compile(r"(?<![\w_])_(?=\S)([^_\n]+?)(?<=\S)_(?![\w_])")
SPACE_BEFORE_PUNCTUATION = re.compile(r"[ \t]+([.,!?;:])")


def speech_text(text, final=True):
    """the text for the voice; "" when nothing is left to say"""
    if not text:
        return ""
    text = FENCE.sub(" ", str(text))
    text = BULLET.sub("", text)
    text = TABLE_RULE.sub("", text)
    text = RULE.sub("", text)
    text = HEADING.sub("", text)
    text = QUOTE.sub("", text)
    text = IMAGE.sub(" ", text)
    text = LINK.sub(r"\1", text)
    text = URL.sub(" ", text)
    text = ACTION.sub(" ", text)
    if not final:
        text = OPEN_ACTION.sub("", text)
    text = STRONG.sub(r"\2", text)
    text = UNDERSCORE.sub(r"\1", text)
    text = text.replace("~~", "").replace("`", "").replace("*", "").replace("|", " ")
    lines = []
    for line in text.splitlines():
        line = SPACE_BEFORE_PUNCTUATION.sub(r"\1", re.sub(r"[ \t]+", " ", line)).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)
