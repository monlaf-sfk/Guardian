import threading
import time

from sqlalchemy import Column, Integer, String, select, Sequence
from sqlalchemy.orm import Session

from db.models import BASE
from db.models.users import  Users


class AntiFlood(BASE):
    __tablename__ = "antiflood"
    id = Column(Integer, Sequence('seq_reg_id', start=1, increment=1), primary_key=True)
    user_id = Column(Integer)
    chat_id = Column(String(14))
    count = Column(Integer, default=0)
    limit = Column(Integer, default=5)
    limit_msg = Column(Integer, default=5)
    time = Column(Integer, default=5)

    def __init__(self, chat_id, user_id):
        self.chat_id = str(chat_id)  # ensure string
        self.user_id = str(user_id)  # ensure string

    def __repr__(self):
        return "<Chat {} User: {} ID: {}>".format(self.chat_id, self.user_id, self.id)



INSERTION_LOCK = threading.RLock()


async def check_flood(user_id, chat_id, session: Session):
    db_query = session.execute(select(AntiFlood).filter_by(user_id=user_id, chat_id=chat_id))
    antiflood: AntiFlood = db_query.scalar()
    if antiflood is None:
        antiflood = AntiFlood(chat_id,user_id)
        session.add(antiflood)
        session.flush()
    user = session.query(Users).get(user_id)
    time_delta = time.time() - float(user.last_message)
    if time_delta > float(antiflood.time):
        user.last_message = time.time()
        antiflood.count = 1
        session.add_all([antiflood,user])
        session.commit()
        return True
    if antiflood.count > antiflood.limit_msg:
        return False
    antiflood.count += 1
    session.add(antiflood)
    session.commit()
    return True


def create(chat_id, user_id, session: Session):
    with INSERTION_LOCK:
        fetch = session.query(AntiFlood).filter(chat_id=chat_id, user_id=user_id).get(user_id)
        if not fetch:
            curr = AntiFlood(chat_id, user_id)
            session.add(curr)
            session.flush()
        else:
            fetch.is_afk = True
        session.add(curr)
        session.commit()
