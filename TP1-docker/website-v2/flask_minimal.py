from flask import Flask
from flask import request
import subprocess
import urllib.request, urllib.error, json

app = Flask(__name__)

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

    number_of_queries = update_query_names(username)
    return f"""<h2>Minecraft head of {username}</h2>
            <img src="{avatar_url}" alt="Minecraft head of {username}">
            <p>Number of queries for {username} head : {number_of_queries}</p>
            <a href="/"><input type="button" value="Back"/></a>
            """

def update_query_names(username) -> int:
    process = subprocess.run(["./customDbExe", username])
    return process.returncode