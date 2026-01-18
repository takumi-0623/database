from flask import Flask, render_template, request, redirect, url_for
from app.models import db, Memo, User
from dotenv import load_dotenv
import os
from uuid import UUID
from datetime import datetime
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask import Flask, render_template, request, redirect, url_for, flash

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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# メモ一覧（ログインユーザーのものだけ表示）
@app.route('/')
@login_required
def index():
    # URLからソート順を取得（デフォルトは作成日の降順）
    sort_key = request.args.get('sort', 'created_at')
    # デフォルトは「未提出」を表示するように設定
    view_status = request.args.get('view_status', '未提出')
    
    # クエリの基本形
    query = Memo.query.filter_by(user_id=current_user.id, status=view_status)
    
    # ソート条件の分岐
    if sort_key == 'title':
        memos = query.order_by(Memo.title.asc()).all()
    elif sort_key == 'deadline':
        # 締切日は「設定されているものを優先的に、近い順」で並べる
        memos = query.order_by(Memo.deadline.asc().nullslast()).all()
    else:
        # デフォルト：作成日の新しい順
        memos = query.order_by(Memo.created_at.desc()).all()
        
    return render_template('index.html', memos=memos, current_sort=sort_key, current_view=view_status)

# 新規ユーザー登録（登録後そのままログインするように修正）
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 1. 重複チェック
        if User.query.filter_by(username=username).first():
            # ここでエラーを出し、ログイン画面ではなく「登録画面」へ戻す
            flash('このユーザー名は既に使われています。別の名前を入力してください。', 'error')
            return redirect(url_for('register'))

        # 2. 正常な登録処理
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        return redirect(url_for('index'))
    
    return render_template('register.html')

# メモの詳細を表示
@app.route('/memo/<uuid:memo_id>')
@login_required
def view_memo(memo_id):
    memo = Memo.query.get_or_404(str(memo_id))
    return render_template('view_memo.html', memo=memo)

# 新しいメモの作成フォームを表示
@app.route('/create', methods=['GET'])
@login_required
def show_create_memo():
    # ログインユーザーの過去のメモから、タイトルだけを重複なく取得
    past_titles = db.session.query(Memo.title).filter_by(user_id=current_user.id).distinct().all()
    # tupleのリスト [('授業A',), ('授業B',)] を文字列のリスト ['授業A', '授業B'] に変換
    titles = [t[0] for t in past_titles]
    return render_template('create_memo.html', titles=titles)

# メモ作成（インデントを修正）
@app.route('/create', methods=['POST'])
@login_required
def create_memo():
    title = request.form['title']
    content = request.form['content']
    deadline_str = request.form.get('deadline')
    
    deadline = None
    if deadline_str and deadline_str.strip() != '':
        try:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            deadline = None
    
    new_memo = Memo(title=title, content=content, deadline=deadline, user_id=current_user.id, status='未提出')
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

        # 2. Userモデルに追加したcheck_passwordメソッドを呼び出す
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        
        # 3. 失敗した時にメッセージを送ってログイン画面へリダイレクト
        flash('ユーザー名またはパスワードが正しくありません。', 'error')
        return redirect(url_for('login'))
        
    return render_template('login.html')
# ログアウト
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# メモを削除
@app.route('/memo/<uuid:memo_id>/delete', methods=['POST'])
@login_required
def delete_memo(memo_id):
    memo = Memo.query.get_or_404(str(memo_id))
    if memo.user_id != current_user.id:
        return "権限がありません", 403
    db.session.delete(memo)
    db.session.commit()
    return redirect(url_for('index'))

# 編集フォームを表示
@app.route('/memo/<uuid:memo_id>/edit', methods=['GET'])
@login_required
def show_edit_memo(memo_id):
    memo = Memo.query.get_or_404(str(memo_id))
    # 編集画面でも履歴を表示する場合、同様にタイトルを取得
    past_titles = db.session.query(Memo.title).filter_by(user_id=current_user.id).distinct().all()
    titles = [t[0] for t in past_titles]
    
    # 詳細画面ではなく、更新したステータスの一覧画面へ戻る
    return render_template('edit_memo.html', memo=memo, titles=titles)

# データを更新
@app.route('/memo/<uuid:memo_id>/edit', methods=['POST'])
@login_required
def update_memo(memo_id):
    memo = Memo.query.get_or_404(str(memo_id))
    if memo.user_id != current_user.id:
        return "権限がありません", 403
    
    memo.title = request.form['title']
    memo.content = request.form['content']
    
    deadline_str = request.form.get('deadline')
    if deadline_str and deadline_str.strip() != '':
        try:
            memo.deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            pass
    else:
        memo.deadline = None

    # ラジオボタンの値を取得して更新
    memo.status = request.form.get('status')
        
    db.session.commit()
    return redirect(url_for('index', view_status=memo.status))

# 授業名の一覧を表示・追加
@app.route('/titles', methods=['GET', 'POST'])
@login_required
def manage_titles():
    if request.method == 'POST':
        new_title = request.form.get('new_title')
        if new_title:
            # メモの中身は空で、タイトルだけの「型」として保存
            # ※このアプリの設計上、Memoテーブルのtitleを履歴としているため
            # 一つダミーのメモを作るか、専用のSubjectテーブルを作るのが本来は理想です。
            # 現状の構成を維持するなら、空のメモとして保存します。
            dummy_memo = Memo(title=new_title, content="（授業名登録）", user_id=current_user.id)
            db.session.add(dummy_memo)
            db.session.commit()
        return redirect(url_for('manage_titles'))

    # 重複なくタイトルを取得
    titles = db.session.query(Memo.title).filter_by(user_id=current_user.id).distinct().all()
    titles = [t[0] for t in titles]
    return render_template('manage_titles.html', titles=titles)

# 削除処理（前回の続き）
@app.route('/titles/delete', methods=['POST'])
@login_required
def delete_title_group():
    target_title = request.form.get('title')
    # その授業名のメモをすべて削除
    Memo.query.filter_by(user_id=current_user.id, title=target_title).delete()
    db.session.commit()
    return redirect(url_for('manage_titles'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)