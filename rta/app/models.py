from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import uuid

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False) # 本来はハッシュ化して保存
    memos = db.relationship('Memo', backref='author', lazy=True)

class Memo(db.Model):
    # この一行を追加することで、二重定義のエラーを回避します
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deadline = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='未提出', nullable=False)
    # ユーザーとの紐付け
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)