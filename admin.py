from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
from config import Config
from database import db
from models.user import User
from keyboards import get_admin_keyboard, get_confirmation_keyboard

async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != Config.ADMIN_ID:
        await update.message.reply_text("⚠️ আপনার Admin এক্সেস নেই!")
        return
    
    await update.message.reply_text(
        "🔧 **Admin Panel** - LifeBox Bot\n\n"
        "নিচ থেকে অপশন সিলেক্ট করুন:",
        reply_markup=get_admin_keyboard(),
        parse_mode="Markdown"
    )

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "admin_activation":
        await show_activation_requests(query)
    elif query.data == "admin_withdraw":
        await show_withdraw_requests(query)
    elif query.data == "admin_daily_report":
        await show_daily_report(query)
    elif query.data.startswith("admin_confirm_"):
        await handle_confirmation(query, context)
    elif query.data.startswith("admin_reject_"):
        await handle_rejection(query, context)

async def show_activation_requests(query):
    requests = db.get_pending_activations()
    
    if not requests:
        await query.edit_message_text("✅ কোন pending activation request নেই")
        return
    
    message = "🔔 **Pending Activation Requests:**\n\n"
    keyboard = []
    
    for req in requests:
        message += f"👤 User: @{req[7]}\n💳 Amount: {req[3]}৳\n📱 Method: {req[4]}\n🔢 TXN ID: {req[2]}\n\n"
        keyboard.append([
            InlineKeyboardButton(f"✅ Confirm {req[0]}", callback_data=f"admin_confirm_act_{req[0]}"),
            InlineKeyboardButton(f"❌ Reject {req[0]}", callback_data=f"admin_reject_act_{req[0]}")
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_back")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")

async def show_withdraw_requests(query):
    requests = db.get_pending_withdrawals()
    
    if not requests:
        await query.edit_message_text("✅ কোন pending withdrawal request নেই")
        return
    
    message = "🔔 **Pending Withdrawal Requests:**\n\n"
    keyboard = []
    
    for req in requests:
        message += f"👤 User: @{req[7]}\n💰 Amount: {req[2]} points\n📱 Method: {req[3]}\n🔢 Account: {req[4]}\n\n"
        keyboard.append([
            InlineKeyboardButton(f"✅ Confirm {req[0]}", callback_data=f"admin_confirm_withdraw_{req[0]}"),
            InlineKeyboardButton(f"❌ Reject {req[0]}", callback_data=f"admin_reject_withdraw_{req[0]}")
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_back")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")

async def handle_confirmation(query, context):
    parts = query.data.split("_")
    action = parts[2]
    request_id = parts[3]
    
    if action == "act":
        cursor = db.conn.cursor()
        cursor.execute("UPDATE transactions SET status = 'approved' WHERE id = ? RETURNING user_id", (request_id,))
        result = cursor.fetchone()
        
        if result:
            user_id = result[0]
            cursor.execute("UPDATE users SET is_active = TRUE WHERE user_id = ?", (user_id,))
            
            # Give referral bonus if applicable
            cursor.execute("SELECT referrer_id FROM users WHERE user_id = ?", (user_id,))
            referrer_result = cursor.fetchone()
            
            if referrer_result and referrer_result[0]:
                referrer_id = referrer_result[0]
                bonus_amount = Config.REFERRAL_BONUS['initial']
                
                cursor.execute('''
                    UPDATE users SET balance = balance + ?, total_earned = total_earned + ? 
                    WHERE user_id = ?
                ''', (bonus_amount, bonus_amount, referrer_id))
                
                # Notify referrer
                try:
                    await context.bot.send_message(
                        chat_id=referrer_id,
                        text=f"🎉 রেফারেল বোনাস!\n\n+{bonus_amount} points\n"
                             f"আপনার রেফারেল একটিভ হয়েছে!"
                    )
                except Exception as e:
                    print(f"Could not notify referrer {referrer_id}: {e}")
            
            db.conn.commit()
            
            # Notify user
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="🎉 **অভিনন্দন! আপনার একাউন্ট একটিভ হয়েছে**\n\n"
                         "✅ এখন আপনি সব ধরনের টাস্ক করতে এবং ইনকাম করতে পারবেন!\n"
                         "💎 প্রথম টাস্ক করে আজই ইনকাম শুরু করুন!"
                )
            except Exception as e:
                print(f"Could not notify user {user_id}: {e}")
            
            await query.edit_message_text(f"✅ User {user_id} activated successfully!")
    
    elif action == "withdraw":
        cursor = db.conn.cursor()
        cursor.execute("UPDATE withdrawals SET status = 'approved' WHERE id = ?", (request_id,))
        db.conn.commit()
        
        await query.edit_message_text(f"✅ Withdrawal request {request_id} approved!")

async def send_admin_notification(context, user_id, transaction_id, method):
    user = User(user_id)
    message = (
        f"🔔 **নতুন একটিভেশন রিকুয়েস্ট**\n\n"
        f"👤 User: @{user.username}\n"
        f"🆔 ID: {user_id}\n"
        f"💳 Method: {method.upper()}\n"
        f"🔢 TXN ID: {transaction_id}\n\n"
        f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"admin_confirm_act_{transaction_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_act_{transaction_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=Config.ADMIN_ID,
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_daily_report(query):
    cursor = db.conn.cursor()
    
    # Get daily stats
    cursor.execute('''
        SELECT 
            COUNT(*) as total_users,
            SUM(CASE WHEN is_active THEN 1 ELSE 0 END) as active_users,
            COUNT(CASE WHEN date(created_at) = date('now') THEN 1 END) as new_today,
            SUM(balance) as total_balance,
            COUNT(CASE WHEN date(created_at) = date('now') AND is_active THEN 1 END) as activated_today
        FROM users
    ''')
    stats = cursor.fetchone()
    
    cursor.execute('''
        SELECT COUNT(*) FROM transactions 
        WHERE date(created_at) = date('now') AND status = 'approved'
    ''')
    approved_transactions = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COUNT(*), SUM(amount) FROM withdrawals 
        WHERE date(created_at) = date('now') AND status = 'approved'
    ''')
    withdrawal_stats = cursor.fetchone()
    
    report_message = (
        f"📊 **Daily Report - {datetime.now().strftime('%Y-%m-%d')}**\n\n"
        f"👥 Total Users: {stats[0]}\n"
        f"✅ Active Users: {stats[1]}\n"
        f"🆕 New Today: {stats[2]}\n"
        f"🎯 Activated Today: {stats[4]}\n"
        f"💰 Total Balance: {stats[3]} points\n"
        f"💳 Approvals Today: {approved_transactions}\n"
        f"📤 Withdrawals: {withdrawal_stats[0]} requests\n"
        f"💸 Withdrawn Today: {withdrawal_stats[1] or 0} points\n\n"
        f"📈 System Status: ✅ Operational"
    )
    
    await query.edit_message_text(report_message, parse_mode="Markdown")
