import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN", "8273775147:AAFlZtDYFs4GhaSmmfnHMTrVzEvsbZTV_Fc")
    ADMIN_ID = int(os.getenv("ADMIN_ID", "8010011335"))
    API_ID = os.getenv("API_ID")
    API_HASH = os.getenv("API_HASH")
    BOT_NAME = "LifeBox"
    
    BKASH_NUMBER = os.getenv("BKASH_NUMBER", "01906721744")
    NAGAD_NUMBER = os.getenv("NAGAD_NUMBER", "01906721744")
    ACTIVATION_AMOUNT = 200
    
    POINTS_PER_BDT = int(os.getenv("POINTS_PER_BDT", "10"))
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///lifebox.db")
    
    REFERRAL_BONUS = {
        'initial': 300,
        'monthly': [100, 90, 80, 70, 70, 70, 70, 60, 60, 50, 50]
    }
    
    WITHDRAW_CONDITIONS = {
        'min_referrals': 1,
        'withdraw_min': [1000, 2000, 3000],
        'withdraw_max': 10000,
        'withdraw_counts': {}  # ইউজার আইডি অনুযায়ী কতবার withdrawn হয়েছে
    }
    
    CONTRACT_CHANNEL = "https://t.me/+lzLsjJxGrmY0NzE1"
    JOIN_CHANNEL = "https://t.me/inlifebox"
    
    TASK_SETTINGS = {
        'daily_task_limit': 2,
        'time_task_expiry_months': 5,
        'screenshot_verification_minutes': 30
  }
