import os
import requests
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

# Import custom helpers (functions such as login_required, apology, etc.)
from helper import login_required, apology, fetch_info, fetch_media, search_media, fetch_popular, fetch_top_rated

# Configure application
app = Flask(__name__)

# Set up the database connection using SQLite
db = SQL("sqlite:///imdb.db")

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# TMDB API Key
TMDB_API_KEY = '467129e714b8545fa30895f786855903'

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route('/')
@login_required
def homepage():
    """Homepage: Fetch and display popular media"""
    try:
        # Fetch movies and TV shows from the helper function
        media = fetch_media()

        # If no session exists, create one to store media list
        if 'media_list' not in session:
            session['media_list'] = media

        return render_template('index.html', media=session['media_list'])
    except Exception as e:
        # Handle unexpected errors and show an apology page
        return apology("Unable to load homepage", 500)

@app.route("/mylist/tv")
@login_required
def my_list_tv():
    """Display the user's TV shows list"""
    try:
        user_id = session.get("user_id")

        # Fetch user's TV shows from the database
        tv_shows = db.execute("SELECT tv_id, status, score, episodes FROM user_tv_list WHERE user_id = ?", user_id)

        # Get additional information about each TV show from TMDB
        tv_list = []
        for tv in tv_shows:
            tv_info = fetch_info("tv", tv["tv_id"])
            if tv_info:
                tv_info["status"] = tv["status"]
                tv_info["rating"] = tv["score"]
                tv_info["episodes"] = tv["episodes"]
                tv_list.append(tv_info)

        return render_template("my_list_tv.html", tv_shows=tv_list)
    except Exception as e:
        return apology("Error loading your TV list", 500)

@app.route("/mylist/movie")
@login_required
def my_list_movie():
    """Display the user's movie list"""
    try:
        user_id = session.get("user_id")

        # Fetch user's movies from the database
        movies = db.execute("SELECT movie_id, status, score FROM user_movie_list WHERE user_id = ?", user_id)

        # Get additional information about each movie from TMDB
        movie_list = []
        for movie in movies:
            movie_info = fetch_info("movie", movie["movie_id"])
            if movie_info:
                movie_info["status"] = movie["status"]
                movie_info["rating"] = movie["score"]
                movie_list.append(movie_info)

        return render_template("my_list_movie.html", movies=movie_list)
    except Exception as e:
        return apology("Error loading your movie list", 500)

@app.route("/top-rated")
@login_required
def top_rated():
    """Display top-rated movies and TV shows"""
    try:
        # Fetch top-rated movies and TV shows from the helper functions
        top_movies = fetch_top_rated("movie")
        top_tv_shows = fetch_top_rated("tv")
        return render_template('top_rated.html', top_rated_movies=top_movies, top_rated_tv_shows=top_tv_shows)
    except Exception as e:
        return apology("Unable to load top-rated media", 500)

@app.route("/popular")
def popular():
    """Display popular movies and TV shows"""
    try:
        # Fetch popular movies and TV shows
        popular_movies = fetch_popular("movie")
        popular_tv_shows = fetch_popular("tv")

        # Check if the API calls returned valid data
        if popular_movies is None or popular_tv_shows is None:
            raise Exception("Failed to fetch popular media")

        return render_template("popular.html", popular_movies=popular_movies, popular_tv_shows=popular_tv_shows)
    except Exception as e:
        return apology("Error fetching popular media", 500)

@app.route("/search", methods=['POST'])
@login_required
def search():
    """Search for movies or TV shows"""
    try:
        query = request.form.get('search')
        if query:
            # Fetch search results using the helper function
            results = search_media(query)
            return render_template('results.html', query=query, results=results)
        return render_template('index.html', media=session['media_list'])
    except Exception as e:
        return apology("Error performing search", 500)

@app.route("/api/tv/<int:id>/season/<int:season_number>", methods=['GET'])
def fetch_season_episodes(id, season_number):
    """Fetch episodes of a particular season from TMDB"""
    try:
        url = f'https://api.themoviedb.org/3/tv/{id}/season/{season_number}?api_key={TMDB_API_KEY}'
        response = requests.get(url)

        # Check if the request was successful
        if response.status_code == 200:
            return response.json()
        else:
            return {}, 404
    except Exception as e:
        return {}, 500

