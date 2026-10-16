import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from deep_translator import GoogleTranslator

TOKEN = "8750644059:AAEA-loCMcUkGH_EU-Zd334E7NikGI0KOfs"

user_flashcards = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "مرحباً بك يا دكتور! 🩺✨\n"
        "أرسل لي النص أو الشيت، وسأعرضه لك كاملاً بحيث تكون **كل كلمة زراً خاصاً بها** في مكانها الصحيح لتضغط عليها فوراً!"
    )
    await update.message.reply_text(welcome_text)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_content = update.message.text
    
    # استخراج الكلمات من النص مع الحفاظ على ترتيبها
    words = re.findall(r'\b[A-Za-z]{3,}\b', text_content)
    
    if not words:
        await update.message.reply_text("لم ألاحظ كلمات إنجليزية واضحة في النص.")
        return

    # بناء مصفوفة أزرار (شبكة) تشبه شكل النص، بحيث كل أفقياً عدة كلمات بجانب بعضها
    keyboard = []
    row = []
    
    for i, word in enumerate(words[:30]):  # عرض حتى 30 كلمة لكي لا يصبح الزر طويلاً جداً
        # جعل كل كلمة زراً مستقلاً بذاته
        row.append(InlineKeyboardButton(word, callback_data=f"w_{word}"))
        
        # كل 3 أو 4 كلمات نضعها في سطر واحد (مربعات بجانب بعضها)
        if len(row) == 3:
            keyboard.append(row)
            row = []
            
    if row:  # إضافة البقية إن وجدت
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📄 **إليك الشيت كأزرار تفاعلية:**\nاضغط على أي كلمة في مكانها لتظهر لك ترجمتها فوراً:",
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("w_"):
        word = data.replace("w_", "")
        
        try:
            translation_ar = GoogleTranslator(source='auto', target='ar').translate(word)
        except Exception:
            translation_ar = "تعذر الترجمة مؤقتاً"
            
        msg = (
            f"📌 **الكلمة:** `{word.capitalize()}`\n"
            f"🔹 **الترجمة العربية:** {translation_ar}"
        )
        
        # إرسال الترجمة في رسالة تحت الأزرار مباشرة دون أن تغادر النص
        await query.message.reply_text(msg)

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(button_callback))

    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
