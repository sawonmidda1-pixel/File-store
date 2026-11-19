import sqlite3
import secrets
import string
from pathlib import Path

class Database:
    def __init__(self, db_path="bot_data.sqlite3"):
        self.db_path = str(db_path)
        self._init_db()

    def _connect(self):
        con = sqlite3.connect(self.db_path, timeout=30)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        return con

    def _init_db(self):
        with self._connect() as con:
            con.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    coins INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    price INTEGER NOT NULL CHECK(price >= 0),
                    content TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS purchases (
                    user_id INTEGER NOT NULL,
                    file_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, file_id),
                    FOREIGN KEY(user_id) REFERENCES users(user_id),
                    FOREIGN KEY(file_id) REFERENCES files(id)
                );
                CREATE TABLE IF NOT EXISTS referrals (
                    referrer_id INTEGER NOT NULL,
                    referred_id INTEGER NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS redeem_codes (
                    code TEXT PRIMARY KEY,
                    coins INTEGER NOT NULL,
                    max_uses INTEGER NOT NULL,
                    uses INTEGER NOT NULL DEFAULT 0,
                    active INTEGER NOT NULL DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS redeem_uses (
                    code TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (code, user_id)
                );
            """)

    def add_user(self, user_id, username):
        with self._connect() as con:
            cur = con.execute(
                "INSERT OR IGNORE INTO users(user_id, username) VALUES (?, ?)",
                (int(user_id), str(username))
            )
            con.execute("UPDATE users SET username=? WHERE user_id=?",
                        (str(username), int(user_id)))
            return cur.rowcount == 1

    def user_exists(self, user_id):
        with self._connect() as con:
            return con.execute("SELECT 1 FROM users WHERE user_id=?",
                               (int(user_id),)).fetchone() is not None

    def add_coins(self, user_id, amount):
        with self._connect() as con:
            con.execute("UPDATE users SET coins=coins+? WHERE user_id=?",
                        (int(amount), int(user_id)))

    def deduct_coins(self, user_id, amount):
        with self._connect() as con:
            cur = con.execute(
                "UPDATE users SET coins=coins-? WHERE user_id=? AND coins>=?",
                (int(amount), int(user_id), int(amount))
            )
            if cur.rowcount != 1:
                raise ValueError("User not found or insufficient coins")

    def get_coins(self, user_id):
        with self._connect() as con:
            row = con.execute("SELECT coins FROM users WHERE user_id=?",
                              (int(user_id),)).fetchone()
            return int(row["coins"]) if row else 0

    def record_referral(self, referrer_id, referred_id):
        with self._connect() as con:
            con.execute(
                "INSERT OR IGNORE INTO referrals(referrer_id, referred_id) VALUES (?, ?)",
                (int(referrer_id), int(referred_id))
            )

    def get_referral_count(self, user_id):
        with self._connect() as con:
            row = con.execute("SELECT COUNT(*) AS n FROM referrals WHERE referrer_id=?",
                              (int(user_id),)).fetchone()
            return int(row["n"])

    def add_file(self, name, price, content):
        with self._connect() as con:
            con.execute("INSERT INTO files(name, price, content) VALUES (?, ?, ?)",
                        (str(name), int(price), str(content)))

    def get_all_files(self):
        with self._connect() as con:
            return [dict(r) for r in con.execute(
                "SELECT id, name, price, content FROM files ORDER BY id DESC"
            ).fetchall()]

    def get_file(self, file_id):
        with self._connect() as con:
            row = con.execute("SELECT id, name, price, content FROM files WHERE id=?",
                              (int(file_id),)).fetchone()
            return dict(row) if row else None

    def remove_file(self, file_id):
        with self._connect() as con:
            con.execute("DELETE FROM purchases WHERE file_id=?", (int(file_id),))
            con.execute("DELETE FROM files WHERE id=?", (int(file_id),))

    def already_purchased(self, user_id, file_id):
        with self._connect() as con:
            return con.execute(
                "SELECT 1 FROM purchases WHERE user_id=? AND file_id=?",
                (int(user_id), int(file_id))
            ).fetchone() is not None

    def record_purchase(self, user_id, file_id):
        with self._connect() as con:
            con.execute("INSERT OR IGNORE INTO purchases(user_id, file_id) VALUES (?, ?)",
                        (int(user_id), int(file_id)))

    def get_purchase_count(self, user_id):
        with self._connect() as con:
            row = con.execute("SELECT COUNT(*) AS n FROM purchases WHERE user_id=?",
                              (int(user_id),)).fetchone()
            return int(row["n"])

    def get_leaderboard(self):
        with self._connect() as con:
            return [dict(r) for r in con.execute(
                "SELECT username, coins FROM users ORDER BY coins DESC, user_id ASC LIMIT 10"
            ).fetchall()]

    def create_redeem_code(self, coins, max_uses):
        alphabet = string.ascii_uppercase + string.digits
        with self._connect() as con:
            for _ in range(10):
                code = ''.join(secrets.choice(alphabet) for _ in range(10))
                try:
                    con.execute(
                        "INSERT INTO redeem_codes(code, coins, max_uses) VALUES (?, ?, ?)",
                        (code, int(coins), int(max_uses))
                    )
                    return code
                except sqlite3.IntegrityError:
                    continue
        raise RuntimeError("Could not create a unique redeem code")

    def use_redeem_code(self, code, user_id):
        code = str(code).strip().upper()
        user_id = int(user_id)
        with self._connect() as con:
            row = con.execute(
                "SELECT coins, max_uses, uses, active FROM redeem_codes WHERE code=?",
                (code,)
            ).fetchone()
            if not row:
                return "not_found"
            if not row["active"] or row["uses"] >= row["max_uses"]:
                return "expired"
            if con.execute("SELECT 1 FROM redeem_uses WHERE code=? AND user_id=?",
                           (code, user_id)).fetchone():
                return "already_used"
            con.execute("INSERT INTO redeem_uses(code, user_id) VALUES (?, ?)",
                        (code, user_id))
            con.execute("UPDATE redeem_codes SET uses=uses+1 WHERE code=?", (code,))
            con.execute("UPDATE users SET coins=coins+? WHERE user_id=?",
                        (int(row["coins"]), user_id))
            return int(row["coins"])

    def find_user(self, identifier):
        identifier = str(identifier).strip().lstrip("@")
        with self._connect() as con:
            if identifier.isdigit():
                row = con.execute(
                    "SELECT user_id, username, coins FROM users WHERE user_id=?",
                    (int(identifier),)
                ).fetchone()
            else:
                row = con.execute(
                    "SELECT user_id, username, coins FROM users WHERE lower(username)=lower(?)",
                    (identifier,)
                ).fetchone()
            return dict(row) if row else None

    def get_all_users(self):
        with self._connect() as con:
            return [dict(r) for r in con.execute(
                "SELECT user_id, username, coins FROM users ORDER BY user_id"
            ).fetchall()]

    def get_stats(self):
        with self._connect() as con:
            users = con.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            files = con.execute("SELECT COUNT(*) FROM files").fetchone()[0]
            purchases = con.execute("SELECT COUNT(*) FROM purchases").fetchone()[0]
            codes = con.execute(
                "SELECT COUNT(*) FROM redeem_codes WHERE active=1 AND uses<max_uses"
            ).fetchone()[0]
            return {"users": users, "files": files,
                    "purchases": purchases, "codes": codes}
