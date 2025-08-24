from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import Config

def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📅 Daily Task", callback_data="task_daily")],
        [InlineKeyboardButton("⏰ Time Task", callback_data="task_time")],
        [InlineKeyboardButton("👤 My Account", callback_data="account_info")],
        [InlineKeyboardButton("💳 Withdraw", callback_data="withdraw_request")],
        [InlineKeyboardButton("📝 Contract Work", url=Config.CONTRACT_CHANNEL)],
        [InlineKeyboardButton("📢 Join Telegram", url=Config.JOIN_CHANNEL)]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_payment_keyboard():
    keyboard = [
        [InlineKeyboardButton("📱 বিকাশ", callback_data="payment_bkash")],
        [InlineKeyboardButton("📲 নগদ", callback_data="payment_nagad")],
        [InlineKeyboardButton("🔙 Back", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("👥 Activation Requests", callback_data="admin_activation")],
        [InlineKeyboardButton("💳 Withdraw Requests", callback_data="admin_withdraw")],
        [InlineKeyboardButton("📊 Daily Report", callback_data="admin_daily_report")],
        [InlineKeyboardButton("📈 Monthly Report", callback_data="admin_monthly_report")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings")],
        [InlineKeyboardButton("👤 User Management", callback_data="admin_users")],
        [InlineKeyboardButton("📋 Task Management", callback_data="admin_tasks")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_withdraw_amount_keyboard(user_balance, withdraw_count):
    amounts = []
    min_amount = Config.WITHDRAW_CONDITIONS['withdraw_min'][min(withdraw_count, 2)]
    
    for amount in [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]:
        if amount >= min_amount and amount <= user_balance and amount <= Config.WITHDRAW_CONDITIONS['withdraw_max']:
            amounts.append(InlineKeyboardButton(f"{amount} Points", callback_data=f"withdraw_amount_{amount}"))
    
    # 2 columns per row
    keyboard = [amounts[i:i+2] for i in range(0, len(amounts), 2)]
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_main")])
    
    return InlineKeyboardMarkup(keyboard)

def get_withdraw_method_keyboard():
    keyboard = [
        [InlineKeyboardButton("📱 বিকাশ", callback_data="withdraw_method_bkash")],
        [InlineKeyboardButton("📲 নগদ", callback_data="withdraw_method_nagad")],
        [InlineKeyboardButton("🔙 Back", callback_data="withdraw_back")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_task_types_keyboard():
    keyboard = [
        [InlineKeyboardButton("📅 Daily Tasks", callback_data="task_daily")],
        [InlineKeyboardButton("⏰ Time Tasks", callback_data="task_time")],
        [InlineKeyboardButton("🔙 Back", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_confirmation_keyboard(action, id):
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_{action}_{id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{action}_{id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
