import json


def extract_json(raw_output: str):
    """
    Parse a model response into JSON, tolerating markdown code fences and
    surrounding prose that models often add despite instructions not to.
    Raises (via json.loads) if there's no parseable JSON.
    """
    text = raw_output.strip()

    # Strip a leading ```json / ``` fence and a trailing ``` fence.
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
        text = text.strip()

    # If prose still surrounds it, slice from the first { to the last }.
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start:end + 1]

    return json.loads(text)