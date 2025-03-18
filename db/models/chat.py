import threading

from aiogram.types import Chat as OChat



from sqlalchemy import Column, String, Boolean, Integer
from sqlalchemy.orm import Session

from db.models import BASE


class Chat(BASE):
    __tablename__ = "chats"
    chat_id: int = Column(Integer, primary_key=True)
    title: str = Column(String, default=None)
    invite_link: str = Column(String, default=None)
    username: str = Column(String, default=None)
    permission: bool = Column(Boolean, default=False)
    message_count: int = Column(Integer, default=0)
    blocked: bool = Column(Boolean, default=False)
    def __init__(self, chat_inf: OChat):
        self.chat_id = chat_inf.id
        self.title = chat_inf.title

    def __repr__(self):
        return "<Chat {} {}>".format(self.chat_id ,self.permission)

INSERTION_LOCK = threading.RLock()

def update_chat(chat_inf: OChat, session: Session):
    with INSERTION_LOCK:
        chat = session.query(Chat).get(chat_inf.id)
        if not chat:
            chat = Chat(chat_inf)
            session.add(chat)
            session.flush()

        else:
            chat.title = chat_inf.title
            if chat_inf.username:
                chat.username = chat_inf.username
            if chat_inf.invite_link:
                chat.invite_link = chat_inf.invite_lin
        session.commit()
        return chat
def get_all_chats(SESSION):
    try:
        return SESSION.query(Chat).all()
    finally:
        SESSION.close()



