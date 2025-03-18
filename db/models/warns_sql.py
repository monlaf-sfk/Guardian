import threading

from sqlalchemy import Integer, Column, String, UnicodeText, func, distinct, Boolean
from sqlalchemy.dialects import sqlite

from db.models import BASE


class Warns(BASE):
    __tablename__ = "warns"

    user_id = Column(Integer, primary_key=True)
    chat_id = Column(String(14), primary_key=True)
    num_warns = Column(Integer, default=0)
    reasons = Column(sqlite.TEXT)

    def __init__(self, user_id, chat_id):
        self.user_id = user_id
        self.chat_id = str(chat_id)
        self.num_warns = 0
        self.reasons = ''

    def __repr__(self):
        return "<{} warns for {} in {} for reasons {}>".format(self.num_warns, self.user_id, self.chat_id, self.reasons)


class WarnFilters(BASE):
    __tablename__ = "warn_filters"
    chat_id = Column(String(14), primary_key=True)
    keyword = Column(UnicodeText, primary_key=True, nullable=False)
    reply = Column(UnicodeText, nullable=False)

    def __init__(self, chat_id, keyword, reply):
        self.chat_id = str(chat_id)  # ensure string
        self.keyword = keyword
        self.reply = reply

    def __repr__(self):
        return "<Permissions for %s>" % self.chat_id

    def __eq__(self, other):
        return bool(isinstance(other, WarnFilters)
                    and self.chat_id == other.chat_id
                    and self.keyword == other.keyword)


class WarnSettings(BASE):
    __tablename__ = "warn_settings"
    chat_id = Column(String(14), primary_key=True)
    warn_limit = Column(Integer, default=3)
    type_warn = Column(String(14), default='mute')
    time_punish = Column(Integer, default=120)
    def __init__(self, chat_id, warn_limit=3, type_warn='mute', time_punish= 120):
        self.chat_id = str(chat_id)
        self.warn_limit = warn_limit
        self.type_warn = type_warn
        self.time_punish = time_punish

    def __repr__(self):
        return "<{} has {} possible warns.>".format(self.chat_id, self.warn_limit)




WARN_INSERTION_LOCK = threading.RLock()
WARN_FILTER_INSERTION_LOCK = threading.RLock()
WARN_SETTINGS_LOCK = threading.RLock()

WARN_FILTERS = {}


def warn_user(SESSION, user_id, chat_id, reason=None):
    with WARN_INSERTION_LOCK:
        warned_user = SESSION.query(Warns).get((user_id, str(chat_id)))
        if not warned_user:
            warned_user = Warns(user_id, str(chat_id))

        warned_user.num_warns += 1
        if reason:
            warned_user.reasons = warned_user.reasons + ";" + reason # TODO:: double check this wizardry

        reasons = warned_user.reasons
        num = warned_user.num_warns

        SESSION.add(warned_user)
        SESSION.commit()

        return num, reasons


def remove_warn(user_id, chat_id , SESSION):
    with WARN_INSERTION_LOCK:
        removed = False
        warned_user = SESSION.query(Warns).get((user_id, str(chat_id)))

        if warned_user and warned_user.num_warns > 0:
            warned_user.num_warns -= 1

            SESSION.add(warned_user)
            SESSION.commit()
            removed = True

        SESSION.close()
        return removed


def reset_warns(user_id, chat_id, SESSION):
    with WARN_INSERTION_LOCK:
        warned_user = SESSION.query(Warns).get((user_id, str(chat_id)))
        if warned_user:
            warned_user.num_warns = 0
            warned_user.reasons = ''

            SESSION.add(warned_user)
            SESSION.commit()
        SESSION.close()


def get_warns(user_id, chat_id, SESSION):
    try:
        user = SESSION.query(Warns).get((user_id, str(chat_id)))
        if not user:
            return None
        reasons = user.reasons
        num = user.num_warns
        return num, reasons
    finally:
        SESSION.close()


