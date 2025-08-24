from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import Config
from database import db
from models.user import User
from handlers.admin import send_admin_notification
from keyboards import get_payment_keyboard

async def payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "payment_activate":
        await query.edit_message_text(
            f"💳 একাউন্ট একটিভেশন\n\n"
            f"একাউন্ট একটিভ করতে {Config.ACTIVATION_AMOUNT}৳ সেন্ড মানি করুন\n\n"
            "পেমেন্ট মাধ্যম সিলেক্ট করুন:",
            reply_markup=get_payment_keyboard()
        )
    
    elif query.data in ["payment_bkash", "payment_nagad"]:
        method = "bkash" if query.data == "payment_bkash" else "nagad"
        number = Config.BKASH_NUMBER if method == "bkash" else Config.NAGAD_NUMBER
        
        context.user_data['payment_method'] = method
        
        await query.edit_message_text(
            f"🔵 {method.upper()} - {number}\n\n"
            "💳 পেমেন্ট完成后, আপনার ট্রানজেকশন আইডি এই চ্যাটে পাঠান:\n\n"
            "⚠️ মনে রাখবেন: একই ট্রানজেকশন আইডি reuse করা যাবে না"
        )

async def transaction_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    transaction_id = update.message.text.strip()
    
    if 'payment_method' in context.user_data:
        method = context.user_data['payment_method']
        
        if is_valid_transaction(transaction_id):
            cursor = db.conn.cursor()
            cursor.execute('''
                INSERT INTO transactions (user_id, transaction_id, amount, payment_method)
                VALUES (?, ?, ?, ?)
            ''', (user_id, transaction_id, Config.ACTIVATION_AMOUNT, method))
            db.conn.commit()
            
            await notify_admin(update, context, user_id, transaction_id, method)
            
            await update.message.reply_text(
                "✅ আপনার রিকুয়েস্ট গ্রহণ করা হয়েছে\n\n"
                "⏳ কিছুক্ষণ অপেক্ষা করুন, এডমিন ASAP approve করবেন"
            )
        else:
            await update.message.reply_text(
                "❌ এই ট্রানজেকশন আইডি ইতিমধ্যে ব্যবহার করা হয়েছে\n\n"
                "⚠️ সঠিক ও বৈধ ট্রানজেকশন আইডি দিন"
            )

def is_valid_transaction(transaction_id):
    cursor = db.conn.cursor()
    cursor.execute("SELECT * FROM transactions WHERE transaction_id = ?", (transaction_id,))
    return cursor.fetchone() is None

async def notify_admin(context, user_id, transaction_id, method):
    from handlers.admin import send_admin_notification
    await send_admin_notification(context, user_id, transaction_id, method)
