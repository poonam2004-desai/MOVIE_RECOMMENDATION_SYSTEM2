# --------------------------
# DEBUG (VERY IMPORTANT)
# --------------------------
import os

print("Current Folder:", os.getcwd())
print("Files in folder:", os.listdir())

# --------------------------
# IMPORT LIBRARIES
# --------------------------
import pandas as pd
import numpy as np
import ast
import json
import requests
import time
import db

# --------------------------
# LOAD DATA
# --------------------------
movies = pd.read_csv('tmdb_5000_movies.csv')
credits = pd.read_csv('tmdb_5000_credits.csv')

movies = movies.merge(credits, on='title')

movies = movies[['movie_id','title','overview','genres','keywords','cast','crew']]
movies.dropna(inplace=True)

# --------------------------
# CONVERT FUNCTIONS
# --------------------------
def convert(text):
    L = []
    try:
        for i in ast.literal_eval(text):
            L.append(i.get('name') if isinstance(i, dict) else str(i))
        return L
    except Exception:
        try:
            for i in json.loads(text):
                L.append(i.get('name') if isinstance(i, dict) else str(i))
            return L
        except Exception:
            return []

movies['genres'] = movies['genres'].apply(convert)
movies['keywords'] = movies['keywords'].apply(convert)

def convert_cast(text):
    L = []
    counter = 0
    try:
        seq = ast.literal_eval(text)
    except Exception:
        try:
            seq = json.loads(text)
        except Exception:
            seq = []
    for i in seq:
        if counter < 3:
            L.append(i.get('name') if isinstance(i, dict) else str(i))
            counter += 1
        else:
            break
    return L

movies['cast'] = movies['cast'].apply(convert_cast)

def fetch_director(text):
    L = []
    try:
        seq = ast.literal_eval(text)
    except Exception:
        try:
            seq = json.loads(text)
        except Exception:
            seq = []
    for i in seq:
        try:
            if i.get('job') == 'Director':
                L.append(i.get('name'))
                break
        except Exception:
            continue
    return L

movies['crew'] = movies['crew'].apply(fetch_director)

# --------------------------
# PREPROCESSING
# --------------------------
movies['overview'] = movies['overview'].apply(lambda x: x.split())

movies['genres'] = movies['genres'].apply(lambda x: [i.replace(" ","") for i in x])
movies['keywords'] = movies['keywords'].apply(lambda x: [i.replace(" ","") for i in x])
movies['cast'] = movies['cast'].apply(lambda x: [i.replace(" ","") for i in x])
movies['crew'] = movies['crew'].apply(lambda x: [i.replace(" ","") for i in x])

movies['tags'] = movies['overview'] + movies['genres'] + movies['keywords'] + movies['cast'] + movies['crew']

new_df = movies[['movie_id','title','tags']].copy()

new_df['tags'] = new_df['tags'].apply(lambda x: " ".join(x))
new_df['tags'] = new_df['tags'].apply(lambda x: x.lower())

# --------------------------
# STEMMING
# --------------------------
from nltk.stem.porter import PorterStemmer

ps = PorterStemmer()

def stem(text):
    return " ".join([ps.stem(word) for word in text.split()])

new_df['tags'] = new_df['tags'].apply(stem)

# --------------------------
# VECTORIZATION
# --------------------------
from sklearn.feature_extraction.text import CountVectorizer

cv = CountVectorizer(max_features=5000, stop_words='english')
vectors = cv.fit_transform(new_df['tags']).toarray()

# --------------------------
# SIMILARITY
# --------------------------
from sklearn.metrics.pairwise import cosine_similarity

similarity = cosine_similarity(vectors)

# --------------------------
# RECOMMENDATION FUNCTION
# --------------------------
def recommend(movie):
    if movie not in new_df['title'].values:
        print("Movie not found!")
        return
    
    index = new_df[new_df['title'] == movie].index[0]
    distances = similarity[index]
    
    movie_list = sorted(list(enumerate(distances)), key=lambda x: x[1], reverse=True)[1:6]
    
    for i in movie_list:
        print(new_df.iloc[i[0]].title)

# --------------------------
# TEST
# --------------------------
recommend('Avatar')

# --------------------------
# SAVE FILES
# --------------------------
import pickle

# Try to populate poster URLs using TMDB API (best-effort, non-blocking)
TMDB_API_KEY = "a71b1374a6f462f48dc76e74d341ffba"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
FETCH_POSTERS = int(os.environ.get('FETCH_POSTERS', '300'))  # limit poster fetch for demo; set env to increase

def fetch_poster_for_row(r):
    mid = r.get('movie_id')
    title = r.get('title')
    try:
        if pd.isna(mid) or mid == '':
            return None
        resp = requests.get(f"https://api.themoviedb.org/3/movie/{int(mid)}?api_key={TMDB_API_KEY}", timeout=6)
        data = resp.json()
        poster = data.get('poster_path')
        if poster:
            return TMDB_IMAGE_BASE + poster
    except Exception:
        return None
    return None


# add poster_url column (optional)

# add poster_url column (optional)
new_df['poster_url'] = None
# only fetch posters for the first N rows to avoid long runs during demos
for idx, row in new_df.head(FETCH_POSTERS).iterrows():
    try:
        poster = fetch_poster_for_row(row)
        if poster:
            new_df.at[idx, 'poster_url'] = poster
        # be gentle to TMDB
        time.sleep(0.08)
    except Exception:
        continue

# Insert into SQLite
inserted = db.insert_movies(new_df)
print(f'Inserted {inserted} movies into SQLite DB')

# save similarity for fast recommendations
pickle.dump(similarity, open('similarity.pkl','wb'))
print("Similarity matrix saved as similarity.pkl ✅")