import pickle
from typing import Tuple, List, Dict
import sqlite3
from sklearn.metrics.pairwise import cosine_similarity

import numpy as np
from numpy import array


def dump_nearest(puzzle_num: int, word: str, words: List[str], mat: array, k: int = 1000) \
        -> Dict[str, Tuple[str, float]]:
    word_idx = words.index(word)
    sim_idxs, sim_dists = most_similar(mat, word_idx, k + 1)
    words_a = np.array(words)
    sort_args = np.argsort(sim_dists)[::-1]
    words_sorted = words_a[sim_idxs[sort_args]]
    dists_sorted = sim_dists[sort_args]
    result = zip(words_sorted, dists_sorted)
    closeness = dict()
    for idx, (w, d) in enumerate(result):
        closeness[w] = (idx, d)
    closeness[word] = ("정답!", 1)
    with open(f'data/near/{puzzle_num}.dat', 'wb') as f:
        pickle.dump(closeness, f)
    return closeness


def get_nearest(puzzle_num: int, word: str, words: List[str], mat: array) -> Dict[str, Tuple[str, float]]:
    print(f"getting nearest words for {puzzle_num}")
    try:
        with open(f'data/near/{puzzle_num}.dat', 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return dump_nearest(puzzle_num, word, words, mat)
