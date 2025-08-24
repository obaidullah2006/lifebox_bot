from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, JobQueue
from datetime import datetime, timedelta
from config import Config
from database import db
from models.user import User
from keyboards import get_task_types_keyboard

async def tasks_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_model = User(user.id)
    
    if not user_model.is_active:
        await update.message.reply_text(
            "⚠️ টাস্ক করতে চাইলে প্রথমে একাউন্ট একটিভ করুন!\n"
            "একাউন্ট একটিভ না করলে টাস্ক করতে পারবেন না।"
        )
        return
    
    await update.message.reply_text(
        "🎯 টাস্ক সেকশন\n\n"
        "নিচ থেকে টাস্কের ধরন সিলেক্ট করুন:",
        reply_markup=get_task_types_keyboard()
    )

async def task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "task_daily":
        await show_daily_tasks(query)
    elif query.data == "task_time":
        await show_time_tasks(query)
    elif query.data.startswith("task_start_"):
        task_id = int(query.data.split("_")[2])
        await start_task(query, context, task_id)
    elif query.data.startswith("task_submit_"):
        task_id = int(query.data.split("_")[2])
        await submit_task(query, context, task_id)

async def show_daily_tasks(query):
    cursor = db.conn.cursor()
    cursor.execute('''
        SELECT * FROM tasks 
        WHERE task_type = 'daily' AND is_active = TRUE 
        AND expires_at > datetime('now')
        ORDER BY created_at DESC
    ''')
    tasks = cursor.fetchall()
    
    if not tasks:
        await query.edit_message_text(
            "📅 আজকের Daily Tasks\n\n"
            "⚠️ আজকে কোন টাস্ক নেই। পরে চেক করুন!"
        )
        return
    
    message = "📅 আজকের Daily Tasks:\n\n"
    keyboard = []
    
    for task in tasks:
        message += f"🎯 {task[2]}\n📝 {task[3]}\n💰 {task[4]} Points\n\n"
        keyboard.append([InlineKeyboardButton(
            f"Start Task - {task[4]} Points", 
            callback_data=f"task_start_{task[0]}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup)

async def start_task(query, context: ContextTypes.DEFAULT_TYPE, task_id: int):
    user_id = query.from_user.id
    cursor = db.conn.cursor()
    
    # Check if already completed
    cursor.execute('''
        SELECT * FROM completed_tasks 
        WHERE user_id = ? AND task_id = ?
    ''', (user_id, task_id))
    
    if cursor.fetchone():
        await query.edit_message_text(
            "⚠️ আপনি এই টাস্কটি ইতিমধ্যেই সম্পন্ন করেছেন!\n\n"
            "একটি টাস্ক শুধুমাত্র একবারই করা যাবে।"
        )
        return
    
    # Get task details
    cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
    task = cursor.fetchone()
    
    if not task:
        await query.edit_message_text("❌ টাস্কটি পাওয়া যায়নি!")
        return
    
    context.user_data['current_task'] = task_id
    context.user_data['task_start_time'] = datetime.now()
    
    message = (
        f"🎯 টাস্ক: {task[2]}\n\n"
        f"📝 বর্ণনা: {task[3]}\n"
        f"💰 পয়েন্ট: {task[4]}\n"
        f"🔗 লিংক: {task[5]}\n\n"
    )
    
    if task[6]:  # requires_screenshot
        message += "📸 এই টাস্কের জন্য স্ক্রিনশট জমা দিতে হবে\n"
        message += "⚠️ লিংক visit করার 5 সেকেন্ড পর Submit অপশন আসবে\n\n"
        message += "লিংক visit করুন এবং কাজটি সম্পন্ন করুন:"
    else:
        message += "✅ এই টাস্কের জন্য স্ক্রিনশট প্রয়োজন নেই\n"
        message += "⚠️ লিংক visit করার 5 সেকেন্ড পর Submit অপশন আসবে\n\n"
        message += "লিংক visit করুন এবং কাজটি সম্পন্ন করুন:"
    
    keyboard = [
        [InlineKeyboardButton("🔗 Visit Link", url=task[5])],
        [InlineKeyboardButton("⏰ 5s Wait for Submit", callback_data=f"task_wait_{task_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup)

async def handle_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo and 'current_task' in context.user_data:
        photo = update.message.photo[-1]
        file_id = photo.file_id
        user_id = update.effective_user.id
        task_id = context.user_data['current_task']
        
        # Save screenshot info
        cursor = db.conn.cursor()
        cursor.execute('''
            INSERT INTO screenshots (user_id, task_id, file_id)
            VALUES (?, ?, ?)
        ''', (user_id, task_id, file_id))
        
        cursor.execute('''
            INSERT INTO completed_tasks (user_id, task_id, screenshot_id, status)
            VALUES (?, ?, ?, 'pending')
        ''', (user_id, task_id, file_id))
        
        db.conn.commit()
        
        # Schedule points addition after 30 minutes
        context.job_queue.run_once(
            add_task_points, 
            1800,  # 30 minutes in seconds
            data={'user_id': user_id, 'task_id': task_id, 'file_id': file_id}
        )
        
        await update.message.reply_text(
            "✅ স্ক্রিনশট received! টাস্ক under review...\n\n"
            "⏳ 30 minutes পর পয়েন্ট add করা হবে"
        )

async def add_task_points(context: ContextTypes.DEFAULT_TYPE):
    job_data = context.job.data
    user_id = job_data['user_id']
    task_id = job_data['task_id']
    
    # Get task points
    cursor = db.conn.cursor()
    cursor.execute("SELECT points FROM tasks WHERE id = ?", (task_id,))
    task = cursor.fetchone()
    
    if not task:
        return
    
    points = task[0]
    
    # Add points to user
    cursor.execute('''
        UPDATE users SET balance = balance + ?, total_earned = total_earned + ? 
        WHERE user_id = ?
    ''', (points, points, user_id))
    
    # Update completed task status
    cursor.execute('''
        UPDATE completed_tasks SET status = 'approved', points_awarded = TRUE 
        WHERE user_id = ? AND task_id = ?
    ''', (user_id, task_id))
    
    # Update screenshot status
    cursor.execute('''
        UPDATE screenshots SET status = 'approved', verified_at = datetime('now')
        WHERE user_id = ? AND task_id = ?
    ''', (user_id, task_id))
    
    db.conn.commit()
    
    # Notify user
    await context.bot.send_message(
        chat_id=user_id,
        text=f"✅ টাস্ক verified! {points} points added to your account!"
    )
