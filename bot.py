import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from deep_translator import GoogleTranslator

TOKEN = "8750644059:AAEA-loCMcUkGH_EU-Zd334E7NikGI0KOf"

# تخزين البطاقات التعليمية لكل مستخدم
user_flashcards = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "مرحباً بك يا دكتور! 🩺✨\n"
        "البوت جاهز لمساعدتك في مراجعة الشيتات وامتحانك غداً.\n"
        "أرسل لي أي نص أو شيت طبي، وسأعطيك أزراراً لكل كلمة لترجمتها وحفظها فوراً!"
    )
    await update.message.reply_text(welcome_text)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_content = update.message.text
    
    # استخراج الكلمات الفريدة من النص
    words = re.findall(r'\b[A-Za-z]{3,}\b', text_content)
    unique_words = list(set([w.lower() for w in words]))[:15]  # أخذ أول 15 كلمة لسرعة وسلاسة الاستجابة

    if not unique_words:
        await update.message.reply_text("لم ألاحظ كلمات إنجليزية واضحة في النص.")
        return

    keyboard = []
    for word in unique_words:
        keyboard.append([InlineKeyboardButton(f"🔍 ترجمة وعرض: {word}", callback_data=f"tr_{word}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "📄 **تم تحليل النص بنجاح!**\nاضغط على أي كلمة أدناه لترجمتها وعرض بطاقتها:",
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("tr_"):
        word = data.replace("tr_", "")
        
        try:
            # ترجمة فورية لأي كلمة في العالم عبر Google Translator
            translation_ar = GoogleTranslator(source='auto', target='ar').translate(word)
            translation_en = f"Medical or general term: {word}"
        except Exception:
            translation_ar = "تعذر الترجمة مؤقتاً"
            translation_en = word

        save_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⭐ حفظ في قائمة الاستذكار (Flashcards)", callback_data=f"save_{word}")]
        ])
        
        msg = (
            f"📌 **بطاقة المراجعة:**\n\n"
            f"🔹 **الوجه الأول (المصطلح/الكلمة):** `{word.capitalize()}`\n"
            f"🔸 **الوجه الثاني (الإنجليزي):** {translation_en}\n"
            f"🔸 **الوجه الثاني (العربي):** {translation_ar}"
        )
        await query.message.reply_text(msg, reply_markup=save_keyboard)
        
    elif data.startswith("save_"):
        word = data.replace("save_", "")
        user_id = query.from_user.id
        
        if user_id not in user_flashcards:
            user_flashcards[user_id] = []
            
        if word not in user_flashcards[user_id]:
            user_flashcards[user_id].append(word)
            
        await update.effective_message.reply_text("✅ **تمت إضافة الكلمة إلى بطاقات الاستذكار بنجاح!** بالتوفيق في الامتحان!")

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(button_callback))

    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
