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
import random
import datetime

try:
    from .mia_logger import logger
    from .constants import CFG_FILE, TEXT_COLS, TIME_FORMAT, LOCALHOST
    from .constants import NEUTRAL_EMOTION_KEY, TIME_BEFORE_KEY, SIGNAL_EMOTION_KEY
    from . import utils
except ImportError:
    from mia_logger import logger
    from constants import CFG_FILE, TEXT_COLS, TIME_FORMAT, LOCALHOST
    from constants import NEUTRAL_EMOTION_KEY, TIME_BEFORE_KEY, SIGNAL_EMOTION_KEY
    import utils

curr_path = os.path.split(__file__)[0]
EMOTION_EXPRESSION_MAP = os.path.join(curr_path,"emotion_map.json")
PENALTIES_MAP = os.path.join(curr_path,"penalties.json")
POSSIBLE_PENALTIES_KEY = "possible"
RESPONSE_KEY = "response"
EMOTION_FORGOTTEN_KEY="emotion_forgotten"
ADDED_MESSAGE_KEY="added_message"

with open(EMOTION_EXPRESSION_MAP,'r') as em:
    EMOTION_EXPRESSION_MAP = json.load(em)
with open(PENALTIES_MAP,'r') as pm:
    penalties = json.load(pm)

emotions = "\n".join(list(EMOTION_EXPRESSION_MAP.keys()))

EMOTION_QUESTION=f"""
Before we start our conversation can you do the following for every answer:
When I ask something, before you give your answer give me one of the following expressions (lower case):
{emotions}

followed by a newline. Also I call you MIA from now on.
"""
SUMMARY_WORDS=2000
SUMMARIZE_QUESTION='''MIA, please summarize our complete chat history within {summary_words} words. Try to extract the topics we talked about and a short summary what the result of the discussion of each topic was. Please also look out for tasks marked with "{task_key}:" so that we don't forget them.'''
WAKE_UP_MSG = " After that pretend you just woke up in the next upcoming query (human brain summarizes memory during sleep, so this is an emulation after all)."
SUMMARIZE_PREAMBLE='MIA this was your summary of our history "{history}" abd this was you summary of our last of our last conversation: "{summary}".\n Use it for reference in our next conversation'

SUMMARIZE_LONG_QUESTION = 'MIA in the history you find summaries of our previous chats. I added timestamps to the questions so you may get a sense of the time the chats took place. Make a summary of all the discussion we had in the past based on those summaries that is at around {summary_words} words long.'

