from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import Config
from database import db
from models.user import User
from keyboards import get_withdraw_amount_keyboard, get_withdraw_method_keyboard

async def withdraw_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_model = User(user.id)
    
    if not user_model.is_active:
        await query.edit_message_text(
            "⚠️ উত্তোলন করতে চাইলে প্রথমে একাউন্ট একটিভ করুন!\n"
            "একাউন্ট একটিভ না করলে উত্তোলন করতে পারবেন না।"
        )
        return
    
    # Check minimum referrals
    if user_model.referral_count < Config.WITHDRAW_CONDITIONS['min_referrals']:
        await query.edit_message_text(
            f"⚠️ উত্তোলনের শর্ত পূরণ হয়নি!\n\n"
            f"উত্তোলন করতে最少 {Config.WITHDRAW_CONDITIONS['min_referrals']}টি রেফারেল প্রয়োজন\n"
            f"আপনার রেফারেল: {user_model.referral_count}টি\n\n"
            f"রেফারেল বাড়ানোর জন্য /referral কমান্ড ব্যবহার করুন"
        )
        return
    
    if query.data == "withdraw_request":
        await show_withdraw_amounts(query, user_model)
    
    elif query.data.startswith("withdraw_amount_"):
        amount = int(query.data.split("_")[2])
        context.user_data['withdraw_amount'] = amount
        await show_withdraw_methods(query)
    
    elif query.data.startswith("withdraw_method_"):
        method = query.data.split("_")[2]
        context.user_data['withdraw_method'] = method
        await ask_for_account_number(query)

async def show_withdraw_amounts(query, user_model):
    withdraw_count = user_model.withdraw_count
    await query.edit_message_text(
        f"💳 উত্তোলন\n\n"
        f"💰 আপনার ব্যালেন্স: {user_model.balance} points\n"
        f"📊 উত্তোলন সংখ্যা: {withdraw_count}\n\n"
        f"⚠️ সর্বনিম্ন উত্তোলন: {Config.WITHDRAW_CONDITIONS['withdraw_min'][min(withdraw_count, 2)]} points\n"
        f"⚠️ সর্বোচ্চ উত্তোলন: {Config.WITHDRAW_CONDITIONS['withdraw_max']} points\n\n"
        f"কত পয়েন্ট উত্তোলন করতে চান?",
        reply_markup=get_withdraw_amount_keyboard(user_model.balance, withdraw_count)
    )

async def show_withdraw_methods(query):
    await query.edit_message_text(
        "💳 উত্তোলন মাধ্যম选择\n\n"
        "কিসের মাধ্যমে উত্তোলন করতে চান?",
        reply_markup=get_withdraw_method_keyboard()
    )

async def ask_for_account_number(query):
    await query.edit_message_text(
        "📱 একাউন্ট নম্বর\n\n"
        "আপনার একাউন্ট নম্বরটি পাঠান:\n\n"
        "⚠️格式: 01XXXXXXXXX"
    )

async def withdraw_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    account_number = update.message.text.strip()
    
    if 'withdraw_amount' in context.user_data and 'withdraw_method' in context.user_data:
        amount = context.user_data['withdraw_amount']
        method = context.user_data['withdraw_method']
        
        user_model = User(user_id)
        
        # Validate account number
        if not account_number.startswith('01') or len(account_number) != 11 or not account_number.isdigit():
            await update.message.reply_text(
                "❌ একাউন্ট নম্বরটি সঠিক格式ではありません!\n\n"
                "⚠️格式: 01XXXXXXXXX (11位数字)\n"
                "আবার চেষ্টা করুন:"
            )
            return
        
        # Check balance
        if amount > user_model.balance:
            await update.message.reply_text(
                "❌ আপনার পর্যাপ্ত ব্যালেন্স নেই!\n\n"
                f"💰 আপনার ব্যালেন্স: {user_model.balance} points\n"
                f"💳 উত্তোলন amount: {amount} points\n\n"
                "কম amount সিলেক্ট করুন:"
            )
            return
        
        # Create withdrawal request
        cursor = db.conn.cursor()
        cursor.execute('''
            INSERT INTO withdrawals (user_id, amount, method, account_number)
            VALUES (?, ?, ?, ?)
        ''', (user_id, amount, method, account_number))
        
        # Deduct balance
        cursor.execute('''
            UPDATE users SET balance = balance - ?, withdraw_count = withdraw_count + 1 
            WHERE user_id = ?
        ''', (amount, user_id))
        
        db.conn.commit()
        
        # Notify admin
        await notify_admin_withdrawal(context, user_id, amount, method, account_number)
        
        await update.message.reply_text(
            f"✅ উত্তোলন রিকুয়েস্ট গ্রহণ করা হয়েছে!\n\n"
            f"💰 Amount: {amount} points\n"
            f"📱 Method: {method.upper()}\n"
            f"🔢 Account: {account_number}\n\n"
            f"⏳ 24 ঘন্টার মধ্যে processed হবে\n"
            f"📞 কোনো problem হলে এডমিনের সাথে যোগাযোগ করুন"
        )
        
        # Clear context
        context.user_data.pop('withdraw_amount', None)
        context.user_data.pop('withdraw_method', None)

async def notify_admin_withdrawal(context, user_id, amount, method, account_number):
    user = User(user_id)
    
    message = (
        f"🔔 নতুন উত্তোলন রিকুয়েস্ট!\n\n"
        f"👤 User: @{user.username}\n"
        f"🆔 ID: {user_id}\n"
        f"💰 Amount: {amount} points\n"
        f"📱 Method: {method.upper()}\n"
        f"🔢 Account: {account_number}\n"
        f"📊 উত্তোলন সংখ্যা: {user.withdraw_count + 1}\n\n"
        f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"admin_confirm_withdraw_{user_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_withdraw_{user_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=Config.ADMIN_ID,
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
