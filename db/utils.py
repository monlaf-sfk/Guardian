import datetime
import typing


import emoji
import localization
from configurator import config
import logging
import re

from datetime import datetime
from threading import  Thread






database = "assets/moder_bot"


def escape(s, quote=True):
    """
    Replace special characters "&", "<" and ">" to HTML-safe sequences.
    If the optional flag quote is true (the default), the quotation mark
    characters, both double quote (") and single quote (') characters are also
    translated.
    """
    s = s.replace("&", "&amp;") # Must be done first!
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    if quote:
        s = s.replace('"', "&quot;")
        s = s.replace('\'', "&#x27;")
    return s

def user_mention(from_user):
    if from_user.username:
        return " @" + from_user.username
    else:
        return u'<a href="tg://user?id={}">{}</a>'.format(from_user.id, escape(from_user.full_name))



async def write_log(bot, message, log_type = "default"):
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")

    log_message = "🕥 <i>" + current_time + "</i> <b>[" + log_type.upper() + "]</b> "
    log_message += message

    return await bot.send_message(config.groups.logs, log_message,disable_web_page_preview=True)

def get_restriction_time(string: str) -> typing.Optional[int]:
    """
    Get user restriction time in seconds

    :param string: string to check for multiplier. The last symbol should be one of:
        "m" for minutes, "h" for hours and "d" for days
    :return: number of seconds to restrict or None if error
    """
    if len(string) < 2:
        return None
    letter = string[-1]
    try:
        number = int(string[:-1])
    except:
        return None
    else:
        if letter == "m" or letter == "м":
            return 60 * number
        elif letter == "h" or letter == "ч":
            return 3600 * number
        elif letter == "d" or letter == "д":
            return 86400 * number
        else:
            return None


def get_report_comment(message_date: datetime, message_id: int, report_message: typing.Optional[str]) -> str:
    """
    Generates a report message for admins

    :param message_date: Datetime when reported message was sent
    :param message_id: ID of that message
    :param report_message: An optional note for admins so that they can understand what's wrong
    :return: A report message for admins in report chat
    """
    msg = localization.get_string("report_message").format(
        date=message_date.strftime(localization.get_string("report_date_format")),
        chat_id=get_url_chat_id(config.groups.main),
        msg_id=message_id)

    if report_message:
        msg += localization.get_string("report_note").format(note=report_message)
    return msg


def get_url_chat_id(chat_id: int) -> int:
    """
    Well, this value is a "magic number", so I have to explain it a bit.
    I don't want to use hardcoded chat username, so I just take its ID (see "group_main" variable above),
    add id_compensator and take a positive value. This way I can use https://t.me/c/{chat_id}/{msg_id} links,
    which don't rely on chat username.

    :param chat_id: chat_id to apply magic number to
    :return: chat_id for t.me links
    """
    return abs(chat_id+1_000_000_000_000)

def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text  # or whatever



#import psycopg2


log=True
if log:
    lastdate = datetime.now().strftime("%d.%m.%y")
    logger = logging.getLogger('log_db')
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(f'assets/logs/{lastdate}.log', mode='a')
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter(
            '[%(asctime)s] %(message)s', datefmt='%H:%M:%S')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
def new_file():
    if not log:
        return
    global lastdate, fh

    lastdate = datetime.now().strftime("%d.%m.%y")
    try:
        logger.removeHandler(fh)
    except:
        pass
    fh = logging.FileHandler(f'assets/logs/{lastdate}.log', mode='a')
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '[%(asctime)s] %(message)s', datefmt='%H:%M:%S')
    fh.setFormatter(formatter)
    logger.addHandler(fh)


def logs_admin(action: str, text: str):
    if lastdate != datetime.now().strftime("%d.%m.%y") or logger is None:
        new_file()
    logger.info(f'({action}): {text}')

def deEmojify(text):
    regrex_pattern = re.compile(pattern = "["
        u"\U0001F600-\U0001F64F"  # emoticons
                           "]+", flags = re.UNICODE)
    return regrex_pattern.sub(r'',text)

def write_admins_log(action: str, text: str):
    if not log:
        return
    Thread(target=logs_admin, args=(action,deEmojify(text))).start()

def id_from_reply(message):
    prev_message = message.reply_to_message
    if not prev_message:
        return None, None
    user_id = prev_message.from_user.id
    res = message.text.split(None, 1)
    if len(res) < 2:
        return user_id, ""
    return user_id, res[1]

MAX_MESSAGE_LENGTH = 4096
def split_message(msg: str) -> typing.List[str]:
    if len(msg) < MAX_MESSAGE_LENGTH:
        return [msg]

    else:
        lines = msg.splitlines(True)
        small_msg = ""
        result = []
        for line in lines:
            if len(small_msg) + len(line) < MAX_MESSAGE_LENGTH:
                small_msg += line
            else:
                result.append(small_msg)
                small_msg = line
        else:
            # Else statement at the end of the for loop, so append the leftover string.
            result.append(small_msg)

        return result
SMART_OPEN = '“'
SMART_CLOSE = '”'
START_CHAR = ('\'', '"', SMART_OPEN)
def remove_escapes(text: str) -> str:
    counter = 0
    res = ""
    is_escaped = False
    while counter < len(text):
        if is_escaped:
            res += text[counter]
            is_escaped = False
        elif text[counter] == "\\":
            is_escaped = True
        else:
            res += text[counter]
        counter += 1
    return res

