import threading

from sqlalchemy import Column, Integer, Boolean, String
from sqlalchemy.orm import Session

from db.models import BASE

punishmemt = {
    1: 'kick',
    2: 'mute',
    3: 'ban',
}
punishmemt_ = {
    'kick': 1,
    'mute': 2,
    'ban': 3,
}




class Settings(BASE):
    __tablename__ = "settings"
    chat_id: int = Column(Integer, primary_key=True)
    link: bool = Column(Boolean, default=True)
    text_link: bool = Column(Boolean, default=True)
    mention: bool = Column(Boolean, default=True)
    sender_chat: bool = Column(Boolean, default=True)
    via_bots: bool = Column(Boolean, default=False)
    forward_channel: bool = Column(Boolean, default=True)
    antiflood: bool = Column(Boolean, default=False)
    gif: bool = Column(Boolean, default=True)
    sticker: bool = Column(Boolean, default=True)

    def __init__(self, chat_id):
        self.chat_id: int = chat_id

    def __repr__(self):
        return "<SettingsId {}>".format(self.chat_id)


class PunishTime(BASE):
    __tablename__ = "punishtime"
    chat_id: int = Column(Integer, primary_key=True)
    time_stick: int = Column(Integer, default=120)
    time_gif: int = Column(Integer, default=120)
    time_link: int = Column(Integer, default=1200)
    time_text_link: int = Column(Integer, default=1200)
    time_mention: int = Column(Integer, default=120)
    time_via_bots: int = Column(Integer, default=60)
    time_forward_channel: int = Column(Integer, default=900)
    time_antiflood: int = Column(Integer, default=900)
    time_sender_chat: int = Column(Integer, default=120)

    def __init__(self, chat_id):
        self.chat_id: int = chat_id

    def __repr__(self):
        return "<PunishTimeId {}>".format(self.chat_id)


class Punish(BASE):
    __tablename__ = "punishment"
    chat_id: int = Column(Integer, primary_key=True)
    stick: str = Column(String(5), default='mute')
    gif: str = Column(String(5), default='mute')
    link: str = Column(String(5), default='mute')
    text_link: str = Column(String(5), default='mute')
    mention: str = Column(String(5), default='mute')
    via_bots: str = Column(String(5), default='mute')
    forward_channel: str = Column(String(5), default='mute')
    antiflood: str = Column(String(5), default='mute')
    sender_chat: str = Column(String(5), default='mute')
    def __init__(self, chat_id):
        self.chat_id: int = chat_id

    def __repr__(self):
        return "<PunishId {}>".format(self.chat_id)

INSERTION_LOCK = threading.RLock()
def update_settings(chat_id: int , session: Session):
    with INSERTION_LOCK:
        punish = session.query(Punish).get(chat_id)
        if not punish:
            punish = Punish(chat_id)
            session.add(punish)
            session.commit()

        settings = session.query(Settings).get(chat_id)
        if not settings:
            settings = Settings(chat_id)
            session.add(settings)
            session.commit()
        punishtime = session.query(PunishTime).get(chat_id)
        if not punishtime:
            punishtime = PunishTime(chat_id)
            session.add(punishtime)
            session.commit()

