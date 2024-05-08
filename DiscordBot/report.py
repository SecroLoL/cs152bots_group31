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
    AWAITING_GENERAL_ADDNTL_CONTEXT = auto()

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
        self.output = {
            "organization_name": None,
            "category": None,
            "context": None,
            "location": None,
            "suspect": None,
            "urgent": None,
            "size": None,
            "post_content": None
        }   # output JSON sent to moderation team for further action
    
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

            reply = ""
            if message.content in NAVIGATE_TERROR_FLOW:  # user choosing to report terror case
                reply += "Choice confirmed.\n\n"
                reply += "Do you know the group the uploader of this content may be associated with?\n"
                reply += "If so, please provide the name of the group in the form of ('known: group name', e.g. 'known: ISIS').\n\n"
                reply += "If not, specify whether the group is located in the U.S. ('USA'), Abroad/International ('Intl'), or if you're unsure, write 'unknown'."
                # TODO update the output state obj with some additional fields here
                # The response should be one of 'known: ___', 'USA', 'Intl', 'unknown'.
                self.state = State.AWAITING_GROUP_IDENTIFICATION
            elif message.content in NAVIGATE_CYBER_EXPLICIT_FLOWS:  #  user reporting cyber harrassment/explicit content
                reply += "Choice confirmed.\n"
                reply += "Please provide additional context into the abuse you are reporting. Our moderation team will review your case and contact you for followup.\n"
                
                reply += "You may also provide a link to the Discord message content you are reporting so that our moderation team can directly review the post."
                self.state = State.AWAITING_GENERAL_ADDNTL_CONTEXT
            elif message.content in NAVIGATE_OTHER_FLOW:  # User reporting "Other" category
                reply += "We do not currently offer support for other categories of potential abuse.\n"
                reply += "However, we still encourage you to submit information regarding the offensive content.\n"
                reply += "Please provide any context to the abuse you are reporting. Our moderation team will contact you if future efforts are made into your case. "
                reply += "You may also provide a link to the Discord message content you are reporting so that our moderation team can directly review the post."

                self.state = State.AWAITING_GENERAL_ADDNTL_CONTEXT
            else:    # invalid input
                reply += f"Invalid input. Please choose one of the following options: `1`, `2`, `3`, `4`.\n"
                reply += f"Your input: `{message.content}`"
                # user remains in this part of the decision tree until a valid option is selected
            
            return [reply]
        
        if self.state == State.AWAITING_GENERAL_ADDNTL_CONTEXT:
            # We don't have to save this into the state of the Report output because we have no need
            # to implementation any backend functionality for non-terrorism reports. We can just
            # end this flow on the user end.
            reply = "Thank you for submitting your information. Our moderation team will review your report and contact you if further action is required.\n\n"
            reply += "We appreciate your time and effort to help us moderate platform content!"
            return [reply] 

        if self.state == State.AWAITING_GROUP_IDENTIFICATION:
            reply = ""
            response = message.content.lower()
            unknown_options = set(["usa", "intl", "unknown"])
            
            if response.startswith("known"):  # user knew the group
                response_components = response.split(":")
                group_name = response_components[-1].strip()

                self.output["organization"] = group_name
            
            elif response in unknown_options:   #  user didn't know the group
                self.output["organization"] = response

            else:   # invalid input
                reply += f"Invalid input. If you are familiar with the group, please type `known: [group name]`, e.g. `known: ISIS`.\n "
                reply += f"If you do not know the group, but you know they are based in the United States, type 'USA'. If they are based internationally, type 'Intl'.\n"
                reply += f"Otherwise, if you have no information about the organization, type 'Unknown'."
            
            if self.output.get("organization") is not None:  # we can proceed knowing the input was valid
                reply += f"What kind of terrorist recruitment content are you reporting? Choose from one of the following:\n\n"
                reply += "Graphic content/Disturbing Imagery (1)\n"
                reply += "Logistical coordination (2)\n"
                reply += "Propaganda promoting the terrorist organization and/or its members (3)\n"
                reply += "Active threat of impending violence (4)\n"
                reply += "Other (5)\n"

                self.state = State.AWAITING_POST_CATEGORY

            return [reply]

        if self.state == State.AWAITING_POST_CATEGORY:
            reply = ""
            response = message.content.strip().lower()  # lowercase and remove whitespace
            VALID_REPLIES = set([
                "1", "(1)", "2", "(2)", "3", "(3)", "4", "(4)", "5", "(5)"
            ])

            if response not in VALID_REPLIES:
                reply += "Invalid response. Try again.\n\n"
                reply += f"What kind of terrorist recruitment content are you reporting? Choose from one of the following:\n\n"
                reply += "Graphic content/Disturbing Imagery (1)\n"
                reply += "Logistical coordination (2)\n"
                reply += "Propaganda promoting the terrorist organization and/or its members (3)\n"
                reply += "Active threat of impending violence (4)\n"
                reply += "Other (5)\n"

                return [reply]
            # User gave a valid response

            response_to_category = {
                "1": "imagery",
                "(1)": "imagery",
                "2": "coordination",
                "(2)": "coordination",
                "3": "propaganda",
                "(3)": "propaganda",
                "4": "threat",
                "(4)": "threat",
                "5": "other",
                "(5)": "other"
            }

            self.output["category"] = response_to_category.get(response)
            if self.output["category"] is None:
                raise ValueError(f"Couldn't process response from the user into category type: {response}")
            
            # Proceed to next state by asking question about post context

            reply += "Please provide any additional context/information about the post you are reporting.\n"
            reply += "Format your response with a link to the message you are reporting, followed by any information you would like the moderation team to consider while reviewing your report.\n"
            self.state = State.AWAITING_CONTEXT_MSG
            return [reply]

        if self.state == State.AWAITING_CONTEXT_MSG:
            reply = ""
            context_response = message.content.strip().lower()
            # raw context
            self.output["context"] = context_response  

            # try getting the link if it exists from the content
            # Parse out the three ID strings from the message link
            m = re.search('/(\d+)/(\d+)/(\d+)', message.content)
            if not m:
                reply += f"ERROR: Could not find linked content inside of your response. Please start with your link and try again.\n"
            
            guild = self.client.get_guild(int(m.group(1)))
            if not guild:
                reply += "As a bot, I cannot accept reports of messages from guilds that I'm not in. Please have the guild owner add me to the guild and try again.\n"
            channel = guild.get_channel(int(m.group(2)))
            if not channel:
                reply += "It seems this channel was deleted or never existed. Please try again or say `cancel` to cancel.\n"
            try:
                message = await channel.fetch_message(int(m.group(3)))

                self.output["post_content"] = message.content
                self.output["suspect"] = message.author.name

            except discord.errors.NotFound:
                reply += "It seems this message was deleted or never existed. Please try again or say `cancel` to cancel.\n"
            
            reply += "Response received and confirmed!" + "\n\n\n"
            reply += "Do you believe the reported content poses an active/urgent threat to public safety? (Y/N)\n"
            
            self.state = State.AWAITING_THREAT_LEVEL  # transition to next state, wait for user to respond
            return [reply]  

        if self.state == State.AWAITING_THREAT_LEVEL:
            # TODO: fill in this section!
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
    