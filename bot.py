import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = "8750644059:AAEA-loCMcUkGH_EU-Zd334E7NikGI0KOfs"

# تخزين البطاقات التعليمية لكل مستخدم
user_flashcards = {}

# بوادئ ولواحق طبية لاتينية/يونانية للتمييز الذكي
MEDICAL_SUFFIXES = ['itis', 'ology', 'ectomy', 'oscopy', 'pathy', 'emia', 'plasty', 'osis', 'iasis', 'metry', 'graphy', 'gram']
MEDICAL_PREFIXES = ['cardio', 'gastro', 'neuro', 'nephro', 'hepa', 'derm', 'oste', 'arthr', 'pneum', 'hem', 'myo', 'cyst', 'rhin', 'psych', 'arteri', 'ven']

def is_medical_term(word):
    word_lower = word.lower()
    if any(word_lower.endswith(suf) for suf in MEDICAL_SUFFIXES):
        return True
    if any(word_lower.startswith(pref) for pref in MEDICAL_PREFIXES):
        return True
    return False

# قاعدة بيانات موسعة للمصطلحات الطبية والكلمات العادية
DICTIONARY = {
    # مصطلحات طبية / لاتينية
    "cardiology": {"type": "medical", "latin": "Cardiologia", "en": "The study of the heart and its functions.", "ar": "علم القلب وأمراضه"},
    "gastroenteritis": {"type": "medical", "latin": "Gastroenteritis", "en": "Inflammation of the stomach and intestines.", "ar": "التهاب المعدة والأمعاء"},
    "neurology": {"type": "medical", "latin": "Neurologia", "en": "Branch of medicine dealing with the nervous system.", "ar": "علم الأعصاب"},
    "atherosclerosis": {"type": "medical", "latin": "Atherosclerosis", "en": "Build-up of fats in artery walls.", "ar": "تصلب الشرايين"},
    "hypertension": {"type": "medical", "latin": "Hypertensio", "en": "High blood pressure.", "ar": "ارتفاع ضغط الدم"},
    "myocarditis": {"type": "medical", "latin": "Myocarditis", "en": "Inflammation of the heart muscle.", "ar": "التهاب عضلة القلب"},
    
    # كلمات إنجليزية عامة (مثال توضيحي للترجمة العامة)
    "comprises": {"type": "general", "ar": "يتكون من / يشتمل على"},
    "vessels": {"type": "general", "ar": "أوعية (دموية)"},
    "disorders": {"type": "general", "ar": "اضطرابات / أمراض"},
    "common": {"type": "general", "ar": "شائع / متعارف عليه"}
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "مرحباً بك يا دكتور! 🩺✨\n\n"
        "هذا البوت مصمم خصيصاً لمساعدتك في:\n"
        "1. **الترجمة الفورية** لأي كلمة إنجليزية في الشيتات.\n"
        "2. **التعرف الذكي على المصطلحات الطبية** واللاتينية وتحويلها إلى بطاقات استذكار (Flashcards) دقيقة (المصطلح | المعنى الإنجليزي | المعنى العربي).\n\n"
        "أرسل لي أي نص أو شيت طبي الآن لنبدأ!"
    )
    await update.message.reply_text(welcome_text)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_content = update.message.text
    
    # استخراج الكلمات الفريدة من النص
    words = re.findall(r'\b[A-Za-z]{3,}\b', text_content)
    unique_words = list(set([w.lower() for w in words]))

    if not unique_words:
        await update.message.reply_text("لم ألاحظ كلمات إنجليزية واضحة في النص.")
        return

    # بناء أزرار لكل كلمة تم العثور عليها في النص
    keyboard = []
    for word in unique_words[:15]:  # عرض حتى 15 كلمة لترتيب الأزرار
        if is_medical_term(word) or word in DICTIONARY:
            btn_text = f"🩺 مصطلح: {word}" if is_medical_term(word) else f"📖 ترجمة: {word}"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"word_{word}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"🔍 **تم تحليل النص بنجاح!**\nاضغط على أي كلمة أدناه لمعرفة ترجمتها أو تفاصيلها الطبية:",
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("word_"):
        word = data.replace("word_", "")
        
        # التحقق مما إذا كانت مصطلحاً طبياً
        if is_medical_term(word) or (word in DICTIONARY and DICTIONARY[word]["type"] == "medical"):
            info = DICTIONARY.get(word, {
                "latin": word.capitalize(),
                "en": f"Medical term related to {word}.",
                "ar": f"مصطلح طبي تخصصي: {word}"
            })
            
            save_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("⭐ حفظ في قائمة الاستذكار (Flashcards)", callback_data=f"save_{word}")]
            ])
            
            msg = (
                f"📌 **بطاقة المصطلح الطبي:**\n\n"
                f"🔹 **الوجه الأول (المصطلح اللاتيني/الطبي):** `{info.get('latin', word.capitalize())}`\n"
                f"🔸 **الوجه الثاني (الإنجليزي):** {info.get('en', 'N/A')}\n"
                f"🔸 **الوجه الثاني (العربي):** {info.get('ar', 'N/A')}"
            )
            await query.message.reply_text(msg, reply_markup=save_keyboard)
        else:
            # كلمة إنجليزية عامة
            general_info = DICTIONARY.get(word, {"ar": f"معنى إضافي للكلمة: {word}"})
            await query.message.reply_text(f"📖 **ترجمة الكلمة (`{word}`):**\n{general_info['ar']}")
            
    elif data.startswith("save_"):
        word = data.replace("save_", "")
        user_id = query.from_user.id
        
        if user_id not in user_flashcards:
            user_flashcards[user_id] = []
            
        info = DICTIONARY.get(word, {
            "latin": word.capitalize(),
            "en": f"Medical term: {word}",
            "ar": f"مصطلح طبي: {word}"
        })
        
        card = {"term": info.get("latin", word), "en": info.get("en", ""), "ar": info.get("ar", "")}
        if card not in user_flashcards[user_id]:
            user_flashcards[user_id].append(card)
            
        await query.message.reply_text("✅ **تمت إضافة المصطلح إلى بطاقات الاستذكار الخاصة بك بنجاح!**")

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(button_callback))

    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
