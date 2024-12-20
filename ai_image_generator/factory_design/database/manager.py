import sqlite3
import json
import os
from typing import Dict, List, Tuple
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path: str = "./data/image_generation_history.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.create_table()

    def create_table(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS generation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    model TEXT,
                    prompt TEXT,
                    parameters TEXT,
                    image_path TEXT
                )
            """
            )

    def save_generation(
        self, model: str, prompt: str, parameters: Dict, image_path: str
    ):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO generation_history (model, prompt, parameters, image_path) VALUES (?, ?, ?, ?)",
                (model, prompt, json.dumps(parameters), image_path),
            )

    def get_history(self, limit: int = 10) -> List[Tuple]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM generation_history ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            )
            return cursor.fetchall()