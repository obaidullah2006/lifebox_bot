import logging
import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, JobQueue
from config import Config
from handlers.start import start_handler, show_main_menu
from handlers.payment import payment_callback, transaction_handler
from handlers.tasks import tasks_handler, task_callback, handle_screenshot
from handlers.referral import referral_handler, handle_referral_bonus
from handlers.withdraw import withdraw_callback, withdraw_handler
from handlers.admin import admin_handler, admin_callback
from utils.helpers import send_daily_report, calculate_monthly_bonuses

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    application = Application.builder().token(Config.BOT_TOKEN).build()
    job_queue = application.job_queue
    
    # হ্যান্ডলার রেজিস্টার
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("menu", show_main_menu))
    application.add_handler(CommandHandler("admin", admin_handler))
    application.add_handler(CommandHandler("referral", referral_handler))
    
    application.add_handler(CallbackQueryHandler(payment_callback, pattern="^payment_"))
    application.add_handler(CallbackQueryHandler(task_callback, pattern="^task_"))
    application.add_handler(CallbackQueryHandler(withdraw_callback, pattern="^withdraw_"))
    application.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, transaction_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw_handler))
    application.add_handler(MessageHandler(filters.PHOTO, handle_screenshot))
    
    # শেডিউল্ড জবস
    job_queue.run_daily(send_daily_report, time=datetime.time(23, 0), days=(0, 1, 2, 3, 4, 5, 6))
    job_queue.run_monthly(calculate_monthly_bonuses, datetime.time(0, 0), 1)
    
    if os.getenv("RAILWAY_ENVIRONMENT"):
        port = int(os.getenv("PORT", 8443))
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=Config.BOT_TOKEN,
            webhook_url=f"https://{os.getenv('RAILWAY_STATIC_URL')}/{Config.BOT_TOKEN}"
        )
    else:
        application.run_polling()
    
    logger.info("LifeBox Bot started successfully")

if __name__ == "__main__":
    main()
