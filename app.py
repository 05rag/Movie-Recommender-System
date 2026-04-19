import streamlit as st
import pickle
import pandas as pd
import requests
import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import gdown
load_dotenv()
API_KEY = os.getenv('TMDB_API_KEY')

st.set_page_config(layout="wide")
st.title("Movie Recommender System")

def download_file(url, filename):
    if not os.path.exists(filename):
        print(f"Downloading {filename}...")
        response = requests.get(url)
        with open(filename, 'wb') as f:
            f.write(response.content)

if not os.path.exists("similarity.pkl"):
    gdown.download("https://drive.google.com/uc?export=download&id=1id22zj0qas2briT9awgLO37wqzgvNrg_", "similarity.pkl", quiet=False)

if not os.path.exists("movie_dict.pkl"):
    gdown.download("https://drive.google.com/uc?id=1O5ub24ftIjGTMLA9R51hltQVUA41a8bs", "movie_dict.pkl", quiet=False)

@st.cache_resource
def load_data():
    similarity = pickle.load(open('similarity.pkl', 'rb'))
    movie_dict = pickle.load(open('movie_dict.pkl', 'rb'))
    return similarity, movie_dict

similarity, movie_dict = load_data()

movies = pd.DataFrame(movie_dict)
movie_to_index = {title: idx for idx, title in enumerate(movies['title'])}

@st.cache_data
def fetch_poster(movie_id):
    try:
        url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US'
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        poster_path = data.get('poster_path')
        if poster_path:
            return "https://image.tmdb.org/t/p/w500/" + poster_path
        return "https://via.placeholder.com/500x750?text=No+Poster"

    except requests.exceptions.RequestException as e:
        # Now we are only catching actual network/request errors
        print(f"Network error: {e}")
        return "https://via.placeholder.com/500x750?text=Error"

def fetch_all_posters(movie_ids):
    # This fires all 5 requests at the exact same time
    with ThreadPoolExecutor() as executor:
        return list(executor.map(fetch_poster, movie_ids))


def recommend(movie, top_n=6):
    movie_index = movie_to_index.get(movie)

    if movie_index is None:
        return [], []

    recommendations = similarity[movie_index]

    movie_ids = []
    recommended_movie_list = []

    for i in recommendations[:top_n]:
        movie_id = int(movies.iloc[i[0]].movie_id)
        movie_ids.append(movie_id)
        recommended_movie_list.append(movies.iloc[i[0]].title)

    recommended_movie_posters = fetch_all_posters(movie_ids)

    return recommended_movie_list, recommended_movie_posters


option = st.selectbox('Select a movie to get recommendations.', movies['title'].values)

if st.button('Recommend'):
    names, posters = recommend(option)

    with st.container():
        cols = st.columns(5)
        for i in range(5):
            with cols[i]:
                # 2. Use a container for the individual card
                with st.container(border=True):
                    st.image(posters[i], use_container_width=True)
                    st.caption(names[i])