from enum import Enum, auto
import discord
import re

from llm_prompt.prompt_claude import prompt_claude
import llm_prompt.constants as constants

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
    START_AUTO_KEYWORD = "detected review"
    CANCEL_KEYWORD = "cancel"
    CLAUDE_REVIEW_KEYWORD = "automate review"
    CLAUDE_AUTO_REVIEW_KEYWORD = "claude review"
    HELP_KEYWORD = "help"

    def __init__(self, client):
        self.state = State.REVIEW_START
        self.client = client
        self.message = None
        self.report_data = None
        self.is_automated_review = False
        self.is_claude_review = False

    async def handle_message(self, message):
        if message.content == self.CANCEL_KEYWORD:
            return ["Review process has been terminated.", self.state_to_review_complete()]

        if message.content.startswith(self.START_KEYWORD):
            self.is_automated_review = False
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
        
        if message.content.startswith(self.START_AUTO_KEYWORD):
            self.is_automated_review = True

            if not self.client.to_be_reviewed_automated:
                return ["No automated reports to review.", self.state_to_review_complete()]
            
            self.report_data = self.client.to_be_reviewed_automated.pop(0)
            post_content = self.report_data["post_content"]
            threat_level = self.report_data.get("threat_level", "Not specified")
            author = self.report_data["author"]
            channel = self.report_data["channel"]

            formatted_message = (
                f"**Reviewing Report:**\n\n"
                f"**Author:** {author}\n"
                f"**Channel:** {channel}\n"
                f"**Threat Level:** {threat_level}\n\n"
                f"**Content:**\n{post_content}\n\n"
                f"Does this report represent an immediate threat? (yes/no)"
            )
            self.state = State.CHECK_URGENCY
            return [formatted_message]
        
        if message.content.startswith(self.CLAUDE_REVIEW_KEYWORD):
             self.is_automated_review = False
             self.is_claude_review = True

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
                    f"**Content:**\n{post_content or 'No content provided'}\n"
             )

             prompt_prepend = "Review the report below and determine the necessary action based on the content's severity and implications. Choose the most appropriate response from the options provided. Answer 'Immediate threat', '1 day suspension', '7 days suspension', '30 days suspension', 'Indefinite suspension'. No explanation needed.\n\n"
             
             result = prompt_claude(moderator_context=constants.DEFAULT_MOD_CONTEXT,
                input_message= formatted_message,
                prompt_prepend=prompt_prepend,
                client=self.client.claudeClient)
             
             resultText = result.content[0].text

             if resultText == "Immediate threat":
                return [f"Reviewing new report:\n{formatted_message}\nDecision: This has been flagged as an immediate threat. Report has been submitted to authorities. Thank you for your diligence.", self.state_to_review_complete()]
             elif "suspension" in resultText:
               days = re.findall(r'\d+|Indefinite', resultText)
               if days[0] == "Indefinite":
                    suspension_message = "User suspended indefinitely."
               else:
                    suspension_message = f"User suspended for {days[0]} days."

               return [f"Reviewing new automated report:\n{formatted_message}\nDecision: No immediate threat detected. {suspension_message}", self.state_to_review_complete()]
             
        if message.content.startswith(self.CLAUDE_AUTO_REVIEW_KEYWORD):
             self.is_automated_review = True
             self.is_claude_review = True

             if not self.client.to_be_reviewed_automated:
                return ["No automated reports to review.", self.state_to_review_complete()]

             self.report_data = self.client.to_be_reviewed_automated.pop(0)
             post_content = self.report_data["post_content"]
             author = self.report_data["author"]
             channel = self.report_data["channel"]

             formatted_message = (
                f"**Reviewing Report:**\n\n"
                f"**Author:** {author}\n"
                f"**Channel:** {channel}\n"
                f"**Content:**\n{post_content}\n"
             )

             prompt_prepend = "Review the report below and determine the necessary action based on the content's severity and implications. Choose the most appropriate response from the options provided. Answer 'Immediate threat', '1 day suspension', '7 days suspension', '30 days suspension', 'Indefinite suspension'. No explanation needed.\n\n"
             
             result = prompt_claude(moderator_context=constants.DEFAULT_MOD_CONTEXT,
                input_message= formatted_message,
                prompt_prepend=prompt_prepend,
                client=self.client.claudeClient)
            
             resultText = result.content[0].text

             if resultText == "Immediate threat":
                return [f"Reviewing new automated report:\n{formatted_message}\nDecision: This has been flagged as an immediate threat. Report has been submitted to authorities. Thank you for your diligence.", self.state_to_review_complete()]
             elif "suspension" in resultText:
                days = re.findall(r'\d+|Indefinite', resultText)
                if days[0] == "Indefinite":
                    suspension_message = "User suspended indefinitely."
                else:
                    suspension_message = f"User suspended for {days[0]} days."

                return [f"Reviewing new automated report:\n{formatted_message}\nDecision: No immediate threat detected. {suspension_message}", self.state_to_review_complete()]




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
            if self.is_automated_review and self.client.to_be_reviewed_automated and not self.is_claude_review:
                reply.append("Do you want to review another automated report? (yes/no)")
                self.state = State.REVIEW_START
            elif not self.is_automated_review and self.client.to_be_reviewed and not self.is_claude_review:
                reply.append("Do you want to review the next user report? (yes/no)")
                self.state = State.REVIEW_START
            elif self.is_automated_review and self.client.to_be_reviewed_automated and self.is_claude_review:
                reply.append("Do you want to automatically review another automated report? (yes/no)")
                self.state = State.REVIEW_START
            elif not self.is_automated_review and self.client.to_be_reviewed and self.is_claude_review:
                reply.append("Do you want to automatically review another user report? (yes/no)")
                self.state = State.REVIEW_START
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
