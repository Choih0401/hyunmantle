from sentence_transformers import SentenceTransformer
import pickle
import sqlite3
from typing import Set
import unicodedata
import re
from tqdm import tqdm
import numpy as np
from numpy import array
from sklearn.metrics.pairwise import cosine_similarity  # Add this import

def is_hangul(text) -> bool:
    return bool(re.match(r'^[\u3130-\u318F\uAC00-\uD7A3]+$', text))

def load_dic(path: str) -> Set[str]:
    rtn = set()
    with open(path, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            word = line.strip()
            word = unicodedata.normalize('NFC', word)
            if is_hangul(word):
               rtn.add(word)
    return rtn

def blocks(files, size=65536):
    while True:
        b = files.read(size)
        if not b: break
        yield b

def count_lines(filepath):
    with open(filepath, "r", encoding="utf-8", errors='ignore') as f:
        return sum(bl.count("\n") for bl in tqdm(blocks(f), desc='Counting lines', mininterval=1))

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
        sim = float(cosine_similarity(secret_vec.reshape(1, -1), vec.reshape(1, -1))[0][0])  # Update cosine similarity usage
        if word != secret_word:
            scores.append((word, sim))
    top_k = sorted(scores, key=lambda x: x[1], reverse=True)[:k]
    return {w: (i, s) for i, (w, s) in enumerate(top_k)}

model = SentenceTransformer("jhgan/ko-sroberta-multitask")

# 단어 리스트 불러오기 (기존 코드 활용)
normal_words = load_dic('data/ko-aff-dic-0.7.92/ko_filtered.txt')

connection = sqlite3.connect('data/valid_guesses.db')
cursor = connection.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS guesses (word text PRIMARY KEY, vec blob)")

valid_nearest = []
valid_nearest_mat = []

for word in tqdm(normal_words, desc="Embedding with SBERT"):
    vec = model.encode(word)
    cursor.execute("INSERT OR REPLACE INTO guesses VALUES (?, ?)", (word, pickle.dumps(vec)))
    valid_nearest.append(word)
    valid_nearest_mat.append(vec)

connection.commit()
connection.close()