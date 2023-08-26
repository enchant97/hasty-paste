import logging
from collections.abc import Generator

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import (find_lexer_class_by_name, get_all_lexers,
                             get_lexer_by_name)
from pygments.util import ClassNotFound as PygmentsClassNotFound
from quart.utils import run_sync
from ..config import get_settings

logger = logging.getLogger("paste_bin")


def get_highlighter_names() -> Generator[str, None, None]:
    """
    Return all highlighter names

        :yield: Each highlighter name
    """
    allowed_highlighters = get_settings().SYNTAX_HIGHLIGHTING_LANGUAGES
    if allowed_highlighters is not None:
        for language in allowed_highlighters:
            lexer = get_lexer_by_name(language, stripall=True)
            if lexer:
                yield language
            yield "text"
    else:
        for lexer in get_all_lexers():
            if lexer[1]:
                yield lexer[1][0]


def is_valid_lexer_name(lexer_name: str) -> bool:
    """
    Check whether the given name is a valid lexer name

        :param lexer_name: The name to check
        :return: Whether it is valid
    """
    try:
        _ = find_lexer_class_by_name(lexer_name)
        return True
    except PygmentsClassNotFound:
        return False


def highlight_content(content: str, lexer_name: str) -> str:
    """
    Highlight some content with a given lexer,
    will fallback to default lexer if given one is not found

        :param content: The content to highlight
        :param lexer_name: The lexer to use
        :return: The highlighted content as html
    """
    lexer = get_lexer_by_name("text", stripall=True)

    if lexer_name:
        try:
            lexer = get_lexer_by_name(lexer_name, stripall=True)
        except PygmentsClassNotFound:
            logger.debug(
                "skipping code highlighting as no lexer was found by '%s'", lexer_name)

    formatter = HtmlFormatter(linenos="inline", cssclass="highlighted-code")

    return highlight(content, lexer, formatter)


@run_sync
def highlight_content_async_wrapped(content: str, lexer_name: str) -> str:
    """
    Same as `highlight_content()` however is wrapped in Quart's `run_sync()`
    decorator to ensure event loop is not blocked

        :param content: The content to highlight
        :param lexer_name: The lexer to use
        :return: The highlighted content as html
    """
    return highlight_content(content, lexer_name)
