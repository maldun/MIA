#!/usr/bin/env python
# -*- coding: utf-8 -*-
#MIA - MIA Is not an Assistant
#Copyright (C) 2024  Stefan Reiterer

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

try:
    from .constants import TEXT_COLS, URL_KEY, TIME_FORMAT
    from . import constants as CONST
except ImportError:
    from constants import TEXT_COLS, URL_KEY, TIME_FORMAT
    import constants as CONST

import datetime
import markdown
import socket
from markdown import Markdown
class MyMarkdown(Markdown):
    """
    Stupid hack ...
    """
    PREFIX = "<p>"
    SUFFIX = "</p>"
    def convert(self, text,remove_paragraph=False):
        t = super().convert(text)
        if remove_paragraph is True:
            t = t.removeprefix(self.PREFIX).removesuffix(self.SUFFIX)
        return t

def cut_down_lines(answer,line_length=TEXT_COLS-2):
    """
    Cuts lines if they are too long.
    """
    lines = []
    for line in answer.splitlines():
        carry=""
        if len(line) > line_length:
            chunks = chunker(line,line_length)
            new_lines = []
            for chunk in chunks:
                new_line = chunk
                if len(carry) > 0:
                    new_line = carry+new_line
                    carry = ""
                if len(chunk.split())>1:
                    carry = chunk.split()[-1]
                    if new_line.endswith(carry):
                        new_line = new_line.removesuffix(carry)
                    else: # we have whitespace
                        white = new_line.split(carry)[-1]
                        new_line = new_line.rstrip().removesuffix(carry)
                        carry = carry+white
                new_lines += [new_line]
            if len(carry)>0:
                new_lines += [carry]
            lines += new_lines
        else:
            lines += [line]
    
    new_answer = "\n".join(lines)
    return new_answer

# -*- coding: utf-8 -*-
import re
alphabets= "([A-Za-z])"
prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
suffixes = "(Inc|Ltd|Jr|Sr|Co)"
starters = "(Mr|Mrs|Ms|Dr|Prof|Capt|Cpt|Lt|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](com|net|org|io|gov|edu|me)"
digits = "([0-9])"
multiple_dots = r'\.{2,}'

def split_into_sentences(text: str) -> list[str]:
    """
    Split the text into sentences.
    (Source: https://stackoverflow.com/a/31505798)
    
    If the text contains substrings "<prd>" or "<stop>", they would lead 
    to incorrect splitting because they are used as markers for splitting.

    :param text: text to be split into sentences
    :type text: str

    :return: list of sentences
    :rtype: list[str]
    """
    text = " " + text + "  "
    text = text.replace("\n"," ")
    text = re.sub(prefixes,"\\1<prd>",text)
    text = re.sub(websites,"<prd>\\1",text)
    text = re.sub(digits + "[.]" + digits,"\\1<prd>\\2",text)
    text = re.sub(multiple_dots, lambda match: "<prd>" * len(match.group(0)) + "<stop>", text)
    if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
    text = re.sub("\s" + alphabets + "[.] "," \\1<prd> ",text)
    text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>",text)
    text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
    text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
    text = re.sub(" " + alphabets + "[.]"," \\1<prd>",text)
    if "”" in text: text = text.replace(".”","”.")
    if "\"" in text: text = text.replace(".\"","\".")
    if "!" in text: text = text.replace("!\"","\"!")
    if "?" in text: text = text.replace("?\"","\"?")
    text = text.replace(".",".<stop>")
    text = text.replace("?","?<stop>")
    text = text.replace("!","!<stop>")
    text = text.replace("<prd>",".")
    sentences = text.split("<stop>")
    sentences = [s.strip() for s in sentences]
    if sentences and not sentences[-1]: sentences = sentences[:-1]
    return sentences

def split_into_lines_and_sentences(msg: str)->list[str]:
    """
    Converts a msg consisting of lines and breaks those lines into sentences.
    """
    lines = msg.splitlines()
    lines = [line for line in lines if len(line)>0]
    result = []
    for line in lines:
        result += split_into_sentences(line)
    return result

