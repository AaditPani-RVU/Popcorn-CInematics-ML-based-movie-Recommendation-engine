from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
import sqlite3
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

app = Flask(__name__)
app.secret_key = "temporary_key_for_demo"

def db_connection():
    try:
        conn = sqlite3.connect(r"C:\Users\aadip\Downloads\Popcorn_Cinematics\PopcornCinematics\PopcornCinematics\moviess.db")
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None

@app.route('/')
def home():
    return render_template('home.html', movies=[])

@app.route('/movies', methods=['GET'])
def view_movies():
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM movies")
    movies = cursor.fetchall()
    conn.close()

    # Convert the list of tuples into a list of dictionaries for easier rendering
    movie_list = []
    for movie in movies:
        movie_list.append({
            'movie_title': movie[6],
            'director_name': movie[2],
            'duration': movie[1],
            'gross': movie[3],
            'imdb_score': movie[19],
            'genres': movie[4],
            'title_year': movie[17]
        })

    return render_template('movies.html', movies=movie_list)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = db_connection()
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            flash("Registered successfully!")
            return redirect(url_for('login'))
        flash("Database connection failed.")
        return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = db_connection()
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            conn.close()

            if user is None or password != user[0]:
                flash("Invalid credentials")
                return redirect(url_for('login'))
                
            session['username'] = username
            return redirect(url_for('home'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("Logged out successfully!")
    return redirect(url_for('login'))

@app.route('/add_movie', methods=['POST'])
@app.route('/add_movie', methods=['POST'])
@app.route('/add_movie', methods=['POST'])
def add_movie():
    movie_data = (
        request.form['movie_title'],
        request.form['director_name'],
        request.form['duration'],
        request.form['gross'],
        request.form['title_year'],
        request.form['imdb_score'],
        request.form['genres']
    )

    conn = db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO movies (movie_title, director_name, duration, gross,
                                 title_year, imdb_score, genres) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, movie_data)
        conn.commit()
    except sqlite3.Error as e:
        flash(f"Database error: {e}")
        conn.rollback()  # Rollback if there is an error
    finally:
        conn.close()  # Ensure the connection is always closed
    
    flash("Movie added successfully!")
    return redirect(url_for('home'))
@app.route('/search_movies', methods=['GET', 'POST'])
def search_movies():
    query = request.form.get('search_query')
    conn = db_connection()
    cursor = conn.cursor()

    if query:
        cursor.execute("SELECT * FROM movies WHERE movie_title LIKE ? OR genres LIKE ?", ('%' + query + '%', '%' + query + '%'))
    else:
        cursor.execute("SELECT * FROM movies")  # If no query, show all movies.

    movies = cursor.fetchall()
    conn.close()

    # Convert the list of tuples into a list of dictionaries for easier rendering
    movie_list = []
    for movie in movies:
        movie_list.append({
            'movie_title': movie[6],
            'director_name': movie[2],
            'duration': movie[1],
            'gross': movie[3],
            'imdb_score': movie[19],
            'genres': movie[4],
            'title_year': movie[17],
              
        })

    return render_template('movies.html', movies=movie_list)
@app.route('/update_movie/<int:movie_id>', methods=['GET', 'POST'])
def update_movie(movie_id):
    conn = db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        movie_title = request.form['movie_title']
        director_name = request.form['director_name']
        duration = request.form['duration']
        gross = request.form['gross']
        title_year = request.form['title_year']
        imdb_score = request.form['imdb_score']
        genres = request.form['genres']

        cursor.execute("""
            UPDATE movies
            SET  director_name = ?, duration = ?, gross = ?, title_year = ?, imdb_score = ?, genres = ?
            WHERE movie_title= ?
        """, (director_name, duration, gross, title_year, imdb_score, genres,movie_title))
        conn.commit()
        conn.close()

        flash("Movie updated successfully!")
        return redirect(url_for('view_movies'))

    cursor.execute("SELECT * FROM movies WHERE movie_title = ?", (movie_title,))
    movie = cursor.fetchone()
    conn.close()

   
    return render_template('movies.html', movie=movie)





@app.route('/filter_by_genre', methods=['POST'])
def filter_by_genre():
    genres = request.form.get('genres')
    
    if genres is None:
        flash("No genre selected.")
        return redirect(url_for('home'))

    if movies_df.empty:
        flash("No movies data available.")
        return redirect(url_for('home'))

    matched_movies = movies_df[movies_df['genres'].fillna('').str.contains(genres, na=False)]
    title = matched_movies.iloc[0]['movie_title'] if not matched_movies.empty else None
    recommended_movies = get_recommendations(title) if title else []
    
    if not recommended_movies:
        flash("No movies found for genre.")
    
    return render_template('home.html', movies=recommended_movies)

def load_movies():
    conn = db_connection()
    df = pd.read_sql_query("SELECT movie_title, genres FROM movies", conn)
    conn.close()
    if df.empty:
        print("The DataFrame is empty.")
        return df, None
    
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(df['genres'].fillna(''))
    cosine_sim_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)
    print("Loaded movies:", df)
    return df, cosine_sim_matrix

movies_df, cosine_sim_matrix = load_movies()

def get_recommendations(title):
    if title not in movies_df['movie_title'].values:
        print(f"Movie '{title}' not found in the DataFrame.")
        return []

    idx = movies_df.index[movies_df['movie_title'] == title][0]
    sim_scores = sorted(enumerate(cosine_sim_matrix[idx]), key=lambda x: x[1], reverse=True)
    sim_movie_indices = [i[0] for i in sim_scores[1:6]]
    return movies_df['movie_title'].iloc[sim_movie_indices].tolist()

if __name__ == '__main__':
    app.run(debug=True)
