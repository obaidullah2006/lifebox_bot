from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import db
from models.user import User
from keyboards import get_main_menu_keyboard

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # Check if user referred someone
    referrer_id = None
    if context.args:
        try:
            referrer_id = int(context.args[0])
        except ValueError:
            pass
    
    # Add user to database
    db.add_user(user_id, user.username, user.first_name, user.last_name, referrer_id)
    
    user_model = User(user_id)
    
    if not user_model.is_active:
        await show_activation_prompt(update)
    else:
        await show_main_menu(update)

async def show_activation_prompt(update: Update):
    keyboard = [
        [InlineKeyboardButton("একাউন্ট একটিভ করুন", callback_data="payment_activate")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎯 LifeBox - ইনকাম বটে স্বাগতম!\n\n"
        "⚠️ আপনার একাউন্ট একটিভ নয় ❌\n"
        "ইনকাম করতে হলে আপনাকে প্রথমে একাউন্ট একটিভ করতে হবে।",
        reply_markup=reply_markup
    )

async def show_main_menu(update: Update):
    user = update.effective_user
    user_model = User(user.id)
    
    welcome_text = (
        f"🎉 LifeBox - ইনকাম বটে স্বাগতম {user.first_name}!\n\n"
        f"💰 আপনার ব্যালেন্স: {user_model.balance} পয়েন্ট\n"
        f"👥 রেফারেল: {user_model.referral_count} জন\n"
        f"💎 স্ট্যাটাস: {'একটিভ ✅' if user_model.is_active else 'নন-একটিভ ❌'}\n\n"
        "নিচের মেনু থেকে অপশন সিলেক্ট করুন:"
    )
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu_keyboard()
  )
