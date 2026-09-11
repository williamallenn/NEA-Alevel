import sqlite3
from database import DB_PATH

# prints a database table as a column-aligned text table, widths sized to fit the data
def print_table(conn, table, columns):
	rows = conn.execute(f"SELECT {', '.join(columns)} FROM {table} ORDER BY id").fetchall()
	if not rows:
		print("  (no rows)")
		return
	widths = [max(len(col), max(len(str(row[i])) for row in rows)) for i, col in enumerate(columns)]
	header = "  ".join(col.ljust(widths[i]) for i, col in enumerate(columns))
	print(header)
	print("-" * len(header))
	for row in rows:
		print("  ".join(str(row[i]).ljust(widths[i]) for i in range(len(columns))))

# prints the users and scores tables from the leaderboard database
def main():
	conn = sqlite3.connect(DB_PATH)
	print(f"Database file: {DB_PATH}\n")

	print("=== users ===")
	print_table(conn, "users", ["id", "username"])

	print("\n=== scores ===")
	print_table(conn, "scores", ["id", "username", "time_alive", "rounds_passed", "kills", "date_played"])

	conn.close()


if __name__ == "__main__":
	main()
