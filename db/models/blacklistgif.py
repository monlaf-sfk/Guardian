from sqlalchemy import Column, Integer, String

from db.models import BASE


class BlackListGif(BASE):
    __tablename__ = "blacklist_gifs"
    gif_id: str = Column(String, primary_key=True)
    chat_id: int = Column(Integer)

    def __init__(self, chat_id, gif_id):
        self.chat_id: int = chat_id
        self.gif_id: int = gif_id
    def __repr__(self):
        return "<BlackListGif {}>".format(self.gif_id)

