# bot.py
import discord
from discord.ext import commands
import os
import json
import logging
import re
import requests
from report import Report
from modReview import ModReview
import pdb

from llm_prompt.prompt_claude import start_client, prompt_claude
import llm_prompt.constants as constants


# Set up logging to the console
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# There should be a file called 'tokens.json' inside the same folder as this file
token_path = 'tokens.json'
if not os.path.isfile(token_path):
    raise Exception(f"{token_path} not found!")
with open(token_path) as f:
    # If you get an error here, it means your token is formatted incorrectly. Did you put it in quotes?
    tokens = json.load(f)
    discord_token = tokens['discord']


class ModBot(discord.Client):
    def __init__(self): 
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='.', intents=intents)
        self.group_num = None
        self.mod_channels = {} # Map from guild to the mod channel id for that guild
        self.reports = {} # Map from user IDs to the state of their report
        self.reviews = {} 

        self.to_be_reviewed = []
        self.to_be_reviewed_automated = []
        self.claudeClient = start_client()

    async def on_ready(self):
        print(f'{self.user.name} has connected to Discord! It is these guilds:')
        for guild in self.guilds:
            print(f' - {guild.name}')
        print('Press Ctrl-C to quit.')

        # Parse the group number out of the bot's name
        match = re.search('[gG]roup (\d+) [bB]ot', self.user.name)
        if match:
            self.group_num = match.group(1)
        else:
            raise Exception("Group number not found in bot's name. Name format should be \"Group # Bot\".")

        # Find the mod channel in each guild that this bot should report to
        for guild in self.guilds:
            for channel in guild.text_channels:
                if channel.name == f'group-{self.group_num}-mod':
                    self.mod_channels[guild.id] = channel
        

    async def on_message(self, message):
        '''
        This function is called whenever a message is sent in a channel that the bot can see (including DMs). 
        Currently the bot is configured to only handle messages that are sent over DMs or in your group's "group-#" channel. 
        '''
        # Ignore messages from the bot 
        if message.author.id == self.user.id:
            return

        # Check if this message was sent in a server ("guild") or if it's a DM
        if message.guild:
            await self.handle_channel_message(message)
        else:
            await self.handle_dm(message)

    async def handle_dm(self, message):
        # Handle a help message
        if message.content == Report.HELP_KEYWORD:
            reply = "Thank you for requesting help from Group 31's discord bot.\n"
            reply += "To begin a user content report, use the `report` command.\n"
            reply += "Use the `cancel` command to cancel the report process.\n"
            await message.channel.send(reply)
            return

        author_id = message.author.id
        responses = []

        # Only respond to messages if they're part of a reporting flow
        if author_id not in self.reports and not message.content.startswith(Report.START_KEYWORD):
            return

        # If we don't currently have an active report for this user, add one
        if author_id not in self.reports:
            self.reports[author_id] = Report(self)

        # Let the report class handle this message; forward all the messages it returns to uss
        responses, final_outputs = await self.reports[author_id].handle_message(message)
        if final_outputs is not None:
            for out in final_outputs:
                self.to_be_reviewed.append(out)
        for r in responses:
            await message.channel.send(r)

        # If the report is complete or cancelled, remove it from our map
        if self.reports[author_id].report_complete():
            self.reports.pop(author_id)

    async def handle_channel_message(self, message):
        if message.channel.name == f'group-{self.group_num}':
            messageText = message.content
            classification = prompt_claude(constants.DEFAULT_MOD_CONTEXT, messageText, constants.DEFAULT_CLASSIFICATION_PREP, self.claudeClient)
            print(classification.content[0].text)
            threat_level = ""
            if classification.content[0].text == "Yes":
                threat_level = "Threatening"
            
            print(message.content)

            report_data = {
                'post_content': message.content,
                'message_id': message.id,
                'author': message.author.name,
                'channel': message.channel.name
            }

            # Add to automated review queue if threatening
            if threat_level == "Threatening":
                self.to_be_reviewed_automated.append(report_data)
                mod_channel = self.mod_channels.get(message.guild.id) 
                if mod_channel:
                    warning_message = f"Threat detected: {message.content}\nMessage ID: {message.id}\nAuthor: {message.author.name}\nChannel: {message.channel.name}\n"
                    await mod_channel.send(warning_message)  # Send message using the channel object
                else:
                    print(f"No mod channel found for guild {message.guild.name}")

            
        if message.channel.name == f'group-{self.group_num}-mod':
            if message.content == ModReview.HELP_KEYWORD:
                reply += "To initiate the reporting proccess, please type 'review' "
                reply += "To stop the reporting process, please type 'cancel'"
                await message.channel.send(reply)
            
            author_id = message.author.id
            if author_id not in self.reviews:
                if message.content.startswith(ModReview.START_KEYWORD) or message.content.startswith(ModReview.START_AUTO_KEYWORD) or message.content.startswith(ModReview.CLAUDE_REVIEW_KEYWORD) or message.content.startswith(ModReview.CLAUDE_AUTO_REVIEW_KEYWORD) :
                    self.reviews[author_id] = ModReview(self)
                else:
                    return  # Exit if the message isn't a start command and the author has no active review

            # Process the message through the corresponding ModReview instance
            responses = await self.reviews[author_id].handle_message(message)
            for response in responses:
                await message.channel.send(response)

            # Clean up the review object if the review process is complete
            if self.reviews[author_id].review_complete():
                del self.reviews[author_id]


        # Only handle messages sent in the "group-#" channel
        if not message.channel.name == f'group-{self.group_num}':
            return

        # # Forward the message to the mod channel
        # mod_channel = self.mod_channels[message.guild.id]
        # await mod_channel.send(f'Forwarded message:\n{message.author.name}: "{message.content}"')
        # scores = self.eval_text(message.content)
        # await mod_channel.send(self.code_format(scores))

    
    def eval_text(self, message):
        ''''
        TODO: Once you know how you want to evaluate messages in your channel, 
        insert your code here! This will primarily be used in Milestone 3. 
        '''
        return message

    
    def code_format(self, text):
        ''''
        TODO: Once you know how you want to show that a message has been 
        evaluated, insert your code here for formatting the string to be 
        shown in the mod channel. 
        '''
        return "Evaluated: '" + text+ "'"


client = ModBot()
client.run(discord_token)