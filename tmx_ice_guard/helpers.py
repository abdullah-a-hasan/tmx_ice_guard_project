import re


# helper funcs
def strip_tmx_tags(seg_text):
    # clean standard inline tmx tags
    clean = re.sub(r'<(it|ph|bpt|ept|hi).*?>.*?</\1>', " ", seg_text, flags=re.MULTILINE | re.I | re.DOTALL)
    clean = re.sub(r'<(it|ph|bpt|ept|hi).*?>', " ", clean, flags=re.MULTILINE | re.I | re.DOTALL)
    clean = re.sub(r'\s{2,}', ' ', clean, flags=re.MULTILINE | re.I | re.DOTALL)
    return clean.strip()


def pre_process_context(input_platform: str, text: str):
    """
    Pre-process context text obtained from the input platform. For example, platform specific tags can be cleaned up.
    :param input_platform: name of the platform where the context is coming from..
    :param text: context text to be processed.
    :return: str
    """
    if input_platform == 'phrase':
        replacements = [(r'{.>', ''), (r'<.}', '')]
        for pattern, replacement in replacements:
            text = re.sub(pattern, replacement, text)
        return text
    elif input_platform == 'memoq':
        replacements = [(r'^<seg>', ''), (r'</seg>$', '')]
        for pattern, replacement in replacements:
            text = re.sub(pattern, replacement, text)
        text = strip_tmx_tags(text)
        return text
    elif input_platform == 'trados':
        replacements = [(r' \| .+$', '')]
        for pattern, replacement in replacements:
            text = re.sub(pattern, replacement, text)
    return text


def post_process_context(target_platform: str, text: str):
    """
    Post-process context text aimed for the output platform. For example, platform specific tags can be added.
    :param target_platform: label of the platform where the context is going to.
    :param text: context text to be processed.
    :return:
    """
    if target_platform == 'memoq':
        text = "&lt;seg&gt;" + text + "&lt;/seg&gt;"
        return text
    return text
