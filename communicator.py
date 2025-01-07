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

EMOTION_EXPRESSION_MAP = {
    "agree":"yes",
    "disagree":"no",
    "neutral":"idle",
    "annoyed":"annoyed",
    "happy":"greet"
}

emotions = "\n".join(list(EMOTION_EXPRESSION_MAP.keys()))

EMOTION_QUESTION=f"""
Before we start our conversation can you do the following for every answer:
When I ask something, before you give your answer give me one of the following expressions:
{emotions}

followed by a newline.
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
    USER_ROLE = "user"
    ASSISTANT_ROLE = "assistant"
    def __init__(self,port=11434,address="localhost",protocol="http",version="llama3.2",**_):
        self.port = port
        self.address = address
        self.protocol = protocol
        self.version = version
        
        self.host = protocol + "://" + address + '/' + str(port)
        self.client = Client(host=self.host,headers=self.DEFAULT_HEADER)
        self._history = []
    
    def chat(self,msg,stream=True):
        msg_dic = self.update_history(msg,role=self.USER_ROLE)
        answer = chat(model=self.version,
                     messages=self._history,
                     stream=stream,
                     )
        return answer
    
    def handle_chunk(self,chunk):
        return chunk[self.MSG_KEY][self.CONTENT_KEY]
    
    def update_history(self,anwser,role=ASSISTANT_ROLE):
        answer_dic = {"role":role,"content":answer}
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

if __name__ == "__main__":
    print(EMOTION_QUESTION)
