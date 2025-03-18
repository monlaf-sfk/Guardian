import threading

from sqlalchemy import func, distinct, Column, String, UnicodeText


from db.models import BASE


class BlackListFilters(BASE):
    __tablename__ = "blacklist"
    chat_id = Column(String(14), primary_key=True)
    trigger = Column(UnicodeText, primary_key=True, nullable=False)

    def __init__(self, chat_id, trigger):
        self.chat_id = str(chat_id)  # ensure string
        self.trigger = trigger

    def __repr__(self):
        return "<Blacklist filter '%s' for %s>" % (self.trigger, self.chat_id)

    def __eq__(self, other):
        return bool(isinstance(other, BlackListFilters)
                    and self.chat_id == other.chat_id
                    and self.trigger == other.trigger)




BLACKLIST_FILTER_INSERTION_LOCK = threading.RLock()

CHAT_BLACKLISTS = {}


def add_to_blacklist(chat_id, trigger, SESSION):
    with BLACKLIST_FILTER_INSERTION_LOCK:
        blacklist_filt = BlackListFilters(str(chat_id), trigger)

        SESSION.merge(blacklist_filt)  # merge to avoid duplicate key issues
        SESSION.commit()
        CHAT_BLACKLISTS.setdefault(str(chat_id), set()).add(trigger)


def rm_from_blacklist(chat_id, trigger, SESSION):
    with BLACKLIST_FILTER_INSERTION_LOCK:
        blacklist_filt = SESSION.query(BlackListFilters).get((str(chat_id), trigger))
        if blacklist_filt:
            if trigger in CHAT_BLACKLISTS.get(str(chat_id), set()):  # sanity check
                CHAT_BLACKLISTS.get(str(chat_id), set()).remove(trigger)

            SESSION.delete(blacklist_filt)
            SESSION.commit()
            return True

        SESSION.close()
        return False


def get_chat_blacklist(chat_id, SESSION):
    global CHAT_BLACKLISTS
    if CHAT_BLACKLISTS.get(str(chat_id), set()):
        return CHAT_BLACKLISTS.get(str(chat_id), set())
    try:
        chats = SESSION.query(BlackListFilters.chat_id).distinct().all()
        for (chat_id,) in chats:  # remove tuple by ( ,)
            CHAT_BLACKLISTS[chat_id] = []

        all_filters = SESSION.query(BlackListFilters).all()
        for x in all_filters:
            CHAT_BLACKLISTS[x.chat_id] += [x.trigger]
        CHAT_BLACKLISTS = {x: set(y) for x, y in CHAT_BLACKLISTS.items()}
    finally:
        SESSION.close()
        return CHAT_BLACKLISTS.get(str(chat_id), set())










