import json
import os
from datetime import datetime

DB_FILE = "calorie_bank_db.json"

class CalorieBank:
    def __init__(self):
        self.balance = 0
        self.history = []
        self._load_state()

    def _load_state(self):
        """Safely loads balance from local disk."""
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, 'r') as f:
                    data = json.load(f)
                    self.balance = data.get("balance", 0)
                    self.history = data.get("history", [])
            except Exception:
                self.balance = 0
                self.history = []

    def _save_state(self):
        """Saves current balance securely back to local storage."""
        with open(DB_FILE, 'w') as f:
            json.dump({"balance": self.balance, "history": self.history}, f, indent=4)

    def deposit_run(self, file_name: str, calories_burned: int) -> int:
        """Processes an upload confirmation and drops raw fuel tokens into the bank."""
        if calories_burned <= 0:
            return self.balance
            
        self.balance += calories_burned
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "type": "RUN_UPLOAD",
            "source": file_name,
            "amount": calories_burned
        })
        self._save_state()
        return self.balance

