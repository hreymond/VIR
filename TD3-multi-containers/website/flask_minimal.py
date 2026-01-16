from flask import Flask
from flask import request
import os
import urllib.request, urllib.error, json
import psycopg2

app = Flask(__name__)

app.logger.info("Connecting to postgres database")

conn : psycopg2.connection = None


def get_db_connection() -> psycopg2.connection:
    global conn

    conn = psycopg2.connect(host="postgres",
                        database="postgres",
                        user="postgres",
                        password="admin")
    
    with conn.cursor() as cur:
        # Create table stats if it does not exist
        cur.execute('CREATE TABLE IF NOT EXISTS stats (id serial PRIMARY KEY,'
                                        'username varchar (150) NOT NULL,'
                                        'nb_query integer  NOT NULL)'
                                        )
        cur.execute("ALTER TABLE stats ADD CONSTRAINT stats_username_unique UNIQUE (username);")
        cur.close()
    conn.commit()

    return conn


# Index page : just display a form asking for minecraft username
@app.route("/")
def index():
    return """
            <h1></h1> 
            <form action="/display_skin">
                <label for="username">Minecraft username:</label><br>
                <input type="text" id="fname" name="username"><br>
                <input type="submit">
            </form>
            <p><a href="admin_view"> Admin page </a></p>
            """

# Display skin page : get the player head given it's username, and store the queried names in queried_name.json
@app.route("/display_skin")
def display_skin():
    username = request.args.get("username", "").strip()
    if not username:
        return "Missing username", 400

    url = f"https://api.mojang.com/users/profiles/minecraft/{username}"
    try:
        with urllib.request.urlopen(url) as resp:
            if resp.getcode() != 200:
                return """User not found<a href="/"><input type="button" value="Back"/></a>""", 404
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code in (204, 404):
            return """User not found <a href="/"><input type="button" value="Back"/></a>""", 404
        raise

    player_uuid = data.get("id")

    avatar_url = f"https://mc-heads.net/avatar/{player_uuid}"

    number_of_queries = update_query_count(username)
    return f"""<h2>Minecraft head of {username}</h2>
            <img src="{avatar_url}" alt="Minecraft head of {username}">
            <p>Number of queries for {username} head : {number_of_queries}</p>
            <a href="/"><input type="button" value="Back"/></a>
            """

# Display statistics about the number of username queried
@app.route("/admin_view")
def admin_view():
    conn = get_db_connection()
    stats = None
    with conn.cursor() as cur:
        cur.execute('SELECT * FROM stats;')
        stats = cur.fetchall()
    html_page = """<h2>Statistics for this website</h2>
                    <p>Number of query for each username</p>
                    <ul>
                """
    for stat in stats:
        html_page += f"<li>{stat[1]} : {stat[2]} queries</li>"
    html_page += "</ul>"
    return html_page

# Update the count of username
def update_query_count(username) -> int:
    # Discard empty usernames
    username = (username or "").strip()
    if not username:
        return 0

    conn = get_db_connection()
    stat_row = []
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO stats (username, nb_query)
            VALUES (%s, 1)
            ON CONFLICT (username)
            DO UPDATE SET nb_query = stats.nb_query + 1
            RETURNING nb_query;
            """,
            (username,)
        )
        if cur.rowcount == 0:
            print(f"[ERROR] No entries for username just updated : {username}")
            return 0
        if cur.rowcount > 1:
            print(f"[WARNING] {cur.rowcount} entries for the same username : {username}")
        stat_row = cur.fetch_one()

    conn.commit()
    # Return query count
    # 
    # Stats
    # ID username query_count
    return stat_row[2]