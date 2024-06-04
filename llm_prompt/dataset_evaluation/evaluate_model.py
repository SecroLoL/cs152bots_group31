'''
Evaluate an LLM's ability to classify messages from custom dataset

Should be able to load a dataset and then query model for a response across each message.
'''
import os 
import sys 
import anthropic 

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))   # append the root to path

from enum import Enum
from typing import List, Tuple, Mapping
from src.claude_trials import prompt_claude, start_client
from src.constants import * 
from src.dataset_eval.process_dataset import Category, DataProcessor, Example
from sklearn.metrics import f1_score, confusion_matrix

ABUSE_TYPE_TO_CATEGORY = {
    "logistical": Category.LOGISTICAL,
    "graphic": Category.GRAPHIC,
    "propaganda": Category.PROPAGANDA,
    "threat": Category.THREAT,
    "other": Category.OTHER,
    "invalid": Category.INVALID,
}

class ModelInference:

    def __init__(self, client: anthropic.Anthropic):
        self.client = client
        self.processor = DataProcessor()
        self.moderator_context = DEFAULT_MOD_CONTEXT  # can be changed via `custom_args` in `infer_from_text()`
        self.classification_prep = DEFAULT_CLASSIFICATION_PREP  # ^


    def infer_from_text(self, message: str, custom_args: Mapping = {}) -> Tuple[bool, Category]:
        """
        Prompts claude to infer on the message. By default, this function asks Claude 
        to determine whether the message is related to terrorist recruitment activity
        and furthermore, to identify what kind of content it may be.

        Args:
            message (str): Message to be reviewed by LLM
            custom_args (Mapping): Dictionary of args that can be used to prompt Claude with custom prompting context, etc.

                see `src.claude_trials.prompt_claude()` for which args can be provided as custom args.
        """
        # TODO add custom prompting for Claude

        # For now, we use the default prompt
        result = prompt_claude(
            moderator_context=self.moderator_context,
            input_message=message,
            prompt_prepend=self.classification_prep,
            client=self.client
        )

        response_str = result.content[0].text

        # Convert result into an example object
        response_split = response_str.split(" ")
        pred, category = response_split[0], response_split[1]

        pred_bool = True if pred == "yes" else False
        category = ABUSE_TYPE_TO_CATEGORY.get(category, None)

        assert category is not None, f"Expected to find category type, but instead got {category}."

        return pred_bool, category
    
    def compute_results(self, true_labels: List[bool], pred_labels: List[bool], true_categories: List[Example], pred_categories: List[Example]):
        """
        Computes F1 scores and confusion matrices for labels and category predictions
        """
        # convert labels into integers
        CATEGORY_TO_ID = {cat : i for i, cat in enumerate(ABUSE_TYPE_TO_CATEGORY.keys())}

        true_categories = [CATEGORY_TO_ID.get(cat) for cat in true_categories]
        pred_categories = [CATEGORY_TO_ID.get(cat) for cat in pred_categories]

        true_labels = [0 if tag == False else True for tag in true_labels]
        pred_labels = [0 if tag == False else True for tag in pred_labels]

        weighted_labels_f1 = f1_score(true_labels, pred_labels, average='weighted')
        weighted_categories_f1 = f1_score(true_categories, pred_categories, average='weighted')

        cm_labels = confusion_matrix(true_labels, pred_labels)
        cm_categories = confusion_matrix(true_categories, pred_categories)

        return weighted_labels_f1, weighted_categories_f1, cm_labels, cm_categories     



    def evaluate_file(self, data_path: str, custom_args: Mapping = {}) -> float:

        # Load file data
        file_examples = self.processor.process_file(data_path)
        
        true_labels, label_preds = [], []
        true_categories, category_preds = [], []
        # Infer on the data
        for i, example in enumerate(file_examples):
            message = example.message
            true_label = example.flagged
            true_category = example.category
            pred, category = self.infer_from_text(
                                                  message, 
                                                  custom_args=custom_args
                                                  )
            
            # Compute general stats
            label_preds.append(pred)
            category_preds.append(category)
            true_labels.append(true_label)
            true_categories.append(true_category)

        labels_f1, categories_f1, labels_cm, categories_cm  = self.compute_results(
            true_labels=true_labels,
            pred_labels=label_preds,
            true_categories=true_categories,
            pred_categories=category_preds,
        )

        return labels_f1, categories_f1, labels_cm, categories_cm

    


def main():

    client = start_client()
    inference = ModelInference(client)

    sample_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "sample.txt")
    inference.evaluate_file(sample_path)


if __name__ == "__main__":
    main()