import os
import requests
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helper import login_required,apology,fetch_info,fetch_media,search_media,fetch_popular,fetch_top_rated

# Configure application
app = Flask(__name__)
db = SQL("sqlite:///imdb.db")
# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

TMDB_API_KEY = '467129e714b8545fa30895f786855903'


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
@app.route("/page/<int:page>")
@login_required
def index(page=1):
    # Fetch movies and TV shows
    media = fetch_media()

    # Define the number of items per page
    items_per_page = 8
    total_items = len(media)
    total_pages = (total_items // items_per_page) + (1 if total_items % items_per_page else 0)

    # Paginate the media
    start = (page - 1) * items_per_page
    end = start + items_per_page
    paginated_media = media[start:end]

    return render_template('index.html', media=paginated_media, page=page, total_pages=total_pages)

@app.route("/mylist")
@login_required
def my_list():
    user_id = session.get("user_id")

    # Fetch user's movies and TV shows from the database
    movies = db.execute("SELECT movie_id, status, score FROM user_movie_list WHERE user_id = ?", user_id)
    tv_shows = db.execute("SELECT tv_id, status, score, episodes FROM user_tv_list WHERE user_id = ?", user_id)

    # Get additional information about each movie or TV show from TMDB
    movie_list = []
    tv_list = []

    for movie in movies:
        movie_info = fetch_info("movie", movie["movie_id"])
        if movie_info:
            movie_info["status"] = movie["status"]
            movie_info["rating"] = movie["score"]
            movie_list.append(movie_info)

    for tv in tv_shows:
        tv_info = fetch_info("tv", tv["tv_id"])
        if tv_info:
            tv_info["status"] = tv["status"]
            tv_info["rating"] = tv["score"]
            tv_info["episodes"] = tv["episodes"]
            tv_list.append(tv_info)

    return render_template("my_list.html", movies=movie_list, tv_shows=tv_list)

@app.route("/top-rated")
@login_required
def top_rated():
    # Fetch top-rated movies and TV shows
    top_movies = fetch_top_rated("movie")
    top_tv_shows = fetch_top_rated("tv")

    return render_template('top_rated.html', top_rated_movies=top_movies, top_rated_tv_shows=top_tv_shows)


@app.route("/popular")
def popular():
    # Fetch popular movies and TV shows
    popular_movies = fetch_popular("movie")
    popular_tv_shows = fetch_popular("tv")

    # Check if there was an error fetching movies or TV shows
    if popular_movies is None:
        return apology("Error fetching popular movies",400)

    if popular_tv_shows is None:
        return apology("Error fetching popular TV shows",400)

    return render_template("popular.html", popular_movies=popular_movies, popular_tv_shows=popular_tv_shows)

@app.route("/search", methods=['POST'])
@login_required
def search():
    media = session['media_list']
    query = request.form.get('search')
    if query:
        results = search_media(query)
        return render_template('results.html', query=query, results=results)
    return render_template('index.html', media=media)

@app.route("/api/tv/<int:id>/season/<int:season_number>", methods=['GET'])
def fetch_season_episodes(id, season_number):

    url = f'https://api.themoviedb.org/3/tv/{id}/season/{season_number}?api_key={TMDB_API_KEY}'
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    return {}, 404


@app.route("/page/movie/<int:id>", methods=["GET", "POST"])
@app.route("/movie/<int:id>", methods=["GET", "POST"])
@login_required
def movie(id):

    # Get the user ID from the session
    user_id = session.get("user_id")

    # Fetch movie details using a custom fetch_info function
    media = fetch_info("movie", id)

    # Error handling if the movie is not found
    if not media:
        return apology("Movie not found", 404)

    movie_id = media['id']

    # Check if the movie is already in the user's list
    user_list = db.execute("SELECT * FROM user_movie_list WHERE user_id = ? AND movie_id = ?", user_id, movie_id)


    if request.method == "POST":
        try:
            # Get form input for rating and status
            rating = int(request.form.get("rating"))
            status = request.form.get("status")

            # Check if status is present
            if not status:
                return apology("Status is required", 400)

            # Validate rating (must be an integer between 1 and 10)
            if not rating or rating < 1 or rating > 10:
                return apology("Invalid rating: rating must be between 1 and 10", 400)

            # Check if the movie is already in the user's list
            user_list = db.execute("SELECT * FROM user_movie_list WHERE user_id = ? AND movie_id = ?", user_id, movie_id)

            # If the movie is not in the list, insert a new record
            if not user_list:
                db.execute("INSERT INTO user_movie_list (user_id, status, score, movie_id) VALUES (?, ?, ?, ?)", user_id, status, rating, movie_id)
                return redirect("/mylist")

            # If the movie is already in the list, update the existing record
            else:
                db.execute("UPDATE user_movie_list SET status = ?, score = ? WHERE user_id = ? AND movie_id = ?", status, rating, user_id, movie_id)
                return redirect("/mylist")

        except ValueError:
            # Handle case where the rating is not a valid integer
            return apology("Invalid input: rating must be an integer", 400)

        except Exception as e:
            # Generic error handling for unexpected issues (e.g., database errors)
            print(f"Error occurred: {e}")
            return apology("An unexpected error occurred", 500)

    # Render the movie information page if it's a GET request
    return render_template("movie_infopage.html", media=media, list=user_list)


@app.route("/remove/<type>/<int:id>", methods=["POST"])
@login_required
def remove(type,id):

    user_id = session.get("user_id")

    if request.method == "POST":

        if type == 'movie':
            db.execute("DELETE FROM user_movie_list WHERE user_id = ? AND movie_id = ?", user_id , id)
            return redirect("/mylist")
        elif type == 'tv':
            db.execute("DELETE FROM user_tv_list WHERE user_id = ? AND tv_id = ?", user_id , id)
            return redirect("/mylist")

@app.route("/page/tv/<int:id>", methods=["GET", "POST"])
@app.route("/tv/<int:id>", methods=["GET", "POST"])
@login_required
def tv_show(id):
    user_id = session.get("user_id")

    # Fetch detailed info about the TV show, including seasons
    media = fetch_info("tv", id)

    # Error handling: Check if media exists
    if not media:
        return apology("TV show not found", 404)

    tv_id = media['id']
    seasons = media['seasons']

    # Check if the user has already added this TV show
    user_list = db.execute("SELECT * FROM user_tv_list WHERE user_id = ? AND tv_id = ?", user_id, tv_id)

    # Error handling: Check if seasons exist in the media
    if not seasons:
        return apology("No seasons found for this TV show", 404)

    if request.method == "POST":
        # Error handling: Validate form inputs
        try:
            episode = int(request.form.get("episode"))
            season_number = int(request.form.get("season_number"))
            rating = int(request.form.get("rating"))
            status = request.form.get("status")
        except ValueError:
            return apology("Invalid input", 400)

        # Error handling: Check for valid rating
        if rating < 1 or rating > 10:
            return apology("Rating must be between 1 and 10", 400)

        # Error handling: Ensure episode and season selection is valid
        if season_number <= 0 or season_number > len(seasons):
            return apology("Invalid season selected", 400)

        selected_season = next((season for season in seasons if season['season_number'] == season_number), None)
        if not selected_season or episode <= 0 or episode > selected_season['episode_count']:
            return apology("Invalid episode number for the selected season", 400)

        # Error handling: Check if status is valid
        valid_status = ["watching", "completed", "on-hold", "dropped", "plan-to-watch"]
        if status not in valid_status:
            return apology("Invalid status", 400)

        # Insert new user data for this TV show if not in the database
        if not user_list:
            db.execute("INSERT INTO user_tv_list (user_id, status, score, episodes, season, tv_id) VALUES (?, ?, ?, ?, ?, ?)",
                       user_id, status, rating, episode, season_number, tv_id)
            return redirect("/mylist")

        # Update existing record for the TV show
        db.execute("UPDATE user_tv_list SET status = ?, score = ?, episodes = ?, season = ? WHERE user_id = ? AND tv_id = ?",
                   status, rating, episode, season_number, user_id, tv_id)
        return redirect("/mylist")

    return render_template("tv_infopage.html", media=media, seasons=seasons, list=user_list)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    session.clear()  # Forget any user_id

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Validate form inputs
        if not username or not password:
            return apology("must provide username and password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Check username and password
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return apology("invalid username and/or password", 403)

        # Remember user
        session["user_id"] = rows[0]["id"]
        return redirect("/")

    return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")

@app.route("/signup", methods=["GET","POST"])
def signup():
    """Sign Up"""

    # User reached route via POST
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

        # Attempt to insert the new user into the database
        try:
            hashed_password = generate_password_hash(password)
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hashed_password)
            user_id = db.execute("SELECT id FROM users WHERE username = ?", username)[0]["id"]
            session["user_id"] = user_id
            return redirect("/")

        except ValueError:
            return apology("username taken", 400)

    return render_template("signup.html")

if __name__ == '__main__':
    app.run(debug=True)
