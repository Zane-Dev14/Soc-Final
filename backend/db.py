import os
import sqlite3
import logging
from dotenv import load_dotenv
import requests
from utils import fetch_user_repos

load_dotenv()
logging.basicConfig(level=logging.DEBUG)

DB_PATH = os.getenv('SQLITE_DB_PATH','./app.db')

def connect_db():
    logging.debug("Connecting to database...")
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    if not isinstance(conn, sqlite3.Connection):
        raise Exception("Failed to establish database connection.")
    return conn

client = connect_db()

def setup_database():
    logging.debug("Setting up database.")
    client.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        github_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        email TEXT,
        phone_no TEXT,  
        token TEXT NOT NULL
    );
    """)
    
    client.execute("""
    CREATE TABLE IF NOT EXISTS pull_requests (
        pr_id INTEGER PRIMARY KEY,
        repo_name TEXT NOT NULL,
        github_login TEXT NOT NULL,
        total_commits INTEGER DEFAULT 0,
        total_lines INTEGER DEFAULT 0,
        status TEXT DEFAULT 'open',
        FOREIGN KEY(github_login) REFERENCES users(github_id)
    );
    """)
    
    client.execute("""
    CREATE TABLE IF NOT EXISTS leaderboard (
        user_id INTEGER PRIMARY KEY,   
        total_prs INTEGER DEFAULT 0,
        total_commits INTEGER DEFAULT 0,
        total_lines INTEGER DEFAULT 0,
        points INTEGER DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    """)
    logging.debug("Database setup complete.")
    
def save_user_to_db(github_user, email, phone, token,SOCname):
    logging.debug(f"Checking if user exists: {github_user['login']}")

    client.execute("""
INSERT OR REPLACE INTO users (github_id, name, email, phone_no, token)
VALUES (?, ?, ?, ?, ?)
""", (github_user['login'], SOCname, email, phone, token))

    
    client.commit()

def get_all_users():
    res = client.execute("SELECT * FROM users").fetchall()
    users = []

    for row in res:
        github_username = row[1]
        try:
            repos = fetch_user_repos(github_username, client)
            repo_details = [
                {
                    'repo_name': repo['name'],
                    'last_commit': repo['updated_at']
                }
                for repo in repos
            ]
        except Exception as e:
            logging.error(f"Failed to fetch repos for {github_username}: {str(e)}")
            repo_details = [] 
        
        users.append({
            'SOCid': row[0],
            'username': github_username,
            'email': row[3],
            'repos': repo_details
        })
    return users
