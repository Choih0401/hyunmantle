# 🧩 Hyunmantle (현맨틀)

🧩 Hyunmantle — A Flask-based Korean *Semantle* clone that picks a daily secret word and scores guesses by semantic similarity using Word2Vec/embeddings. Packaged with Docker, auto-rotates the puzzle, and serves a simple web UI.

> ✅ Docker images are **auto-built & published** to Docker Hub via GitHub Actions:  
> **https://hub.docker.com/r/choih0401/hyunmantle**

---

## 🚀 Quick Start (Docker Hub image)

```bash
# Pull the latest image (auto-published by GitHub Actions)
docker pull choih0401/hyunmantle:latest

# (Recommended) Run with a host-mounted data directory
# - Mount ./data on host to /app/data in container (to keep dictionary/model/DB persistent)
docker run -d --name hyunmantle -p 8899:80 \ 
  -v $(pwd)/data:/app/data \ 
  choih0401/hyunmantle:latest

# Open http://localhost:8899
```

> If you run without the volume mount, any prepared data (dictionary, vectors, DB) created inside the container will be ephemeral.

---

## 📦 Data Preparation

This project needs a **Korean dictionary** and a **Word2Vec model** to compute similarity.  
With the container running (or by launching an ephemeral container), run the helper scripts **inside** the container.

### 1) Dictionary (Hunspell ko)
```bash
# Prepare host data dir if you mounted it
mkdir -p ./data

# Download Korean hunspell dictionary into host ./data (or exec into container and use /app/data)
cd data
wget https://github.com/spellcheck-ko/hunspell-dict-ko/releases/download/0.7.92/ko-aff-dic-0.7.92.zip
unzip ko-aff-dic-0.7.92.zip
cd ..
```

### 2) Filter words → DB
```bash
# Run filter in the running container
docker exec -it hyunmantle python /app/filter_words.py

# (Alternatively) one-off container
docker run --rm -it -v $(pwd)/data:/app/data --entrypoint python choih0401/hyunmantle:latest /app/filter_words.py
```

### 3) Word2Vec model → DB
Place your model as `./data/namu.model` on host (or `/app/data/namu.model` in container), then:
```bash
docker exec -it hyunmantle python /app/process_vecs.py
# or
docker run --rm -it -v $(pwd)/data:/app/data --entrypoint python choih0401/hyunmantle:latest /app/process_vecs.py
```

### 4) (Optional) Pre-compute neighbors
```bash
docker exec -it hyunmantle python /app/process_similar.py
```

> The app expects `data/namu.model` (Gensim Word2Vec). Replace with your own model or adjust the path in `process_vecs.py` if needed.

---

## 🛠️ Tech Stack

- **Flask** + **Gunicorn** — Web server
- **APScheduler** — Daily puzzle rotation (cron)
- **Gensim Word2Vec / Sentence-Transformers** — Embeddings & similarity
- **SQLite** — Compact storage for words & vectors
- **Docker** — Containerized runtime
- **GitHub Actions** — CI that builds & publishes the Docker image

---

## 🧩 How It Works

- A **daily secret word** is selected and stored.
- Each guess is scored by **cosine similarity** to the secret word vector.
- The UI shows closeness/rankings and provides reveal/Top-K pages.

Main scripts:
- `filter_words.py` — cleans/filters the word list
- `process_vecs.py` — loads Word2Vec and stores vectors into SQLite
- `process_similar.py` — (optional) precomputes nearest neighbors
- `semantle.py` — Flask app (routes, game logic)

---

## 🐳 Docker Compose (optional)

Create `docker-compose.yml`:

```yaml
services:
  app:
    image: choih0401/hyunmantle:latest
    container_name: hyunmantle
    restart: unless-stopped
    ports:
      - "8899:80"
    volumes:
      - ./data:/app/data
```

Then:

```bash
docker compose up -d
# prepare data (see steps above)
docker exec -it hyunmantle python /app/filter_words.py
docker exec -it hyunmantle python /app/process_vecs.py
```

---

## 🔗 Links

- **Docker Hub**: https://hub.docker.com/r/choih0401/hyunmantle
- **GitHub**: https://github.com/Choih0401/hyunmantle

---

## 📜 License

See [LICENSE.txt](https://github.com/Choih0401/hyunmantle/blob/master/LICENSE.txt).
