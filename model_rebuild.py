import pickle

import pandas as pd
from nltk.stem.porter import PorterStemmer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import db


def main() -> None:
    """Rebuild movies.pkl and similarity.pkl from all DB rows."""
    print("Loading all movies from DB...")
    df = pd.DataFrame(db.get_all_movies())
    print(f"Total: {len(df)} movies")

    df = df[df["tags"].notna() & (df["tags"].str.strip() != "")]
    df = df.drop_duplicates(subset="title", keep="first").reset_index(drop=True)
    print(f"After clean: {len(df)} movies")

    ps = PorterStemmer()
    df["tags"] = df["tags"].apply(lambda t: " ".join([ps.stem(w) for w in str(t).split()]))

    cv = CountVectorizer(max_features=10000, stop_words="english")
    vectors = cv.fit_transform(df["tags"]).toarray()

    print("Computing similarity matrix...")
    similarity = cosine_similarity(vectors)

    pickle.dump(df[["movie_id", "title", "tags"]], open("movies.pkl", "wb"))
    pickle.dump(similarity, open("similarity.pkl", "wb"))

    lang_counts = df["language"].value_counts().to_dict() if "language" in df.columns else {}
    print(f"Done! {len(df)} movies | Languages: {lang_counts}")


if __name__ == "__main__":
    main()