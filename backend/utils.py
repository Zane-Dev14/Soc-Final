import random
import requests
import logging
from flask import redirect
import datetime
import time

from configs.globals import CRON_TOKEN

logging.basicConfig(level=logging.DEBUG)


def calculate_leaderboard(client):
    pr_list = client.execute("""
    SELECT pr_id, repo_name, github_login
    FROM pull_requests
    JOIN users ON pull_requests.user_id = users.id
    GROUP BY users.name
    ORDER BY pr_count DESC;
    """)
    return list(pr_list)

def fetch_user_repos(username, client):
    max_attempts = 3
    attempts = 0
    token = client.execute(f"SELECT key FROM users WHERE github_id = {username}").fetchall()

    if not token:
        logging.warning("No tokens available. Redirecting to refresh login.")
        return None

    while attempts < max_attempts:
        url = f"https://api.github.com/users/{username}/repos"
        headers = {'Authorization': f'token {token[0]}'}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                logging.error(f"Token {token} is unauthorized. Removing...")
            elif response.status_code == 403:
                logging.warning(f"Token {token} exceeded rate limit. Rotating...")
            else:
                logging.error(f"Failed to fetch repos for {username}: {e}")
                raise e

    raise Exception("All tokens failed or rate-limited.")

def update_leaderboard(client):
    try:
        cursor = client.cursor()
        cursor.execute("""
        INSERT OR IGNORE INTO leaderboard (user_id, total_prs, total_commits, total_lines, points)
        SELECT id, 0, 0, 0, 0 FROM users
        """)
        client.commit()
        cursor.close()
    except Exception as e:
        logging.error(f"Error updating leaderboard: {str(e)}")


def load_filter_list():
    with open('filter.txt', 'r') as f:
        return [line.strip() for line in f if line.strip()]
def fetch_filtered_prs(client):
    repos = load_filter_list()
    pr_count = 0

    for repo in repos:
        prs = fetch_recent_prs(repo, client)
        if not prs:
            continue

        for pr in prs:
            print(f"PR State: {pr['state']}")
            if pr['state'] != 'open':
                continue

            github_login = pr['user']['login'] if 'user' in pr else None
            if not github_login:
                continue

            existing_pr = client.execute(
                "SELECT pr_id, status FROM pull_requests WHERE pr_id = ?",
                (pr['id'],)
            ).fetchone()

            if existing_pr and existing_pr['status'] == 'open' and pr['state'] == 'merged':
                client.execute("""
                    UPDATE pull_requests
                    SET status = 'merged'
                    WHERE pr_id = ?
                """, (pr['id'],))
                client.commit()

                client.execute("""
                    UPDATE leaderboard
                    SET points = points + 10
                    WHERE user_id = (SELECT id FROM users WHERE github_id = ?)
                """, (github_login,))

                client.commit()

            elif not existing_pr:
                pr_details = fetch_pr_details(repo, pr['id'], client)
                if not pr_details:
                    continue

                total_commits = pr_details.get('commits', 0)
                total_lines = pr_details.get('additions', 0) - pr_details.get('deletions', 0)

                client.execute("""
                    INSERT INTO pull_requests (pr_id, repo_name, github_login, total_commits, total_lines, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    pr['id'],
                    repo,
                    github_login,
                    total_commits,
                    total_lines,
                    pr['state']
                ))

                pr_count += 1

    client.commit()
    return pr_count


def fetch_recent_prs(repo, client):
    token = CRON_TOKEN
    url = f"https://api.github.com/repos/{repo}/pulls?state=open"
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    while True:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 403:
            retry_after = response.headers.get('Retry-After')
            if retry_after:
                wait_time = int(retry_after)
            else:
                reset_time = int(response.headers.get('X-RateLimit-Reset', time.time()))
                wait_time = max(reset_time - int(datetime.datetime.now().timestamp()), 60)
            logging.warning(f"Rate limit hit. Sleeping for {wait_time} seconds...")
            time.sleep(wait_time + 1)
        else:
            logging.error(f"Failed to fetch open PRs for {repo}: {response.status_code}")
            break

    return None


def insert_pull_request(client, pr, repo):
    github_login = pr['user']['login']
    pr_details = fetch_pr_details(repo, pr['id'], client)
    
    if pr_details:
        total_lines = pr_details['additions'] - pr_details['deletions']
        client.execute("""
        INSERT INTO pull_requests (pr_id, repo_name, github_login, total_commits, total_lines, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            pr['id'],
            repo,
            github_login,
            pr_details['commits'],
            total_lines,
            pr['state']  # Assuming you want to store PR status as well
        ))
        logging.info(f"Inserted PR {pr['id']} by {github_login} for {repo}")
    else:
        logging.warning(f"Skipping PR {pr['id']} due to missing details.")
    
    client.commit()


def fetch_pr_details(repo, pr_id, client):
    token=CRON_TOKEN
    # Fetch all open PRs and match the pr_id manually
    url = f"https://api.github.com/repos/{repo}/pulls"
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        pr_list = response.json()
        
        # Search for matching PR by ID
        matched_pr = next((pr for pr in pr_list if pr['id'] == pr_id), None)
        if not matched_pr:
            logging.warning(f"PR {pr_id} not found in the open PR list for {repo}")
            return None
        
        # Fetch detailed info using the pulls_url
        detail_url = matched_pr['url']  # This is the correct URL for the PR
        details_response = requests.get(detail_url, headers=headers)

        if details_response.status_code == 200:
            pr_details = details_response.json()
            return {
                'commits': pr_details['commits'],
                'additions': pr_details['additions'],
                'deletions': pr_details['deletions']
            }
        else:
            logging.warning(f"Failed to fetch detailed PR data: {details_response.status_code}")
            return None
    else:
        logging.error(f"Failed to fetch open PRs for {repo}: {response.status_code}")
        return None
