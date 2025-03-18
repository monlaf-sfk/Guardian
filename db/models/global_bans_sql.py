import threading

from sqlalchemy import Column, UnicodeText, Integer, String, Boolean

from db.models import BASE


class GloballyBannedUsers(BASE):
    __tablename__ = "gbans"
    user_id = Column(Integer, primary_key=True)
    name = Column(UnicodeText, nullable=False)
    reason = Column(UnicodeText)

    def __init__(self, user_id, name, reason=None):
        self.user_id = user_id
        self.name = name
        self.reason = reason

    def __repr__(self):
        return "<GBanned User {} ({})>".format(self.name, self.user_id)

    def to_dict(self):
        return {"user_id": self.user_id,
                "name": self.name,
                "reason": self.reason}


class GbanSettings(BASE):
    __tablename__ = "gban_settings"
    chat_id = Column(String(14), primary_key=True)
    setting = Column(Boolean, default=True, nullable=False)

    def __init__(self, chat_id, enabled):
        self.chat_id = str(chat_id)
        self.setting = enabled

    def __repr__(self):
        return "<Gban setting {} ({})>".format(self.chat_id, self.setting)





GBANNED_USERS_LOCK = threading.RLock()
GBAN_SETTING_LOCK = threading.RLock()
GBANNED_LIST = set()
GBANSTAT_LIST = set()


def gban_user(SESSION, user_id, name, reason=None):
    with GBANNED_USERS_LOCK:
        user = SESSION.query(GloballyBannedUsers).get(user_id)
        if not user:
            user = GloballyBannedUsers(user_id, name, reason)
        else:
            user.name = name
            user.reason = reason

        SESSION.merge(user)
        SESSION.commit()



def update_gban_reason(SESSION, user_id, name, reason=None):
    with GBANNED_USERS_LOCK:
        user = SESSION.query(GloballyBannedUsers).get(user_id)
        if not user:
            return None
        old_reason = user.reason
        user.name = name
        user.reason = reason

        SESSION.merge(user)
        SESSION.commit()
        return old_reason


def ungban_user(user_id, SESSION):
    with GBANNED_USERS_LOCK:
        user = SESSION.query(GloballyBannedUsers).get(user_id)
        if user:
            SESSION.delete(user)

        SESSION.commit()



def is_user_gbanned(user_id, SESSION):
    return SESSION.query(GloballyBannedUsers).get(user_id)


def get_gbanned_user(user_id, SESSION):
    try:
        return SESSION.query(GloballyBannedUsers).get(user_id)
    finally:
        SESSION.close()


def get_gban_list(SESSION):
    try:
        return [x.to_dict() for x in SESSION.query(GloballyBannedUsers).all()]
    finally:
        SESSION.close()


def enable_gbans(chat_id, SESSION):
    with GBAN_SETTING_LOCK:
        chat = SESSION.query(GbanSettings).get(str(chat_id))
        if not chat:
            chat = GbanSettings(chat_id, True)

        chat.setting = True
        SESSION.add(chat)
        SESSION.commit()



def disable_gbans(chat_id, SESSION):
    with GBAN_SETTING_LOCK:
        chat = SESSION.query(GbanSettings).get(str(chat_id))
        if not chat:
            chat = GbanSettings(chat_id, False)

        chat.setting = False
        SESSION.add(chat)
        SESSION.commit()


def does_chat_gban(chat_id, SESSION):
    try:
        gbanset:GbanSettings = SESSION.query(GbanSettings).get(chat_id)
        if not gbanset:
            gbanset = GbanSettings(chat_id, True)

        gbanset.setting = True
        SESSION.add(gbanset)
        SESSION.commit()
        return gbanset.setting
    finally:
        SESSION.close()







