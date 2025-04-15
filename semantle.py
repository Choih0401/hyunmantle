import pickle
import sqlite3
from datetime import date, datetime
from sentence_transformers import SentenceTransformer
from numpy.linalg import norm
import numpy as np

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import (
    Flask,
    send_file,
    send_from_directory,
    jsonify,
    render_template
)
from pytz import utc, timezone

KST = timezone('Asia/Seoul')

model = SentenceTransformer("jhgan/ko-sroberta-multitask")

def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (norm(vec1) * norm(vec2))

def precompute_top_k(day: int, secret_word: str, k: int = 1000):
    conn = sqlite3.connect('data/valid_guesses.db')
    cursor = conn.cursor()
    cursor.execute("SELECT word, vec FROM guesses")
    rows = cursor.fetchall()
    conn.close()

    secret_vec = model.encode(secret_word)
    scores = []
    for word, vec_blob in rows:
        vec = pickle.loads(vec_blob)
        sim = float(cosine_similarity(secret_vec, vec))
        if word != secret_word:
            scores.append((word, sim))
    top_k = sorted(scores, key=lambda x: x[1], reverse=True)[:k]
    return {w: (i, s) for i, (w, s) in enumerate(top_k)}

NUM_SECRETS = 4650
FIRST_DAY = date(2025, 4, 14)
scheduler = BackgroundScheduler()
scheduler.start()

app = Flask(__name__)
app.ranks = {}
print("loading valid nearest")
with open('data/secrets.txt', 'r', encoding='utf-8') as f:
    secrets = [l.strip() for l in f.readlines()]
print("initializing nearest words for solutions")
app.secrets = dict()
current_puzzle = (utc.localize(datetime.utcnow()).astimezone(KST).date() - FIRST_DAY).days % NUM_SECRETS
for offset in range(-2, 2):
    puzzle_number = (current_puzzle + offset) % NUM_SECRETS
    secret_word = secrets[puzzle_number]
    app.secrets[puzzle_number] = secret_word
    app.ranks[puzzle_number] = precompute_top_k(puzzle_number, secret_word)

@scheduler.scheduled_job(trigger=CronTrigger(hour=1, minute=0, timezone=KST))
def update_nearest():
    print("scheduled stuff triggered!")
    next_puzzle = ((utc.localize(datetime.utcnow()).astimezone(KST).date() - FIRST_DAY).days + 1) % NUM_SECRETS
    next_word = secrets[next_puzzle]
    to_delete = (next_puzzle - 4) % NUM_SECRETS
    if to_delete in app.secrets:
        del app.secrets[to_delete]
    app.secrets[next_puzzle] = next_word
    app.ranks[next_puzzle] = precompute_top_k(next_puzzle, next_word)

@app.route('/')
def get_index():
    return render_template('index.html')

@app.route('/robots.txt')
def robots():
    return send_file("static/assets/robots.txt")

@app.route("/favicon.ico")
def send_favicon():
    return send_file("static/assets/favicon.ico")

@app.route("/assets/<path:path>")
def send_static(path):
    return send_from_directory("static/assets", path)

@app.route('/guess/<int:day>/<string:word>')
def get_guess(day: int, word: str):
    rtn = {"guess": word}
    if day in app.ranks and word in app.ranks[day]:
        rtn["rank"], rtn["sim"] = app.ranks[day][word]
    else:
        if app.secrets[day] == word:
            word = app.secrets[day]
        # Check if word exists in the DB
        conn = sqlite3.connect('data/valid_guesses.db')
        cur = conn.cursor()
        cur.execute('SELECT vec FROM guesses WHERE word == ?', (word,))
        row = cur.fetchone()
        conn.close()
        try:
            vec1 = model.encode(app.secrets[day])
            vec2 = pickle.loads(row[0])
            rtn["sim"] = float(cosine_similarity(vec1, vec2))
            rtn["rank"] = "1000위 이상"
        except Exception:
            vec1 = model.encode(app.secrets[day])
            vec2 = model.encode(word)
            rtn["sim"] = float(cosine_similarity(vec1, vec2))
            rtn["rank"] = "1000위 이상"
    return jsonify(rtn)

@app.route('/similarity/<int:day>')
def get_similarity(day: int):
    if day not in app.ranks:
        return jsonify({"error": "no data"}), 404

    # 유사도만 뽑아서 정렬
    sims = sorted([sim for _, sim in app.ranks[day].values()], reverse=True)

    return jsonify({
        "top": sims[0],
        "top10": sims[9] if len(sims) > 9 else sims[-1],
        "rest": sims[-1] if sims else 0.0
    })

@app.route('/yesterday/<int:today>')
def get_solution_yesterday(today: int):
    return app.secrets[(today - 1) % NUM_SECRETS]

@app.route('/nearest1k/<int:day>')
def get_nearest_1k(day: int):
    if day not in app.secrets or day not in app.ranks:
        return "이 날의 가장 유사한 단어는 현재 사용할 수 없습니다. 그저께부터 내일까지만 확인할 수 있습니다.", 404
    solution = app.secrets[day]
    nearest_data = app.ranks[day]
    words = [
        dict(
            word=w,
            rank=k[0] + 1,
            similarity="%0.2f" % (k[1] * 100))
        for w, k in sorted(nearest_data.items(), key=lambda item: item[1][0])
    ]
    return render_template('top1k.html', word=solution, words=words, day=day)


@app.route('/giveup/<int:day>')
def give_up(day: int):
    if day not in app.secrets:
        return '저런...', 404
    else:
        return app.secrets[day]
