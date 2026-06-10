import re

def extract_cpp_code(text: str) -> str:

    match = re.search(
        r"```(?:cpp|c\+\+)?\n(.*?)```",
        text,
        re.DOTALL
    )

    if match:
        return match.group(1).strip()

    return text.strip()