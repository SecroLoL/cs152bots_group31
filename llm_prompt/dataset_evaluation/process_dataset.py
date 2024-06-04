'''
Prepare a dataset file for evaluation from a LLM

Dataset structure is expected to be:

<message (str)> <terrorism content? (bool)> <subcategory (str), NONE if not terrorism content>
.
.
.


We want to extract these fields from each line and put them into custom data objects
'''
import os 
import sys 
import anthropic 

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))   # append the root to path

from enum import Enum
from typing import List, Tuple, Mapping
from src.claude_trials import prompt_claude, start_client
from src.constants import * 

class Category(Enum):

    GRAPHIC = "graphic content"
    LOGISTICAL = "logistical coordination"
    PROPAGANDA = "propaganda"
    THREAT = "active threat"
    OTHER = "other"
    INVALID = "not terrorist content"


class Example:

    def __init__(self, message: str, flagged: bool, category: Category):
        """
        Args:
            message (str): Text that is being reviewed
            flagged (bool): Whether this content has been auto-flagged
            category (Category): If this was flagged, what category it belongs to
        """
        self.message = message
        self.flagged = flagged 
        self.category = category 

    def __len__(self):
        # Length of the user message being reviewed
        return len(self.message) 


class DataProcessor:

    def __init__(self):

        self.tag_to_category = {
            "graphic": Category.GRAPHIC,
            "logistical": Category.LOGISTICAL,
            "propaganda": Category.PROPAGANDA,
            "threat": Category.THREAT,
            "other": Category.OTHER,
            "invalid": Category.INVALID
        }   # model outputs to category typing conversion

         
    def process_file(self, file_path: str) -> List[Example]:
        """
        Goes through input file and creates an `Example` instance for each line in the input.
        """ 
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Expected to find file {file_path} but did not.")
        
        final_examples = []
        with open(file_path, mode="r+", encoding="utf-8") as f:
            for line in f.readlines():
                line = line.strip()
                split_line = line.split(" ")

                flagged, category = split_line[-2], split_line[-1]
                message = " ".join(split_line[: -2])

                flagged = True if flagged.lower() == "yes" else False
                filtered_category = self.tag_to_category.get(category, None)

                assert category is not None, f"Category did not match any of the possible types: {category}"

                example = Example(message=message,
                                  flagged=flagged,
                                  category=filtered_category)
                
                final_examples.append(example)
        return final_examples    


def main():

    processor = DataProcessor()

    sample_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "sample.txt")
    examples = processor.process_file(sample_path)

    for example in examples:
        print("-------------")
        print(example.message)
        print(example.category, example.flagged)


if __name__ == "__main__":

    main()