import sqlite3
import hashlib
import binascii
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "leaderboard.db")


class Database:
	"""SQLite-backed storage for user accounts and leaderboard scores."""
	def __init__(self, path=DB_PATH):
		os.makedirs(os.path.dirname(path), exist_ok=True)
		self.conn = sqlite3.connect(path)
		self._create_tables()

	# creates the users and scores tables if they don't already exist
	def _create_tables(self):
		self.conn.execute("""
			CREATE TABLE IF NOT EXISTS users (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				username TEXT UNIQUE NOT NULL,
				password_hash TEXT NOT NULL,
				salt TEXT NOT NULL
			)
		""")
		self.conn.execute("""
			CREATE TABLE IF NOT EXISTS scores (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				username TEXT NOT NULL,
				time_alive REAL NOT NULL,
				rounds_passed INTEGER NOT NULL,
				kills INTEGER NOT NULL,
				date_played TEXT NOT NULL
			)
		""")
		self.conn.commit()

	# hashes a password with PBKDF2, generating a random salt if one isn't given
	def _hash_password(self, password, salt=None):
		if salt is None:
			salt = binascii.hexlify(os.urandom(16)).decode()
		hash_bytes = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
		return binascii.hexlify(hash_bytes).decode(), salt

	# creates a new account, hashing the password, and rejects duplicate usernames
	def register_user(self, username, password):
		username = username.strip()
		if not username or not password:
			return False, "Username and password required"
		password_hash, salt = self._hash_password(password)
		try:
			self.conn.execute(
				"INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
				(username, password_hash, salt),
			)
			self.conn.commit()
			return True, "Account created"
		except sqlite3.IntegrityError:
			return False, "That username is already taken"

	# checks a login attempt against the stored password hash for that username
	def verify_user(self, username, password):
		username = username.strip()
		row = self.conn.execute(
			"SELECT password_hash, salt FROM users WHERE username = ?", (username,)
		).fetchone()
		if row is None:
			return False, "No account with that username"
		stored_hash, salt = row
		test_hash, _ = self._hash_password(password, salt)
		if test_hash == stored_hash:
			return True, "Logged in"
		return False, "Incorrect password"

	def submit_score(self, username, time_alive, rounds_passed, kills):
		self.conn.execute(
			"INSERT INTO scores (username, time_alive, rounds_passed, kills, date_played) VALUES (?, ?, ?, ?, ?)",
			(username, time_alive, rounds_passed, kills, datetime.now().isoformat(timespec="seconds")),
		)
		self.conn.commit()

	# fetches the top scores for the leaderboard, sorted by the given column
	def top_scores(self, order_by="rounds_passed", limit=10):
		if order_by not in ("rounds_passed", "kills", "time_alive"):
			order_by = "rounds_passed"
		return self.conn.execute(
			f"SELECT username, time_alive, rounds_passed, kills, date_played "
			f"FROM scores ORDER BY {order_by} DESC, kills DESC LIMIT ?",
			(limit,),
		).fetchall()

	def all_scores(self, limit=100):
		return self.conn.execute(
			"SELECT id, username, time_alive, rounds_passed, kills, date_played "
			"FROM scores ORDER BY id DESC LIMIT ?",
			(limit,),
		).fetchall()

	def delete_score(self, score_id):
		self.conn.execute("DELETE FROM scores WHERE id = ?", (score_id,))
		self.conn.commit()

	def clear_scores(self):
		self.conn.execute("DELETE FROM scores")
		self.conn.commit()

	def close(self):
		self.conn.close()
