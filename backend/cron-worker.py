import time
from db import connect_db
from utils import fetch_filtered_prs, update_leaderboard
import logging
import datetime
import signal
import sys
from dotenv import load_dotenv
import os

load_dotenv()

os.getenv('CRON_TOKEN')

# Most of this code is GPT, i no no know how to make cron, forgive me :pensive:
logging.basicConfig(level=logging.DEBUG)


RUNNING = True  # Global flag for graceful shutdown

def handle_exit(signum, frame):
    global RUNNING
    logging.info("Received termination signal. Exiting gracefully...")
    RUNNING = False

# Attach signal handlers for graceful termination
signal.signal(signal.SIGTERM, handle_exit)
signal.signal(signal.SIGINT, handle_exit)

def cron_worker():
    global RUNNING
    client = None
    attempts = 0

    try:
        if client is None or client.isolation_level is None:
            client = connect_db()

        update_leaderboard(client)  # Initialize leaderboard once
        logging.info("Leaderboard initialized.")

        while RUNNING:
            try:
                pr_count = fetch_filtered_prs(client)
                logging.info(f"Processed {pr_count} new PRs.")
                attempts = 0

            except Exception as e:
                attempts += 1
                wait_time = min(60 * (2 ** attempts), 300)
                logging.error(f"Error in cron job: {str(e)}. Retrying in {wait_time} seconds.")
                time.sleep(wait_time)

            time.sleep(45 * 60)

    except Exception as e:
        logging.critical(f"Critical failure in cron worker: {str(e)}", exc_info=True)

    finally:
        if client:
            client.close()
        logging.info("Cron worker exited.")


if __name__ == "__main__":
    cron_worker()
