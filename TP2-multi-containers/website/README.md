# A minimal minecraft head display server

A server to display a player head : enter the player username, and it will display its skin.

The server save statistics about the queried usernames a postgres database.

# Setup

Requires python3

- Install Flask : `pip install flask`
- Install psycopg2-binary : `pip install psycopg2-binary`
- Run the server : `flask --app flask_minimal.py`

By default, the server is listening on port 5000

# PostgreSQL Database

**Prerequisites:**

- PostgreSQL server must be running and accessible at the hostname "postgres"
- The database `"database"` must exist
- The user `"postgres"` must exist and have access to the specified database

**Postgresql Configuration:**

Postgres server hostname : "postgres"
Database : "database"
User : "postgres"
Password : "admin"

**Security Note:**

Credentials should not be hardcoded. Use environment variables or a configuration file for production deployments.

# Changelog

V3: Changed database from json file to postgres
