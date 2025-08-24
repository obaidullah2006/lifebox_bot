import os
import sqlite3
import logging
from datetime import datetime, timedelta
from config import Config

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        if Config.DATABASE_URL.startswith('sqlite'):
            self.conn = sqlite3.connect('lifebox.db', check_same_thread=False)
        else:
            import psycopg2
            self.conn = psycopg2.connect(Config.DATABASE_URL, sslmode='require')
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Users টেবিল
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                is_active BOOLEAN DEFAULT FALSE,
                balance INTEGER DEFAULT 0,
                referrer_id INTEGER,
                referral_count INTEGER DEFAULT 0,
                total_earned INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                withdraw_count INTEGER DEFAULT 0
            )
        ''')
        
        # Transactions টেবিল
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                transaction_id TEXT UNIQUE,
                amount INTEGER,
                payment_method TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Withdrawals টেবিল
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS withdrawals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                method TEXT,
                account_number TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Referrals টেবিল
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                referred_id INTEGER UNIQUE,
                bonus_given BOOLEAN DEFAULT FALSE,
                monthly_bonuses_given INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP DEFAULT (DATETIME('now', '+1 year')),
                FOREIGN KEY (referrer_id) REFERENCES users (user_id),
                FOREIGN KEY (referred_id) REFERENCES users (user_id)
            )
        ''')
        
        # Tasks টেবিল
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_type TEXT,
                title TEXT,
                description TEXT,
                points INTEGER,
                link TEXT,
                requires_screenshot BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP DEFAULT (DATETIME('now', '+5 months'))
            )
        ''')
        
        # Completed Tasks টেবিল
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS completed_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                task_id INTEGER,
                screenshot_id TEXT,
                status TEXT DEFAULT 'pending',
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                points_awarded BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )
        ''')
        
        # Screenshots টেবিল
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS screenshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                task_id INTEGER,
                file_id TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                verified_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )
        ''')
        
        self.conn.commit()
        logger.info("Database tables created successfully")
    
    def get_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return cursor.fetchone()
    
    def add_user(self, user_id, username, first_name, last_name, referrer_id=None):
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (user_id, username, first_name, last_name, referrer_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name, referrer_id))
            
            if referrer_id:
                cursor.execute('''
                    INSERT INTO referrals (referrer_id, referred_id)
                    VALUES (?, ?)
                ''', (referrer_id, user_id))
                
                cursor.execute('''
                    UPDATE users SET referral_count = referral_count + 1 
                    WHERE user_id = ?
                ''', (referrer_id,))
            
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return False
    
    def update_user_balance(self, user_id, amount):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE users SET balance = balance + ?, total_earned = total_earned + ? 
            WHERE user_id = ?
        ''', (amount, amount, user_id))
        self.conn.commit()
    
    def get_pending_activations(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT t.*, u.username 
            FROM transactions t 
            JOIN users u ON t.user_id = u.user_id 
            WHERE t.status = 'pending'
        ''')
        return cursor.fetchall()
    
    def get_pending_withdrawals(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT w.*, u.username 
            FROM withdrawals w 
            JOIN users u ON w.user_id = u.user_id 
            WHERE w.status = 'pending'
        ''')
        return cursor.fetchall()

db = Database()
