import uuid
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Memo(db.Model):
    # この一行を追加することで、二重定義のエラーを回避します
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deadline = db.Column(db.DateTime, nullable=True)
