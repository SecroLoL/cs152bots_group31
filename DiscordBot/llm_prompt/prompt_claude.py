import os 
import sys 
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import requests
import json
import src.constants as constants


import anthropic

def start_client():

    load_dotenv()
    
    client = anthropic.Anthropic(
    )
    return client


def prompt_claude(moderator_context: str, input_message: str, prompt_prepend: str, client: anthropic.Anthropic):
    
    """
    Prompts Claude in order to receive out a text result from the model.

    Args:
        moderator_context (str): A description of the role that Claude should take on. See `src/constants.py` for an example. 
                                 This provides context for Claude that allows us to manipulate it to act as a certain role, e.g. moderator
        input_message (str): An input to Claude, AKA the prompt. In the case of classification, this is the user message from the Discord channel.
        prompt_prepend (str): Context that is provided to Claude about the problem at hand. This includes instructions on how to handle the input, what to do,
                              how to formulate a response, etc.
        client (Anthropic): The client object to access Claude through.
    """

    message = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1000,
    temperature=0,
    system=moderator_context,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"{prompt_prepend}{input_message}"
                }
            ]
        }
    ]
    )
    return message


def main():

    """
    In this example, we use the Claude API to classify on general text to determine what the modflow should look like.
    """

    client = start_client()

    result = prompt_claude(moderator_context=constants.DEFAULT_MOD_CONTEXT,
                  input_message="He's bringing a bomb tomorrow. Be there at White Plaza to watch the carnage.",
                  prompt_prepend=constants.DEFAULT_CLASSIFICATION_PREP,
                  client=client)
    print(result)
    return result


if __name__ == "__main__":
    main()