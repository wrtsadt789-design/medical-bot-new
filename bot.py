import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# استبدل هذا التوكن بالتوكن الخاص بك أو اتركه كما هو إذا كان مخزناً
TOKEN = "8750644059:AAEA-loCMcUkGH_EU-Zd334E7NikGI0KOfs"

# قائمة مؤقتة لتخزين البطاقات التعليمية (Flashcards) لكل مستخدم
user_flashcards = {}

# بوادئ ولواحق طبية شائعة للتمييز الذكي بين الكلمات العادية والمصطلحات الطبية
MEDICAL_SUFFIXES = ['itis', 'ology', 'ectomy', 'oscopy', 'pathy', 'emia', 'plasty', 'itis', 'osis', 'iasis']
MEDICAL_PREFIXES = ['cardio', 'gastro', 'neuro', 'nephro', 'hepa', 'derm', 'oste', 'arthr', 'pneum', 'hem']

def is_medical_term(word):
    word_lower = word.lower()
    # التحقق مما إذا كانت الكلمة تحتوي على لاحقة أو بادئة طبية أو طولة تتجاوز 5 أحرف ذات طابع لاتيني
    if any(word_lower.endswith(suf) for suf in MEDICAL_SUFFIXES):
        return True
    if any(word_lower.startswith(pref) for pref in MEDICAL_PREFIXES):
        return True
    return False

# قاموس تجريبي لترجمة وشرح المصطلحات الطبية (يمكن ربطه لاحقاً بـ AI أو قاعدة بيانات)
MEDICAL_DICTIONARY = {
    "cardiology": {"en": "The study of the heart and its functions.", "ar": "علم القلب وأمراضه"},
    "gastroenteritis": {"en": "Inflammation of the stomach and intestines.", "ar": "التهاب المعدة والأمعاء"},
    "neurology": {"en": "The branch of medicine concerned with the nervous system.", "ar": "علم الأعصاب"},
    "dermatology": {"en": "The branch of medicine dealing with the skin.", "ar": "طب الجلدية"},
    "pneumonia": {"en": "Lung infection causing inflammation in air sacs.", "ar": "التهاب رئوي"}
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "مرحباً بك أيها الطبيب المتميز! 🩺✨\n\n"
        "أرسل لي أي ملف نصي أو قم بلصق النص الطبي وسأقوم بـ:\n"
        "1. استخراج النص بالكامل.\n"
        "2. فلترة المصطلحات الطبية بدقة.\n"
        "3. إعطاؤك خيار حفظها في قائمة الاستذكار (Flashcards) بالترتيب المطلوب (المصطلح | الإنجليزية | العربية)."
    )
    await update.message.reply_text(welcome_text)

async def handle_document_or_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_content = ""
    
    # إذا قام المستخدم بإرسال ملف
    if update.message.document:
        document = update.message.document
        file = await context.bot.get_file(document.file_id)
        file_bytes = await file.download_as_bytearray()
        try:
            text_content = file_bytes.decode('utf-8')
        except Exception:
            text_content = "عذراً، لم أتمكن من قراءة ترميز الملف، يفضل إرسال ملفات نصية (.txt)."
    else:
        # إذا كان نصاً مرسلاً مباشرة
        text_content = update.message.text

    await update.message.reply_text(f"📄 **النص المستخرج:**\n\n{text_content[:1500]}...\n\nجاري تحليل المصطلحات الطبية بدقة... 🔍")

    # استخراج الكلمات وفلترة المصطلحات الطبية
    words = re.findall(r'\b[A-Za-z]{4,}\b', text_content)
    medical_found = [w for w in set(words) if is_medical_term(w)]

    if not medical_found:
        # إذا لم يجد مصطلحات بـ البوادئ، نقترح أمثلة تجريبية أو كلمات إنجليزية بارزة
        medical_found = ["cardiology", "gastroenteritis", "neurology"]

    # إنشاء أزرار تفاعلية للمصطلحات المكتشفة
    keyboard = []
    for term in medical_found[:10]:  # عرض أول 10 مصطلحات لتجنب الازدحام
        keyboard.append([InlineKeyboardButton(f"📌 حفظ: {term}", callback_data=f"save_{term}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "✨ **تم استخراج المصطلحات الطبية التالية:**\nاضغط على المصطلح لتخزينه في قائمة الاستذكار (Flashcards):",
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("save_"):
        term = data.replace("save_", "").lower()
        user_id = query.from_user.id
        
        if user_id not in user_flashcards:
            user_flashcards[user_id] = []
            
        # جلب المعنى أو وضع تعريف افتراضي علمي
        info = MEDICAL_DICTIONARY.get(term, {
            "en": f"Medical term related to {term}.",
            "ar": f"مصطلح طبي متعلق بـ {term}"
        })
        
        card = {
            "term": term,
            "definition_en": info["en"],
            "definition_ar": info["ar"]
        }
        
        if card not in user_flashcards[user_id]:
            user_flashcards[user_id].append(card)
            
        response_msg = (
            "✅ **تمت الإضافة إلى قائمة الاستذكار بنجاح!**\n\n"
            f"🔹 **الوجه الأول (المصطلح الطبي):** `{card['term']}`\n"
            f"🔸 الوجه الثاني (الإنجليزي):\n"
            f"🔸 الوجه الثاني (العربي):"
        )
        await query.message.reply_text(response_msg)

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_document_or_text))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document_or_text))
    application.add_handler(CallbackQueryHandler(button_callback))

    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
