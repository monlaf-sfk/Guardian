from sqlalchemy import Column, Integer, String

from db.models import BASE


class BlackListStickers(BASE):
    __tablename__ = "blacklist_stickers"
    sticker_id: int = Column(String, primary_key=True)
    chat_id: int = Column(Integer)


    def __init__(self, chat_id, sticker_id):
        self.chat_id: int = chat_id
        self.sticker_id: int = sticker_id

    def __repr__(self):
        return "<BlackListStickers {}>".format(self.sticker_id)