def chunker(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def filter_symbol_sentences(sentences):
    """
    Filters out sentences which consist only of symbols
    """
    regex = alphabets+r'+?'
    comp = re.compile(regex)
    proper_sentences = [s for s in sentences if len(comp.findall(s))>0]
    return proper_sentences

def get_websocket_url(protocol="http",address="localhost"):
    host = f'{address}'
    if not address in {"localhost","0.0.0.0","127.0.0.1"}:
        host = f"{protocol}://"+host
    return host

def get_own_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def replace_localhost(url):
    new_url=url
    oip = get_own_ip()
    for lh in {"localhost","0.0.0.0","127.0.0.1"}:
        new_url=new_url.replace(lh,oip)
    return new_url

def get_url(web=True,protocol="ws",address="localhost",web_port=None,**kwargs):
    """
    Combines a proper url and returns a dict for jsyfying
    """
    url = ""
    if isinstance(protocol,str):
        url += f"{protocol}://"
    if isinstance(address,str):
        url += address
    if isinstance(web_port,str) or isinstance(web_port,int):
        url += f":{web_port}"
    if web is True:
        url=replace_localhost(url)
    if "json" in kwargs:
        if kwargs["json"] is True:
            return {URL_KEY:url}
    return url

def get_timestamp():
    return datetime.datetime.now().strftime(TIME_FORMAT)

if __name__ == "__main__":
    # Tests
    msg2 = """
       /_/\ 
    ( ^ - ^ ) 
      >___<

     The kitty's snoozing!
    """
    expected = ["The kitty's snoozing!"]
    result = filter_symbol_sentences(split_into_lines_and_sentences(msg2))
    assert expected==result
    
    filt_msg="However, if you'd like, I can provide some general guidance or point you in the direction of resources that might help. Using Flask to play a sound on a webpage can be achieved using various methods, such as:\n\n1. Playing the audio directly from the server using `pygame` or `simpleaudio`.\n2. Serving the audio file as a binary data and playing it in the browser using JavaScript.\n\nIf you'd like more specific guidance, I can try to help you find some resources or provide code snippets that might get you started!"
    md = MyMarkdown(output_format='html')
    filt_msg = md.convert(filt_msg)
    msg4 =cut_down_lines(filt_msg)
    assert msg4.endswith("started!</p>")
    
    msg5 ="This is a common gotcha! Serving audio files directly from the server to be played in the browser can be tricky. You'll need to ensure that the MIME type is correct and that the browser can handle binary data. Here are some general steps:\n\n1. In your Flask app, use `send_file` to serve the `.wav` file as a binary response.\n2. In your JavaScript code, use the HTML5 `Audio` API or a library like Web Audio API to play the audio.\n\nHere's an example of how you might do this in Flask and JavaScript:\n```python\nfrom flask import Flask, send_file\n\napp = Flask(__name__)\n\n@app.route('/play_audio')\ndef play_audio():\n    return send_file('path/to/your/audio.wav', mimetype='audio/wav')\n\n# In your HTML file (client-side)\n<a id=\"play-button\" href=\"/play_audio\">Play Audio</a>\n\n<script>\n  const audioElement = document.createElement('audio');\n  audioElement.src = '/play_audio';\n  audioElement MIME-type: 'audio/wav';\n\n  // Play the audio\n  audioElement.play();\n</script>\n```\nThis is just a basic example, and you may need to modify it to fit your specific use case.\n\nIf you're feeling stuck, I can try to help you with more details or point you in the direction of some resources that might be helpful!"
    last="This is just a basic example, and you may need to modify it to fit your specific use case.\n\nIf you're feeling stuck, I can try to help you with more details or point you in the direction of some resources that might be helpful!"
    last2 =cut_down_lines(last)
    assert "case." in last2
    assert last2.endswith("helpful!")
    
    assert get_url(**{"address":"localhost","protocol":"http","web_port":30})=="http://localhost:30"
    assert get_url(json=True,**{"address":"localhost","protocol":"http","web_port":30})[URL_KEY]=="http://localhost:30"
    assert get_websocket_url()=="localhost"
    assert replace_localhost("localhost")==get_own_ip()
