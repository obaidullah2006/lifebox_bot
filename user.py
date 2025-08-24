from database import db

class User:
    def __init__(self, user_id):
        self.user_id = user_id
        self.data = db.get_user(user_id)
    
    @property
    def is_active(self):
        return self.data and self.data[4]
    
    @property
    def balance(self):
        return self.data[5] if self.data else 0
    
    @property
    def username(self):
        return self.data[1] if self.data else None
    
    @property
    def referral_count(self):
        return self.data[7] if self.data else 0
    
    @property
    def withdraw_count(self):
        return self.data[11] if self.data and len(self.data) > 11 else 0
    
    def activate(self):
        cursor = db.conn.cursor()
        cursor.execute("UPDATE users SET is_active = TRUE WHERE user_id = ?", (self.user_id,))
        db.conn.commit()
    
    def add_balance(self, amount):
        cursor = db.conn.cursor()
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, self.user_id))
        db.conn.commit()
    
    def deduct_balance(self, amount):
        cursor = db.conn.cursor()
        cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, self.user_id))
        db.conn.commit()