def add_warn_filter(chat_id, keyword, reply, SESSION):
    with WARN_FILTER_INSERTION_LOCK:
        warn_filt = WarnFilters(str(chat_id), keyword, reply)

        if keyword not in WARN_FILTERS.get(str(chat_id), []):
            WARN_FILTERS[str(chat_id)] = sorted(WARN_FILTERS.get(str(chat_id), []) + [keyword],
                                                key=lambda x: (-len(x), x))

        SESSION.merge(warn_filt)  # merge to avoid duplicate key issues
        SESSION.commit()


def remove_warn_filter(chat_id, keyword, SESSION):
    with WARN_FILTER_INSERTION_LOCK:
        warn_filt = SESSION.query(WarnFilters).get((str(chat_id), keyword))
        if warn_filt:
            if keyword in WARN_FILTERS.get(str(chat_id), []):  # sanity check
                WARN_FILTERS.get(str(chat_id), []).remove(keyword)

            SESSION.delete(warn_filt)
            SESSION.commit()
            return True
        SESSION.close()
        return False


def get_chat_warn_triggers(chat_id, SESSION):
    global WARN_FILTERS
    if WARN_FILTERS:
        return WARN_FILTERS.get(str(chat_id), set())
    try:
        chats = SESSION.query(WarnFilters.chat_id).distinct().all()
        for (chat_id,) in chats:  # remove tuple by ( ,)
            WARN_FILTERS[chat_id] = []

        all_filters = SESSION.query(WarnFilters).all()
        for x in all_filters:
            WARN_FILTERS[x.chat_id] += [x.keyword]

        WARN_FILTERS = {x: sorted(set(y), key=lambda i: (-len(i), i)) for x, y in WARN_FILTERS.items()}
    finally:
        SESSION.close()
        return WARN_FILTERS.get(str(chat_id), set())



def get_chat_warn_filters(chat_id, SESSION):
    try:
        return SESSION.query(WarnFilters).filter(WarnFilters.chat_id == str(chat_id)).all()
    finally:
        SESSION.close()


def get_warn_filter(chat_id, keyword, SESSION):
    try:
        return SESSION.query(WarnFilters).get((str(chat_id), keyword))
    finally:
        SESSION.close()


def set_warn_limit(SESSION, chat_id, warn_limit,type_warn =None, time_punish = None):
    with WARN_SETTINGS_LOCK:
        curr_setting = SESSION.query(WarnSettings).get(str(chat_id))
        if not curr_setting:
            curr_setting = WarnSettings(chat_id, warn_limit, type_warn)
        curr_setting.warn_limit = warn_limit

        curr_setting.type_warn = type_warn
        if time_punish:
            curr_setting.time_punish = time_punish

        SESSION.add(curr_setting)
        SESSION.commit()


def set_warn_strength(chat_id, type_warn, SESSION):
    with WARN_SETTINGS_LOCK:
        curr_setting = SESSION.query(WarnSettings).get(str(chat_id))
        if not curr_setting:
            curr_setting = WarnSettings(chat_id, type_warn=type_warn)

        curr_setting.type_warn = type_warn

        SESSION.add(curr_setting)
        SESSION.commit()


def get_warn_setting(chat_id, SESSION):
    try:
        setting = SESSION.query(WarnSettings).get(str(chat_id))
        if setting:
            return setting.warn_limit, setting.type_warn , setting.time_punish
        else:
            curr_setting = WarnSettings(chat_id)
            SESSION.add(curr_setting)
            SESSION.commit()
            return 3, 'mute', 120

    finally:
        SESSION.close()


def num_warns(SESSION):
    try:
        return SESSION.query(func.sum(Warns.num_warns)).scalar() or 0
    finally:
        SESSION.close()


def num_warn_chats(SESSION):
    try:
        return SESSION.query(func.count(distinct(Warns.chat_id))).scalar()
    finally:
        SESSION.close()


def num_warn_filters(SESSION):
    try:
        return SESSION.query(WarnFilters).count()
    finally:
        SESSION.close()


def num_warn_chat_filters(chat_id, SESSION):
    try:
        return SESSION.query(WarnFilters.chat_id).filter(WarnFilters.chat_id == str(chat_id)).count()
    finally:
        SESSION.close()


def num_warn_filter_chats(SESSION):
    try:
        return SESSION.query(func.count(distinct(WarnFilters.chat_id))).scalar()
    finally:
        SESSION.close()







