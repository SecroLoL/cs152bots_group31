from enum import Enum, auto
import discord
import re
from constants import *

class State(Enum):
    REPORT_START = auto()
    AWAITING_MSG_LINK = auto()
    MESSAGE_IDENTIFIED = auto()
    REPORT_COMPLETE = auto()

    # new states (one per node in tree traversal), generalized flow
    AWAITING_GENERAL_ABUSE_TYPE = auto()

    # new states for terrorism flow
    AWAITING_GROUP_IDENTIFICATION = auto()
    AWAITING_POST_CATEGORY = auto()
    AWAITING_CONTEXT_MSG = auto()
    AWAITING_THREAT_LEVEL = auto()


class Report:
    START_KEYWORD = "report"
    CANCEL_KEYWORD = "cancel"
    HELP_KEYWORD = "help"

    def __init__(self, client):
        self.state = State.REPORT_START
        self.client = client
        self.message = None
    
    async def handle_message(self, message):
        '''
        This function makes up the meat of the user-side reporting flow. It defines how we transition between states and what 
        prompts to offer at each of those states. You're welcome to change anything you want; this skeleton is just here to
        get you started and give you a model for working with Discord. 
        '''

        if message.content == self.CANCEL_KEYWORD:
            self.state = State.REPORT_COMPLETE
            return ["Report cancelled."]
        
        if self.state == State.REPORT_START:
            reply = "Thank you for beginning your report! Please answer the following questions regarding the nature of the content you are reporting.\n\n"
            reply += "What is the nature of the content that you are attempting to report? Select your choice from the options below.\n\n"
            reply += "Online harrassment/cyberbullying (1)\n"
            reply += "Nude/explicit photos of unconsenting parties, including minors (2)\n"
            reply += "Online terrorist recruitment (3)\n"
            reply += "Other (4)\n"

            self.state = State.AWAITING_GENERAL_ABUSE_TYPE
            return [reply]
        
        if self.state == State.AWAITING_GENERAL_ABUSE_TYPE:
            
            NAVIGATE_TERROR_FLOW = set(["3", "(3)"])   # user choosing to report terror case
            NAVIGATE_CYBER_EXPLICIT_FLOWS = set(["1", "(1)", "2", "(2)"])   # user chose option 1 or 2
            NAVIGATE_OTHER_FLOW = set(["4", "(4)"])   # they chose "Other"

            if message in NAVIGATE_TERROR_FLOW:  # user choosing to report terror case
                pass
            elif message in NAVIGATE_CYBER_EXPLICIT_FLOWS:  #  user reporting cyber harrassment/explicit content
                pass 
            elif NAVIGATE_OTHER_FLOW:  # User reporting "Other" category
                pass 
            else:    # invalid input
                pass 
            

        
        if self.state == State.AWAITING_MSG_LINK:
            # Parse out the three ID strings from the message link
            m = re.search('/(\d+)/(\d+)/(\d+)', message.content)
            if not m:
                return ["I'm sorry, I couldn't read that link. Please try again or say `cancel` to cancel."]
            guild = self.client.get_guild(int(m.group(1)))
            if not guild:
                return ["I cannot accept reports of messages from guilds that I'm not in. Please have the guild owner add me to the guild and try again."]
            channel = guild.get_channel(int(m.group(2)))
            if not channel:
                return ["It seems this channel was deleted or never existed. Please try again or say `cancel` to cancel."]
            try:
                message = await channel.fetch_message(int(m.group(3)))
            except discord.errors.NotFound:
                return ["It seems this message was deleted or never existed. Please try again or say `cancel` to cancel."]

            # Here we've found the message - it's up to you to decide what to do next!
            self.state = State.MESSAGE_IDENTIFIED
            return ["I found this message:", "```" + message.author.name + ": " + message.content + "```", \
                    "This is all I know how to do right now - it's up to you to build out the rest of my reporting flow!"]
        
        if self.state == State.MESSAGE_IDENTIFIED:
            return ["<insert rest of reporting flow here>"]

        return []

    def report_complete(self):
        return self.state == State.REPORT_COMPLETE
    