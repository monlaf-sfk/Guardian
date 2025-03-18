

import threading
from datetime import datetime

from aiogram.types import User
from sqlalchemy import Column, Integer, String, Boolean,DateTime
from sqlalchemy.orm import Session

from db.models import BASE


class Users(BASE):
    __tablename__ = "users"
    id: int = Column(Integer, primary_key=True)
    first_name: str = Column(String, default=None)
    username: str = Column(String, default=None)
    stop_in: datetime = Column(DateTime, default=datetime.now())
    message_count: int = Column(Integer, default=0)
    status: str = Column(String, default='member')
    send_report: bool = Column(Boolean, default=True)
    last_message: int = Column(Integer, default=0)

    def __init__(self, first_name, user_inf: User):
        self.id: int = user_inf.id
        self.first_name: str = first_name
        self.username: str = user_inf.username

    def __repr__(self):
        return "<User {}>".format(self.id)

    @property
    def link(self):
        url = f'https://t.me/{self.username}' if self.username else f'tg://user?id={self.id}' if self.username else \
            f'tg://openmessage?user_id={self.id}'
        return f'<a href="{url}">{self.first_name}</a>'



INSERTION_LOCK = threading.RLock()

def update_user(user_inf: User , session: Session):
    with INSERTION_LOCK:
        try:
            if user_inf:
                user = session.query(Users).get(user_inf.id)

            if not user:
                first_name = ''.join(filter(str.isalnum, user_inf.first_name))
                user = Users(first_name, user_inf)
                session.add(user)
                session.flush()
            else:
                first_name = ''.join(filter(str.isalnum, user_inf.first_name))
                user.first_name = first_name
                user.username = user_inf.username
            session.commit()
            return user
        finally:
            session.close()

