import sqlite3
import hashlib
import binascii
import os
from datetime import datetime

DbPath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "leaderboard.db")


class Database:
	def __init__(self, path=DbPath):
		os.makedirs(os.path.dirname(path), exist_ok=True)
		self.conn = sqlite3.connect(path)
		self._createTables()

	def _createTables(self):
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

	def _hashPassword(self, password, salt=None):
		if salt is None:
			salt = binascii.hexlify(os.urandom(16)).decode()
		hashBytes = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
		return binascii.hexlify(hashBytes).decode(), salt

	def registerUser(self, username, password):
		username = username.strip()
		if not username or not password:
			return False, "Username and password required"
		passwordHash, salt = self._hashPassword(password)
		try:
			self.conn.execute(
				"INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
				(username, passwordHash, salt),
			)
			self.conn.commit()
			return True, "Account created"
		except sqlite3.IntegrityError:
			return False, "That username is already taken"

	def verifyUser(self, username, password):
		username = username.strip()
		row = self.conn.execute(
			"SELECT password_hash, salt FROM users WHERE username = ?", (username,)
		).fetchone()
		if row is None:
			return False, "No account with that username"
		storedHash, salt = row
		testHash, _ = self._hashPassword(password, salt)
		if testHash == storedHash:
			return True, "Logged in"
		return False, "Incorrect password"

	def submitScore(self, username, timeAlive, roundsPassed, kills):
		self.conn.execute(
			"INSERT INTO scores (username, time_alive, rounds_passed, kills, date_played) VALUES (?, ?, ?, ?, ?)",
			(username, timeAlive, roundsPassed, kills, datetime.now().isoformat(timespec="seconds")),
		)
		self.conn.commit()

	def topScores(self, orderBy="rounds_passed", limit=10):
		if orderBy not in ("rounds_passed", "kills", "time_alive"):
			orderBy = "rounds_passed"
		return self.conn.execute(
			f"SELECT username, time_alive, rounds_passed, kills, date_played "
			f"FROM scores ORDER BY {orderBy} DESC, kills DESC LIMIT ?",
			(limit,),
		).fetchall()

	def close(self):
		self.conn.close()
