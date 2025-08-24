from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import Config
from database import db
from models.user import User

async def referral_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_model = User(user.id)
    
    referral_link = f"https://t.me/{context.bot.username}?start={user.id}"
    
    message = (
        f"👥 রেফারেল সিস্টেম\n\n"
        f"💰 প্রারম্ভিক বোনাস: {Config.REFERRAL_BONUS['initial']} points\n"
        f"📈 মাসিক বোনাস: {len(Config.REFERRAL_BONUS['monthly'])} মাস\n\n"
        f"🔗 আপনার রেফারেল লিংক:\n{referral_link}\n\n"
        f"📊 মোট রেফারেল: {user_model.referral_count} জন\n\n"
        "✅ একজন রেফার করলে আপনি পাবেন:\n"
        f"- সাথে সাথে: {Config.REFERRAL_BONUS['initial']} points\n"
        "- প্রতি মাসের ১ তারিখে: অতিরিক্ত বোনাস\n"
        "- সর্বমোট ১২ মাস বোনাস\n\n"
        "⚠️ শর্ত: রেফার করা ইউজারকে একাউন্ট একটিভ করতে হবে"
    )
    
    await update.message.reply_text(message)

async def handle_referral_bonus(context: ContextTypes.DEFAULT_TYPE):
    """মাসিক রেফারেল বোনাস ডিস্ট্রিবিউট করে"""
    cursor = db.conn.cursor()
    
    # Get all active referrals that haven't expired
    cursor.execute('''
        SELECT r.*, u.balance 
        FROM referrals r 
        JOIN users u ON r.referrer_id = u.user_id 
        WHERE r.expires_at > datetime('now') 
        AND r.monthly_bonuses_given < ?
    ''', (len(Config.REFERRAL_BONUS['monthly']),))
    
    referrals = cursor.fetchall()
    
    for referral in referrals:
        referrer_id = referral[1]
        monthly_bonuses_given = referral[4]
        
        if monthly_bonuses_given < len(Config.REFERRAL_BONUS['monthly']):
            bonus_amount = Config.REFERRAL_BONUS['monthly'][monthly_bonuses_given]
            
            # Add bonus to referrer
            cursor.execute('''
                UPDATE users SET balance = balance + ?, total_earned = total_earned + ? 
                WHERE user_id = ?
            ''', (bonus_amount, bonus_amount, referrer_id))
            
            # Update bonus count
            cursor.execute('''
                UPDATE referrals SET monthly_bonuses_given = monthly_bonuses_given + 1 
                WHERE referrer_id = ? AND referred_id = ?
            ''', (referrer_id, referral[2]))
            
            # Notify user
            try:
                await context.bot.send_message(
                    chat_id=referrer_id,
                    text=f"🎉 রেফারেল মাসিক বোনাস!\n\n+{bonus_amount} points\n"
                         f"আপনার রেফারেল থেকে মাসিক বোনাস পেয়েছেন!"
                )
            except Exception as e:
                print(f"Could not notify user {referrer_id}: {e}")
    
    db.conn.commit()
