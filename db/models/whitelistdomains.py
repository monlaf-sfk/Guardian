from sqlalchemy import Column, Integer, String

from db.models import BASE


class WhiteDomains(BASE):
    __tablename__ = "whitelist_domains"
    domen: str = Column(String, primary_key=True)
    chat_id: int = Column(Integer)

    def __init__(self, chat_id, domen):
        self.chat_id: int = chat_id
        self.domen: int = domen

    def __repr__(self):
        return "<WhiteDomains {}>".format(self.domen)

