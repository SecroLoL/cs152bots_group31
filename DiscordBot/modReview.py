from enum import Enum, auto
import discord
import re

class State(Enum):
    REVIEW_START = auto()
    REVIEW_COMPLETE = auto()
    CHECK_URGENCY = auto()
    SUSPEND_USER = auto()
    REPORT_AUTHORITIES = auto()
    SUBMIT_REPORT = auto()
    FINAL_DECISION = auto()
    DETERMINE_SUSPENSION_DURATION = auto()
    REPORT_LINK = auto()


class ModReview:
    START_KEYWORD = "review"
    CANCEL_KEYWORD = "cancel"
    HELP_KEYWORD = "help"

    def __init__(self, client):
        self.state = State.REVIEW_START
        self.client = client
        self.message = None
        self.data = {}

    async def handle_message(self, message):
        if message.content == self.CANCEL_KEYWORD:
            return ["Review process cancelled.", self.state_to_review_complete()]
        
        if self.state == State.REVIEW_START:
            reply = "Welcome to the moderation review system. "
            reply += "You can type `help` anytime for assistance.\n\n"
            reply += "Kindly provide the URL of the Discord message you wish to review."
            self.state = State.REPORT_LINK
            return [reply]

        if self.state == State.REPORT_LINK:
            m = re.search('/(\d+)/(\d+)/(\d+)', message.content)
            if not m:
                return ["Unable to locate the message from the provided link. Please verify and try again or type `cancel` to abort."]
            guild = self.client.get_guild(int(m.group(1)))
            channel = guild.get_channel(int(m.group(2)))
            try:
                fetched_message = await channel.fetch_message(int(m.group(3)))
                self.data["report_content"] = fetched_message.content
                self.state = State.CHECK_URGENCY
                return ["Message successfully retrieved. Does this report represent an immediate threat? Please respond with 'yes' or 'no'."]
            except discord.errors.NotFound:
                return ["The message specified could not be found. Please check the link and try again, or type `cancel` to abort."]

        if self.state == State.CHECK_URGENCY:
            if message.content.lower() == "yes":
                self.state = State.REPORT_AUTHORITIES
                return ["This has been flagged as an immediate threat. A template for reporting to the FBI will be provided. Do you want to proceed with reporting to authorities? (yes/no)"]
            else:
                self.state = State.DETERMINE_SUSPENSION_DURATION
                return ["No immediate threat detected. Please determine the appropriate suspension duration: (1) 1 day, (2) 7 days, (3) 30 days, (4) Indefinite"]

        if self.state == State.DETERMINE_SUSPENSION_DURATION:
            option = message.content
            if option == "1":
                return ["User suspended for 1 day.", self.state_to_final_decision()]
            elif option == "2":
                return ["User suspended for 7 days.", self.state_to_final_decision()]
            elif option == "3":
                return ["User suspended for 30 days.", self.state_to_final_decision()]
            elif option == "4":
                return ["User suspended indefinitely.", self.state_to_final_decision()]
            else:
                return ["Invalid option. Please choose from (1) 1 day, (2) 7 days, (3) 30 days, (4) Indefinite"]

        if self.state == State.REPORT_AUTHORITIES:
            if message.content.lower() == "yes":
                return ["Submitting report to authorities.", self.state_to_submit_report()]
            else:
                return ["No action to report to authorities.", self.state_to_review_complete()]

        if self.state == State.SUBMIT_REPORT:
            return ["Report has been submitted to authorities. Thank you for your diligence.", self.state_to_review_complete()]

        if self.state == State.FINAL_DECISION:
            return ["Final review decisions have been made. The review process is now complete.", self.state_to_review_complete()]

    def state_to_review_complete(self):
        self.state = State.REVIEW_COMPLETE
        return "Review process completed."

    def state_to_submit_report(self):
        self.state = State.SUBMIT_REPORT
        return "Would you like to submit the report to authorities? (yes/no)"

    def state_to_final_decision(self):
        self.state = State.FINAL_DECISION
        return "Finalizing the review decisions. Would you like to take any further action? (yes/no)"

    def review_complete(self):
        return self.state == State.REVIEW_COMPLETE