@app.route("/movie/<int:id>", methods=["GET", "POST"])
@login_required
def movie(id):
    """Display movie details and allow the user to add it to their list"""
    try:
        # Fetch movie details from TMDB
        media = fetch_info("movie", id)
        if not media:
            return apology("Movie not found", 404)

        movie_id = media['id']
        user_id = session.get("user_id")

        # Check if the movie is already in the user's list
        user_list = db.execute("SELECT * FROM user_movie_list WHERE user_id = ? AND movie_id = ?", user_id, movie_id)

        if request.method == "POST":
            # Get the form inputs for rating and status
            rating = int(request.form.get("rating"))
            status = request.form.get("status")

            # Validate form inputs
            if not status:
                return apology("Status is required", 400)
            if rating < 1 or rating > 10:
                return apology("Invalid rating: must be between 1 and 10", 400)

            # Insert or update the user's movie list
            if not user_list:
                db.execute("INSERT INTO user_movie_list (user_id, status, score, movie_id) VALUES (?, ?, ?, ?)", user_id, status, rating, movie_id)
            else:
                db.execute("UPDATE user_movie_list SET status = ?, score = ? WHERE user_id = ? AND movie_id = ?", status, rating, user_id, movie_id)

            return redirect("/mylist/movie")

        return render_template("movie_infopage.html", media=media, list=user_list)
    except ValueError:
        return apology("Invalid input: rating must be an integer", 400)
    except Exception as e:
        return apology("An unexpected error occurred", 500)

@app.route("/remove/<type>/<int:id>", methods=["POST"])
@login_required
def remove(type, id):
    """Remove a movie or TV show from the user's list"""
    try:
        user_id = session.get("user_id")

        if type == 'movie':
            db.execute("DELETE FROM user_movie_list WHERE user_id = ? AND movie_id = ?", user_id, id)
            return redirect("/mylist/movie")
        elif type == 'tv':
            db.execute("DELETE FROM user_tv_list WHERE user_id = ? AND tv_id = ?", user_id, id)
            return redirect("/mylist/tv")
    except Exception as e:
        return apology("An error occurred while removing the item", 500)

@app.route("/tv/<int:id>", methods=["GET", "POST"])
@login_required
def tv_show(id):
    """Display TV show details and allow the user to add it to their list"""
    try:
        user_id = session.get("user_id")
        media = fetch_info("tv", id)

        if not media:
            return apology("TV show not found", 404)

        tv_id = media['id']
        seasons = media['seasons']

        user_list = db.execute("SELECT * FROM user_tv_list WHERE user_id = ? AND tv_id = ?", user_id, tv_id)

        if request.method == "POST":
            # Get form inputs
            episode = int(request.form.get("episode"))
            season_number = int(request.form.get("season_number"))
            rating = int(request.form.get("rating"))
            status = request.form.get("status")

            # Validate inputs
            if rating < 1 or rating > 10:
                return apology("Rating must be between 1 and 10", 400)
            if season_number <= 0 or season_number > len(seasons):
                return apology("Invalid season selected", 400)

            selected_season = next((season for season in seasons if season['season_number'] == season_number), None)
            if not selected_season or episode <= 0 or episode > selected_season['episode_count']:
                return apology("Invalid episode number for the selected season", 400)

            valid_status = ["watching", "completed", "on-hold", "dropped", "plan-to-watch"]
            if status not in valid_status:
                return apology("Invalid status", 400)

            # Insert or update the user's TV show list
            if not user_list:
                db.execute("INSERT INTO user_tv_list (user_id, status, score, episodes, season, tv_id) VALUES (?, ?, ?, ?, ?, ?)",
                           user_id, status, rating, episode, season_number, tv_id)
            else:
                db.execute("UPDATE user_tv_list SET status = ?, score = ?, episodes = ?, season = ? WHERE user_id = ? AND tv_id = ?",
                           status, rating, episode, season_number, user_id, tv_id)

            return redirect("/mylist/tv")

        return render_template("tv_infopage.html", media=media, seasons=seasons, list=user_list)
    except ValueError:
        return apology("Invalid input", 400)
    except Exception as e:
        return apology("An unexpected error occurred", 500)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Validate input
        if not username or not password:
            return apology("must provide username and password", 403)

        # Query the database for the user
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Check username and password
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return apology("invalid username and/or password", 403)

        # Remember the user
        session["user_id"] = rows[0]["id"]
        return redirect("/")

    return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""
    session.clear()
    return redirect("/login")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    """Sign up a new user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Validate form input
        if not username:
            return apology("must provide username", 400)
        if not password or not confirmation:
            return apology("must provide password", 400)
        if password != confirmation:
            return apology("passwords don't match", 400)

        try:
            # Hash the password and insert the user into the database
            hashed_password = generate_password_hash(password)
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hashed_password)

            # Log the user in by storing their user ID in the session
            user_id = db.execute("SELECT id FROM users WHERE username = ?", username)[0]["id"]
            session["user_id"] = user_id

            return redirect("/")
        except Exception as e:
            return apology("Username already taken", 400)

    return render_template("signup.html")

if __name__ == '__main__':
    app.run(debug=True)