def split_quotes(text: str) -> typing.List:
    if any(text.startswith(char) for char in START_CHAR):
        counter = 1  # ignore first char -> is some kind of quote
        while counter < len(text):
            if text[counter] == "\\":
                counter += 1
            elif text[counter] == text[0] or (text[0] == SMART_OPEN and text[counter] == SMART_CLOSE):
                break
            counter += 1
        else:
            return text.split(None, 1)

        # 1 to avoid starting quote, and counter is exclusive so avoids ending
        key = remove_escapes(text[1:counter].strip())
        # index will be in range, or `else` would have been executed and returned
        rest = text[counter + 1:].strip()
        if not key:
            key = text[0] + text[0]
        return list(filter(None, [key, rest]))
    else:
        return text.split(None, 1)


def extract_text(message) -> str:
    return message.text or message.caption or (message.sticker.emoji if message.sticker else None)

# NOTE: the url \ escape may cause double escapes
# match * (bold) (don't escape if in url)
# match _ (italics) (don't escape if in url)
# match ` (code)
# match []() (markdown link)
# else, escape *, _, `, and [

MATCH_MD = re.compile(r'\*(.*?)\*|'
                      r'_(.*?)_|'
                      r'`(.*?)`|'
                      r'(?<!\\)(\[.*?\])(\(.*?\))|'
                      r'(?P<esc>[*_`\[])')
BTN_URL_REGEX = re.compile(r"(\[([^\[]+?)\]\(buttonurl:(?:/{0,2})(.+?)(:same)?\))")
LINK_REGEX = re.compile(r'(?<!\\)\[.+?\]\((.*?)\)')
def _selective_escape(to_parse: str) -> str:
    """
    Escape all invalid markdown

    :param to_parse: text to escape
    :return: valid markdown string
    """
    offset = 0  # offset to be used as adding a \ character causes the string to shift
    for match in MATCH_MD.finditer(to_parse):
        if match.group('esc'):
            ent_start = match.start()
            to_parse = to_parse[:ent_start + offset] + '\\' + to_parse[ent_start + offset:]
            offset += 1
    return to_parse


def _calc_emoji_offset(to_calc) -> int:
    # Get all emoji in text.

    emoticons = emoji.emoji_list(to_calc)
    # Check the utf16 length of the emoji to determine the offset it caused.
    # Normal, 1 character emoji don't affect; hence sub 1.
    # special, eg with two emoji characters (eg face, and skin col) will have length 2, so by subbing one we
    # know we'll get one extra offset,
    return sum(len(e.group(0).encode('utf-16-le')) // 2 - 1 for e in emoticons)

def escape_markdown(text):
    """Helper function to escape telegram markup symbols."""
    escape_chars = '\*_`\['
    return re.sub(r'([%s])' % escape_chars, r'\\\1', text)

def markdown_parser(txt: str, entities = None, offset: int = 0) -> str:
    """
    Parse a string, escaping all invalid markdown entities.

    Escapes URL's so as to avoid URL mangling.
    Re-adds any telegram code entities obtained from the entities object.

    :param txt: text to parse
    :param entities: dict of message entities in text
    :param offset: message offset - command and notename length
    :return: valid markdown string
    """
    if not entities:
        entities = []
    if not txt:
        return ""

    prev = 0
    res = ""
    # Loop over all message entities, and:
    # reinsert code
    # escape free-standing urls
    for ent in entities:
        if ent.offset < -offset:
            continue
        start = ent.offset + offset  # start of entity
        end = ent.offset + offset + ent.length - 1  # end of entity
        data = {
            "url": "<N/A>",
            "text_link": "<N/A>",
            "code": "<N/A>"
        }
        # we only care about code, url, text links
        if ent.type in data.keys():

            # count emoji to switch counter
            count = _calc_emoji_offset(txt[:start])
            start -= count
            end -= count

            # URL handling -> do not escape if in [](), escape otherwise.
            if ent.type == "url":
                if any(match.start(1) <= start and end <= match.end(1) for match in LINK_REGEX.finditer(txt)):
                    continue
                # else, check the escapes between the prev and last and forcefully escape the url to avoid mangling
                else:
                    # TODO: investigate possible offset bug when lots of emoji are present
                    res += _selective_escape(txt[prev:start] or "") + escape_markdown(txt)

            # code handling
            elif ent.type == "code":
                res += _selective_escape(txt[prev:start]) + '`' + txt + '`'

            # handle markdown/html links
            elif ent.type == "text_link":
                res += _selective_escape(txt[prev:start]) + "[{}]({})".format(txt, ent.url)

            end += 1

        # anything else
        else:
            continue

        prev = end

    res += _selective_escape(txt[prev:])  # add the rest of the text
    return res


def button_markdown_parser(txt: str, entities = None, offset: int = 0) -> (str, typing.List):
    markdown_note = markdown_parser(txt, entities, offset)
    prev = 0
    note_data = ""
    buttons = []
    for match in BTN_URL_REGEX.finditer(markdown_note):
        # Check if btnurl is escaped
        n_escapes = 0
        to_check = match.start(1) - 1
        while to_check > 0 and markdown_note[to_check] == "\\":
            n_escapes += 1
            to_check -= 1

        # if even, not escaped -> create button
        if n_escapes % 2 == 0:
            # create a thruple with button label, url, and newline status
            buttons.append((match.group(2), match.group(3), bool(match.group(4))))
            note_data += markdown_note[prev:match.start(1)]
            prev = match.end(1)
        # if odd, escaped -> move along
        else:
            note_data += markdown_note[prev:to_check]
            prev = match.start(1) - 1
    else:
        note_data += markdown_note[prev:]

    return note_data, buttons
