from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import uuid
from werkzeug.security import generate_password_hash, check_password_hash # 1. 追加
import uuid

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    memos = db.relationship('Memo', backref='author', lazy=True)

    # 2. パスワードをハッシュ化して保存するためのメソッド（新規登録用）
    def set_password(self, password):
        self.password = generate_password_hash(password)

    # 3. パスワードを照合するためのメソッド（ログイン用：今回のエラー箇所）
    def check_password(self, password):
        return check_password_hash(self.password, password)

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

