from flask import Flask, render_template, request, redirect, url_for
from app.models import db, Memo, User
from dotenv import load_dotenv
import os
from uuid import UUID
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

# .envファイルを読み込む
load_dotenv()

# 環境変数からデータベース接続情報を取得
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_PORT = os.getenv('POSTGRES_PORT')

app = Flask(__name__)

# SQLAlchemy設定
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key' # セッション暗号化用

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # 未ログイン時に飛ばす先

@app.before_request
def create_tables():
    db.create_all()

# メモ一覧（ログインユーザーのものだけ表示）
@app.route('/')
@login_required
def index():
    # current_user.memos でその人のメモだけ取得できる
    memos = Memo.query.filter_by(user_id=current_user.id).order_by(Memo.created_at.desc()).all()
    return render_template('index.html', memos=memos)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# 新規ユーザー登録
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 簡易的な重複チェック
        if User.query.filter_by(username=username).first():
            return "このユーザー名は既に使われています"

        # 本来は generate_password_hash を使うべきですが、まずはシンプルに保存
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    
    return render_template('register.html')

# メモの詳細を表示
@app.route('/memo/<uuid:memo_id>')
def view_memo(memo_id):
    memo = Memo.query.get_or_404(str(memo_id))
    return render_template('view_memo.html', memo=memo)

# 新しいメモの作成フォームを表示
@app.route('/create', methods=['GET'])
def show_create_memo():
    return render_template('create_memo.html')

# メモ作成時にユーザーIDを保存
@app.route('/create', methods=['POST'])
@login_required
def create_memo():
    title = request.form['title']
    content = request.form['content']
    new_memo = Memo(title=title, content=content, user_id=current_user.id) # IDをセット
    db.session.add(new_memo)
    db.session.commit()
    return redirect(url_for('index'))

# ログイン処理
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.password == password: # 簡易的なパスワードチェック
            login_user(user)
            return redirect(url_for('index'))
        
        return "ログインに失敗しました"
    
    return render_template('login.html') # login.htmlを別途作成

# ログアウト
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# haneisareteru???

# メモを削除
# ===============================
# エンドポイント /memo/(メモのID)/delete
# メソッド　　POST
# 返すもの　index.html (リダイレクト)
# ===============================
@app.route('/memo/<uuid:memo_id>/delete', methods=['POST'])
def delete_memo(memo_id):
    memo = Memo.query.get_or_404(str(memo_id))
    db.session.delete(memo)
    db.session.commit()
    return redirect(url_for('index'))

# 編集フォームを表示 (GET)
@app.route('/memo/<uuid:memo_id>/edit', methods=['GET'])
def show_edit_memo(memo_id):
    memo = Memo.query.get_or_404(str(memo_id))
    return render_template('edit_memo.html', memo=memo)

# データを更新 (POST)
@app.route('/memo/<uuid:memo_id>/edit', methods=['POST'])
def update_memo(memo_id):
    memo = Memo.query.get_or_404(str(memo_id))
    
    # フォームから送られた内容で上書き
    memo.title = request.form['title']
    memo.content = request.form['content']
    
    db.session.commit()
    # 更新後は詳細画面に戻る
    return redirect(url_for('view_memo', memo_id=memo.id))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
