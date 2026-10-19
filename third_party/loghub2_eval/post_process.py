from .common import correct_single_template


def post_process(template):
    """Loghub-2.0's template-correction rules; apply to gold and predictions alike."""
    return correct_single_template(template)
