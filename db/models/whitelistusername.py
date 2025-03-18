from sqlalchemy import Column, Integer, String

from db.models import BASE


class WhiteUsername(BASE):
    __tablename__ = "whitelist_username"
    username: str = Column(String(32), primary_key=True)
    chat_id: int = Column(Integer)


    def __init__(self, chat_id, username):
        self.chat_id: int = chat_id
        self.username: str = username

    def __repr__(self):
        return "<WhiteUsername {}>".format(self.username)

