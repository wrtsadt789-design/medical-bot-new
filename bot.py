import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# تفعيل نظام تسجيل الأخطاء لمعرفة ما يحدث في السيرفر
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# توكن البوت الجديد ومعرف المالك
TOKEN = "8750644059:AAEA-loCMcUkGH_EU-Zd334E7NikGI0KOf"
OWNER_ID = 8201127054


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
  # التأكد من أن الرسالة من المالك فقط
  if update.effective_user.id != OWNER_ID:
    return

  text = update.message.text

  if text == "/start":
    await update.message.reply_text(
        "مرحباً بك يا دكتور! 🩺\nأنا بوت الاستذكار الطبي والمصطلحات.\nأرسل لي أي"
        " نص أو شيت طبي، وسأقوم بتحويله إلى أزرار تفاعلية فورية وترجمته وحفظه"
        " لك."
    )
    return

  # الرد المؤقت لتأكيد استلام النصوص الطبية
  await update.message.reply_text(
      f"تم استلام النص الطبي بنجاح 📋:\n\n{text}\n\nجارٍ معالجة المصطلحات"
      " وإنشاء الأزرار..."
  )


def main():
  # بناء وتشغيل تطبيق البوت
  app = ApplicationBuilder().token(TOKEN).build()

  # استقبال جميع النصوص الواردة
  app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
  app.add_handler(MessageHandler(filters.COMMAND, handle_message))

  print("Medical Bot is running successfully...")
  app.run_polling()


if __name__ == "__main__":
  main()
