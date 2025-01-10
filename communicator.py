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

from ollama import AsyncClient, Client, chat, ChatResponse
import json
import os
import re

curr_path = os.path.split(__file__)[0]
EMOTION_EXPRESSION_MAP = os.path.join(curr_path,"emotion_map.json")

with open(EMOTION_EXPRESSION_MAP,'r') as em:
    emotion_expression_map = json.load(em)


# {
#     "agree":"yes",
#     "disagree":"no",
#     "neutral":"idle",
#     "annoyed":"annoyed",
#     "happy":"greet"
# }

emotions = "\n".join(list(emotion_expression_map.keys()))

EMOTION_QUESTION=f"""
Before we start our conversation can you do the following for every answer:
When I ask something, before you give your answer give me one of the following expressions:
{emotions}

followed by a newline. Also I call you MIA from now on.
""" 

class Communicator:
    """
    This class handles the communication between
    the app and the llm.
    """
    PORT_KEY = "port"
    ADDRESS_KEY = "address"
    DEFAULT_HEADER = {'x-some-header': 'some-value'}
    MSG_KEY = "message"
    CONTENT_KEY="content"
    ROLE_KEY = "role"
    USER_ROLE = "user"
    ASSISTANT_ROLE = "assistant"
    def __init__(self,port=11434,address="localhost",protocol="http",version="llama3.2",history_file="memories.json",**_):
        self.port = port
        self.address = address
        self.protocol = protocol
        self.version = version
        
        self.host = protocol + "://" + address + '/' + str(port)
        self.client = Client(host=self.host,headers=self.DEFAULT_HEADER)
        # if file is not provided with path -> store in current dir
        if os.path.split(history_file)[0] == "":
            self.history_file = os.path.join(curr_path,history_file)
        else:
            self.history_file = history_file
        if os.path.exists(self.history_file):
            with open(self.history_file,'r') as fp:
                self._history = json.load(fp)
        else:
            self._history = []
    
    def chat(self,msg,stream=True):
        msg_dic = self.update_history(msg,role=self.USER_ROLE)
        answer = chat(model=self.version,
                     messages=self._history,
                     stream=stream,
                     )
        return answer
    
    def handle_chunk(self,chunk):
        """
        Handling of chunks to avoid direct calling
        """
        return chunk[self.MSG_KEY][self.CONTENT_KEY]
    
    def update_history(self,answer,role=ASSISTANT_ROLE):
        answer_dic = {self.ROLE_KEY:role,self.CONTENT_KEY:answer}
        self._history.append(answer_dic)
        return answer_dic
    
    def calibrate(self):
        """
        Calibrate the chat for proper answers with emotions
        """
        msg = EMOTION_QUESTION
        answer = self.chat(msg)
        answer_str = ""
        for chunk in answer:
            answer_str += self.handle_chunk(chunk)
        self.update_history(answer_str)
    
    def dump_history(self):
        """
        Store history on close in file
        """
        if hasattr(self,"history_file") and hasattr(self,"_history"):
            with open(self.history_file,'w') as fp:
                json.dump(self._history,fp)
    
    @staticmethod
    def check_emotion(msg):
        line1 = msg.partition('\n')[0].strip()
        if line1 in emotion_expression_map.keys():
            return emotion_expression_map[line1]
        else:
            return None
    
    @staticmethod
    def extract_emotion(msg):
        """
        Filters out all lines with emotion and returns rest as string and list of emotions.
        """
        words_to_match = list(emotion_expression_map.keys())
        if len(msg.splitlines()) == 1:
            emotions = [emotion_expression_map[e] for e in words_to_match if e==msg.strip()]
            return emotions, ['']
        
        word_regexes = []
        for word in words_to_match:
            escaped_word = re.escape(word)
            pattern = fr'{escaped_word}\W*\n' #fr'^\s*({escaped_word})\W*\n\n$'
            word_regexes.append(pattern)
        combined_pattern = '|'.join(word_regexes)
        regex = re.compile(combined_pattern)
        emotions = regex.findall(msg)
        emotions = [e.strip() for e in emotions]
        emotions = [emotion_expression_map[e] for e in emotions]
        texts = regex.split(msg)
        # ignore everything beofe first split
        if len(texts) > len(emotions):
            texts = texts[1:]
        
        return emotions,texts
        #return msg.partition('\n')[2].lstrip()
    
    @staticmethod
    def extract_text(msg):
        """
        Returns the filtered message
        """
        _, texts = Communicator.extract_emotion(msg)
        return '\n'.join(texts)

if __name__ == "__main__":
    print(EMOTION_QUESTION)
    msg = "happy\n\n\nI'm happy you like it! Lamp Haikus might not be as common, but I tried to capture its cozy and warm essence. If you're ready for more, I've got one about a cloud:\n\n\nagree \n\n\nWhispy clouds drift by\nSoftly shading the sun's face\nNature's gentle kiss"
    res,pat = Communicator.extract_emotion(msg)
    assert "yes" in res and "greet" in res
    msg2 = "neutral \nI don't have emotions or feelings, so I'm not capable of feeling annoyance. My previous response was a neutral acknowledgement that you were being slightly perturbing or frustrating."
    res2,pat2 = Communicator.extract_emotion(msg2)
    assert res2 == ["talk"]
