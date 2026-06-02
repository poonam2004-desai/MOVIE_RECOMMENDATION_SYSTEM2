
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
        for i in json.loads(text):
            L.append(i['name'])
    except (json.JSONDecodeError, TypeError):
        pass
    return L

movies['genres'] = movies['genres'].apply(convert)
movies['keywords'] = movies['keywords'].apply(convert)

def convert_cast(text):
    L = []
    counter = 0
    try:
        for i in json.loads(text):
            if counter < 3:
                L.append(i['name'])
                counter += 1
            else:
                break
    except (json.JSONDecodeError, TypeError):
        pass
    return L

movies['cast'] = movies['cast'].apply(convert_cast)

def fetch_director(text):
    L = []
    try:
        for i in json.loads(text):
            if i['job'] == 'Director':
                L.append(i['name'])
                break
    except (json.JSONDecodeError, TypeError):
        pass
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

pickle.dump(new_df, open('movies.pkl','wb'))
pickle.dump(similarity, open('similarity.pkl','wb'))

print("Files saved successfully ✅")