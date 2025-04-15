### Setup

Download Word2Vec and dictionary data:
```bash
cd data
wget https://github.com/spellcheck-ko/hunspell-dict-ko/releases/download/0.7.92/ko-aff-dic-0.7.92.zip
unzip ko-aff-dic-0.7.92.zip
```

Filter and save word2vec in DB
```bash
docker-compose run --rm --entrypoint python app filter_words.py
docker-compose run --rm --entrypoint python app process_vecs.py
```

(Optional) Regenerate secrets
```bash
docker-compose run --rm --entrypoint python app generate_secrets.py
```

Start server
```bash
docker-compose up
```