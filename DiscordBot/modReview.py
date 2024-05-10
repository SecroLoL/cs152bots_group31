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
        self.report_data = None

    async def handle_message(self, message):
        if message.content == self.CANCEL_KEYWORD:
            return ["Review process has been terminated.", self.state_to_review_complete()]

        if message.content.startswith(self.START_KEYWORD):
            if not self.client.to_be_reviewed:
                return ["No more reports to review.", self.state_to_review_complete()]

            self.report_data = self.client.to_be_reviewed.pop(0)
            post_content = self.report_data["post_content"]
            organization_name = self.report_data["organization_name"]
            category = self.report_data["category"]
            context = self.report_data["context"]
            location = self.report_data["location"]
            suspect = self.report_data["suspect"]
            urgent = "Yes" if self.report_data["urgent"] else "No"
            size = self.report_data["size"]

            formatted_message = (
                f"**Reviewing Report:**\n\n"
                f"**Organization:** {organization_name or 'Unknown'}\n"
                f"**Category:** {category or 'Not Specified'}\n"
                f"**Context:** {context or 'No additional context provided'}\n"
                f"**Location:** {location or 'Location not specified'}\n"
                f"**Suspect:** {suspect or 'Suspect information not provided'}\n"
                f"**Urgency:** {urgent}\n"
                f"**Group Size:** {size or 'Not specified'}\n\n"
                f"**Content:**\n{post_content or 'No content provided'}\n\n"
                f"Does this report represent an immediate threat? (yes/no)"
            )
            self.state = State.CHECK_URGENCY
            return [formatted_message]

        if self.state == State.CHECK_URGENCY:
            if message.content.lower() == "yes":
                self.state = State.REPORT_AUTHORITIES
                return ["This has been flagged as an immediate threat. A template for reporting to the FBI will be provided. Do you want to proceed with reporting to authorities? (yes/no)"]
            else:
                self.state = State.DETERMINE_SUSPENSION_DURATION
                return ["No immediate threat detected. Please determine the appropriate suspension duration: (1) 1 day, (2) 7 days, (3) 30 days, (4) Indefinite, (5) Suspension not required."]

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
            elif option == "5":
                return ["No suspension required.", self.state_to_final_decision()]
            else:
                return ["Invalid option. Please choose from (1) 1 day, (2) 7 days, (3) 30 days, (4) Indefinite"]

        if self.state == State.REPORT_AUTHORITIES:
            if message.content.lower() == "yes":
                self.state = State.SUBMIT_REPORT
                return ["Submitting report to authorities.", self.state_to_submit_report()]
            else:
                return ["No action to report to authorities.", self.state_to_review_complete()]

        if self.state == State.SUBMIT_REPORT:
            return ["Report has been submitted to authorities. Thank you for your diligence.", self.state_to_review_complete()]

        if self.state == State.FINAL_DECISION:
            reply = ["Final review decisions have been made. The review process is now complete."]
            if self.client.to_be_reviewed:
                reply.append("Do you want to review the next user report? (yes/no)")
                self.state = State.REVIEW_START  # Reset to start to handle the next report
            else:
                reply.append(self.state_to_review_complete())
            return reply

    def state_to_review_complete(self):
        self.state = State.REVIEW_COMPLETE
        return "Review process completed."

    def state_to_submit_report(self):
        self.state = State.SUBMIT_REPORT

    def state_to_final_decision(self):
        self.state = State.FINAL_DECISION
        return "Finalizing the review decisions. Would you like to take any further action? (yes/no)"

    def review_complete(self):
        return self.state == State.REVIEW_COMPLETE