class MIANeutralEmotionException(Exception):
    pass
    
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
    TIME_TEMPLATE = """
    I send you this as information, that you know what time currently is since you don't have a clock and otherwise don't know what time it is. Is something upcoming?
    Send any emotion we agreed on followed by a newline and a short message 
    when something comes up at least {time_before} later or already overdue by at most {time_before} (e.g. an event we talked before or a 
    task which we talked about. I will mark them to you with the keyword "{task_key}:" followed by task, that you can find them more easily) 
    except "{neutral_emotion}" or respond only with the emotion "{neutral_emotion}" and nothing else that I know nothing is ahead or overdue. 
    So if nothing is to report really only respond with "{neutral_emotion}!". 
    """

    TIME_UPDATE="Hi MIA it is {time}." 
    
    def __init__(self,port=11434,address="localhost",protocol="http",version="llama3.2",
                 history_file="memories.json",neutral_emotion="disagree",time_before="1 hour",task_key="TASK",summary_words=2000,calibration_file="calibration.txt",
                 long_time_history_file="long_time_history.json",max_conversations=30,**_):
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
            
        if not os.path.exists(long_time_history_file):
            self.long_time_history_file = os.path.join(curr_path,long_time_history_file)
        else:
            self.long_time_history_file = long_time_history_file
        
        if os.path.exists(calibration_file):
            with open(calibration_file,'r') as cfp:
                self._addtional_calibration=cfp.read()
        elif os.path.exists(os.path.join(curr_path,calibration_file)):
            with open(os.path.join(curr_path,calibration_file),'r') as cfp:
                self._addtional_calibration=cfp.read()
        else:
            self._addtional_calibration=""
        
        time_update_msg = self.TIME_TEMPLATE.format(neutral_emotion=neutral_emotion,
                                                    time_before=time_before, task_key=task_key)
        self.time_update_msg = self.TIME_UPDATE + time_update_msg
        setattr(self,NEUTRAL_EMOTION_KEY,neutral_emotion)
        self.summarize_msg = SUMMARIZE_QUESTION.format(task_key=task_key,summary_words=summary_words)
        self.summarize_long_msg = SUMMARIZE_LONG_QUESTION.format(summary_words=summary_words//2)
        self._max_conversations = max_conversations
    
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
        """
        Updates the chat history.
        """
        answer_dic = {self.ROLE_KEY:role,self.CONTENT_KEY:answer}
        self._history.append(answer_dic)
        return answer_dic
    
    def _silent_conversation(self,msg):
        """
        Auxillary function for silent conversations in the backgroung.
        """
        answer = self.chat(msg)
        answer_str = ""
        for chunk in answer:
            answer_str += self.handle_chunk(chunk)
        return answer_str
        
    def calibrate(self):
        """
        Calibrate the chat for proper answers with emotions and other
        things the user wants to add e.g. a personality (in calibration_file).
        Furthermore an initial timestamp is added to tell MIA to look out for
        tasks.
        """
        msg = "\n".join((EMOTION_QUESTION,self._addtional_calibration))
        timestamp = utils.get_timestamp()[:-1]
        msg += self.time_update_msg.format(time=timestamp)
        answer_str = self._silent_conversation(msg)
        self.update_history(answer_str)
    
    def dump_history(self):
        """
        Store history on close in file
        """
        if hasattr(self,"history_file") and hasattr(self,"_history"):
            with open(self.history_file,'w') as fp:
                json.dump(self._history,fp,indent=2)
    
    def emulate_dreaming(self,wake_up=True):
        """
        Asks MIA to summarize the message hitory and replaces the
        memories with this summary. This emulates what brains do
        when they go to sleep (somewhat ...)
        currently done manual, but maybe automatic later on
        after a good frequency is known. Long time history
        is also stored. Maybe postrpocessing is added later
        to emulate long time memories. For now it's more
        for debugging.
        """
        msg = self.summarize_msg
        answer = self._silent_conversation(msg)
        self.update_history(answer)
        self.dump_history()
        
        # summarize including the long time history
        if os.path.exists(self.long_time_history_file):
            with open(self.long_time_history_file,'r') as fp:
                long_time_history = json.load(fp)
        else:
            long_time_history = []
        
        # summarize long time history adding new history
        long_time_history += self._history[-2:]
        self._history = long_time_history
        msg = self.summarize_long_msg
        timestamp = utils.get_timestamp()[:-1]
        msg += f" (Current time is {timestamp})"
        answer_long = self._silent_conversation(msg)
        self.update_history(answer_long)
        long_time_history = self._history
        with open(self.long_time_history_file,'w') as fp:
            json.dump(long_time_history,fp,indent=2)
        
        # use summaries as basis
        msg=SUMMARIZE_PREAMBLE.format(summary=answer,history=answer_long)
        # clear memory
        self._history = []
        self.dump_history()
        # start new history
        self.calibrate()
        if wake_up is True:
            msg += WAKE_UP_MSG
        answer=self._silent_conversation(msg)
        self.update_history(answer)
        self.dump_history()
        
    @staticmethod
    def check_emotion(msg):
        line1 = msg.partition('\n')[0].strip()
        if line1 in EMOTION_EXPRESSION_MAP:
            return line1
        else:
            return None
    
    @staticmethod
    def empty_emotion(msg):
        """
        Things to do when no emotion was recieved.
        """
        if "disagree" in EMOTION_EXPRESSION_MAP:
            emotions=["disagree"]
        texts = [msg,EMOTION_FORGOTTEN_KEY]
        logger.error(f"Error: Emotion forgotten with message {msg}")
        return emotions, texts
    
    @staticmethod
    def _determine_penalty(misdeed):
        """
        Penalizes MIA for misbehavior ... aka sends a fun message after a hickup.
        """
        response = penalties[misdeed][RESPONSE_KEY]
        possible = penalties[misdeed][POSSIBLE_PENALTIES_KEY]
        nr_penalties = len(possible)
        penalty_nr = random.randint(0,nr_penalties-1)
        penalty = possible[penalty_nr]
        answer = "\n".join([response,penalty])
        return answer
    
    def penalize(self,emotions,texts,_test=False):
        """
        Checks if something went wrong and penalize.
        """
        if _test is True:
            texts += [EMOTION_FORGOTTEN_KEY]
        
        if len(emotions)<len(texts):
            misdeed = texts[-1]
            penalty = self._determine_penalty(misdeed)
            return penalty
        else:
            return None
    
    @staticmethod
    def map_emotion(emotion):
        """
        Maps an emotion to provided expression.
        In case of doubt return "neutral"
        """
        if emotion in EMOTION_EXPRESSION_MAP:
            return EMOTION_EXPRESSION_MAP[emotion]
        elif emotion.upper() in EMOTION_EXPRESSION_MAP:
            return EMOTION_EXPRESSION_MAP[emotion.upper()]
        elif emotion.capitalize() in EMOTION_EXPRESSION_MAP:
            return EMOTION_EXPRESSION_MAP[emotion.capitalize()]
        else:
            return EMOTION_EXPRESSION_MAP["neutral"]
    
    @staticmethod
    def extract_emotion(msg):
        """
        Filters out all lines with emotion and returns rest as string and list of emotions.
        """
        # all emotions and some combinations
        words_to_match = list(EMOTION_EXPRESSION_MAP.keys())
        words_to_match += [e.capitalize() for e in EMOTION_EXPRESSION_MAP]
        words_to_match += [e.upper() for e in EMOTION_EXPRESSION_MAP]
        # filter duplicates
        words_to_match = list(set(words_to_match))
        
        if len(msg.splitlines()) == 1:
            emotions = [e for e in words_to_match if e==msg.strip()]
            if len(emotions) == 0:
                return Communicator.empty_emotion(msg)
            return emotions, ['']
        
        word_regexes = []
        for word in words_to_match:
            escaped_word = re.escape(word)
            pattern = fr'{escaped_word}\W*\n' #fr'^\s*({escaped_word})\W*\n\n$'
            word_regexes.append(pattern)
        combined_pattern = '|'.join(word_regexes)
        regex = re.compile(combined_pattern)
        # add a newline for easier finding of emotions at the end of text.
        msg += '\n'
        emotions = regex.findall(msg)
        emotions = [e.strip() for e in emotions]
        emotions = [e.lower() for e in emotions]
        texts = regex.split(msg)
        # ignore everything beofe first split
        if len(texts) > len(emotions):
            if len(emotions)>0:
                texts = texts[1:]
            else:
               emotions, texts = Communicator.empty_emotion(msg)
        
        # remove artificial newline if it is necessary
        if len(texts) > 1 and texts[-1] == '':
            texts = texts[:-1]
        return emotions,texts
        #return msg.partition('\n')[2].lstrip()
    
    @staticmethod
    def extract_text(msg):
        """
        Returns the filtered message
        """
        _, texts = Communicator.extract_emotion(msg)
        return '\n'.join(texts)
    
    def exchange(self,message,emotion_reaction=None,update_message=None,filter_message=True,
                 map_emotions_to_reactions=True,final_update=None):
        """
        Performs an message exchange.
        emotion_reaction is a callable
        which reacts to emotions found 
        in the message, If it is set to
        none an empty function is used.
        Similar, update_message is an 
        update function which reacts to
        the next chunk in the message.
        If None is provided an empty function
        is used as well.
        Filter message flag tells if the message
        function uses the message or the (emotion)
        filtered message.
        Returns the complete message and filtered
        messages alike.
        final_update is a function for message
        postprocessing. Maybe necessary for some cases.
        """
        if emotion_reaction is None:
            def emotion_reaction(emotion):
                return
        if update_message is None:
            def update_message(message):
                return
        if final_update is None:
            def final_update(answer,filt_answer,penalty):
                """
                By default final update checks if max length of conversation
                is reached, summarize and reset memory.
                """
                if len(self._history)>self._max_conversations*2+1:
                    self.emulate_dreaming(wake_up=False)
                return
        # init vars
        answer = ""
        emotion = None
        nr_emotions = 0
        answer_stream = self.chat(message)
        # process chunks
        try:
            for chunk in answer_stream:
                chunk_str = self.handle_chunk(chunk)
                answer += chunk_str
                emotions, text = self.extract_emotion(answer)
                # if new emotion in list process it
                if nr_emotions < len(emotions):
                    emotion = emotions[nr_emotions]
                    #tx = text[nr_emotions]
                    nr_emotions+= 1
                    arg = self.map_emotion(emotion) if map_emotions_to_reactions is True else emotion
                    emotion_reaction(arg)
                # update message
                to_send = self.extract_text(answer) if filter_message is True else answer
                update_message(to_send)
        except Exception as exc:
            # give expception back
            # but sorre current messge befor everything breaks down
            self.update_history(answer)
            self.dump_history()
            raise exc
        
        filt_answer = self.extract_text(answer)
        penalty = self.penalize(emotions, text)
        self.update_history(answer)
        self.dump_history()
        final_update(answer, filt_answer, penalty)
        return answer, filt_answer, penalty
    
    def time_update(self,emotion_expression=None,update_message=None,_test_neutral=False,
                    _test_neutral_but_penalty=False):
        """
        Function that Sends a request and should be scheduled.
        """
        timestamp = utils.get_timestamp()[:-1]
        message = self.time_update_msg.format(time=timestamp)
        if emotion_expression is None:
            def emotion_reaction(emotion):
                return
        if update_message is None:
            def update_message(message):
                return

        def _emotion_reaction(emotion):
            if emotion == getattr(self,NEUTRAL_EMOTION_KEY):
                return
            else: #if emotion == getattr(self,SIGNAL_EMOTION_KEY):
                expression = self.map_emotion(emotion)
                emotion_expression(expression)
            
        def _update_message(message):
            emotions, texts = Communicator.extract_emotion(message)
            emotion = emotions[0]
            text = "\n".join(texts)
            if emotion == getattr(self,NEUTRAL_EMOTION_KEY):
                pass
            else: 
                if texts[-1] == EMOTION_FORGOTTEN_KEY:
                    text = "\n".join(texts[:-1])
                update_message(text)
        
        # using final_update because maybe there is something to say
        def _final_update(answer,filt_answer,penalty):
            if _test_neutral is True:
                answer=getattr(self,NEUTRAL_EMOTION_KEY)
                breakpoint()
            if _test_neutral_but_penalty is True:
                answer=getattr(self,NEUTRAL_EMOTION_KEY)+'\n\nbla bla bla'
                
            emotions, texts = Communicator.extract_emotion(answer)
            emotion = emotions[0]
            text = "\n".join(texts)
            if emotion == getattr(self,NEUTRAL_EMOTION_KEY):
                if len(text)>0:
                    check = texts + [ADDED_MESSAGE_KEY]
                    penalty = self.penalize(emotions,check)
                else:
                    penalty = None
                    answer = None
                dic = dict(answer=answer,
                           filt_answer="\n".join(texts),
                           penalty=penalty)
                string = json.dumps(dic)
                raise MIANeutralEmotionException(string)
            
        # using exception handling for personal experiment ...
        def handle_mia_excp(mia_excp_msg):
            dic = json.loads(mia_excp_msg)
            answer, filt_answer, penalty = dic["answer"],dic["filt_answer"],dic["penalty"]
            self.update_history(getattr(self,NEUTRAL_EMOTION_KEY))
            self.dump_history()
            return answer, filt_answer, penalty
        
        try:
            answer, filt_answer, penalty = self.exchange(message,emotion_reaction=_emotion_reaction,
                                                         update_message=_update_message,
                                                         final_update=_final_update,
                                                         filter_message=False,
                                                         map_emotions_to_reactions=False)
        except MIANeutralEmotionException as mia_excp:
            answer, filt_answer, penalty = handle_mia_excp(str(mia_excp))
        return answer, filt_answer, penalty

def tests():
    print(EMOTION_QUESTION)
    
    msg = "happy\n\n\nI'm happy you like it! Lamp Haikus might not be as common, but I tried to capture its cozy and warm essence. If you're ready for more, I've got one about a cloud:\n\n\nagree \n\n\nWhispy clouds drift by\nSoftly shading the sun's face\nNature's gentle kiss"
    res,pat = Communicator.extract_emotion(msg)
    assert "happy" in res and "agree" in res
    
    msg2 = "neutral \nI don't have emotions or feelings, so I'm not capable of feeling annoyance. My previous response was a neutral acknowledgement that you were being slightly perturbing or frustrating."
    res2,pat2 = Communicator.extract_emotion(msg2)
    assert res2 == ["neutral"]
    
    msg3 = "After a while, Crocodile"
    res3,pat3 = Communicator.extract_emotion(msg3)
    assert res3 == ["disagree"] and pat3 == [msg3,EMOTION_FORGOTTEN_KEY]
    
    msg = "agree\n\n\nYes, I've checked the schedule, and it looks like you have an upcoming task. You're currently working at \"Going to sleep at 23:00 today (12.01.2025)\", which means you'll be sleeping in about 1 hour and 18 minutes. Disagree"
    emotions, texts = Communicator.extract_emotion(msg)
    assert emotions==["agree","disagree"]
    assert texts[-1]!=''
    

if __name__ == "__main__":
    tests()
