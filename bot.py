import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = "8750644059:AAEA-loCMcUkGH_EU-Zd334E7NikGI0KOfs"

# قاموس أساسي سريع
MEDICAL_DICT = {
    "cardiovascular": "قلبي وعائي",
    "system": "جهاز / نظام",
    "comprises": "يتكون من / يشتمل على",
    "heart": "القلب",
    "blood": "دم",
    "vessels": "أوعية",
    "cardiology": "علم القلب",
    "medical": "طبي",
    "sternum": "عظمة القص"
}

# تحليل ذكي للواحق الطبية اللاتينية لمعرفة أي مصطلح جديد فوراً
MEDICAL_SUFFIXES = {
    "itis": "التهاب (Inflammation)",
    "ology": "علم أو دراسة (Study of)",
    "ectomy": "استئصال جراحي (Surgical removal)",
    "oscopy": "منظار / فحص بالمنظار (Examination)",
    "pathy": "اعتلال / مرض (Disease/Disorder)",
    "emia": "حالة في الدم (Blood condition)",
    "osis": "حالة مرضية / مزمنة (Abnormal condition)",
    "plasty": "إصلاح جراحي / ترقيع (Surgical repair)",
    "algia": "ألم (Pain)"
}

user_flashcards = {}

def analyze_medical_term(word):
    word_lower = word.lower()
    
    # 1. البحث في القاموس المباشر أولاً
    if word_lower in MEDICAL_DICT:
        return MEDICAL_DICT[word_lower]
        
    # 2. التحليل الذكي للواحق اللاتينية والطبية للمصطلحات الجديدة
    for suffix, meaning in MEDICAL_SUFFIXES.items():
        if word_lower.endswith(suffix):
            # استخراج الجذر لمعرفة معناه التقديري
            root = word_lower[:-len(suffix)]
            return f"مصطلح طبي (لاحقة {suffix}): يشير إلى {meaning} في منطقة ({root})"
            
    return "مصطلح تخصصي / تشريحي"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "مرحباً بك يا دكتور! 🩺✨\n"
        "البوت الآن مبرمج بـ **التحليل الذكي للمصطلحات اللاتينية والطبية**، ولن يعتمد فقط على القاموس!\n\n"
        "📌 **المميزات المتاحة:**\n"
        "• أرسل أي شيت وسأرسله لك كاملاً مقسماً كأزرار شبكية.\n"
        "• يحلل أي مصطلح طبي جديد تلقائياً بناءً على قواعده اللاتينية.\n"
        "• لإضافة بطاقة استذكارية: `add: المصطلح | التعريف`\n"
        "• لمراجعة البطاقات: `/review`"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_content = update.message.text
    user_id = update.message.from_user.id
    
    # إضافة بطاقة استذكار
    if text_content.lower().startswith("add:"):
        try:
            parts = text_content.replace("add:", "").split("|")
            if len(parts) == 2:
                term = parts[0].strip()
                definition = parts[1].strip()
                if user_id not in user_flashcards:
                    user_flashcards[user_id] = []
                user_flashcards[user_id].append({"term": term, "definition": definition})
                await update.message.reply_text(f"✅ تم إضافة بطاقة الاستذكار:\n📌 **{term}** ➡️ {definition}")
                return
        except Exception:
            pass

    # معالجة الشيت النصي وإرساله كاملاً مقسماً
    words = re.findall(r'\b[A-Za-z]{3,}\b', text_content)
    if not words:
        await update.message.reply_text("لم ألاحظ كلمات إنجليزية واضحة.")
        return

    chunk_size = 30
    for i in range(0, len(words), chunk_size):
        chunk = words[i:i + chunk_size]
        keyboard = []
        row = []
        for word in chunk:
            row.append(InlineKeyboardButton(word, callback_data=f"w_{word}"))
            if len(row) == 3:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        reply_markup = InlineKeyboardMarkup(keyboard)
        part_num = (i // chunk_size) + 1
        
        await update.message.reply_text(
            f"📄 **الجزء ({part_num}) من الشيت الكامل:**\nاضغط على أي كلمة للتحليل والترجمة:",
            reply_markup=reply_markup
        )

async def review_flashcards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    cards = user_flashcards.get(user_id, [])
    if not cards:
        await update.message.reply_text("📭 ليس لديك بطاقات مضافة. أضف بـ: `add: المصطلح | التعريف`", parse_mode="Markdown")
        return
        
    review_text = "🧠 **بطاقات الاستذكار الخاصة بك:\n\n"
    for idx, card in enumerate(cards, 1):
        review_text += f"{idx}. 📌 ** ➡️ {card['definition']}\n"
    await update.message.reply_text(review_text, parse_mode="Markdown")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("w_"):
        word = data.replace("w_", "")
        # استخدام التحليل الذكي الشامل لأي كلمة جديدة أو قديمة
        translation_ar = analyze_medical_term(word)
            
        msg = (
            f"📌 **المصطلح:** `{word}`\n"
            f"🔹 **التحليل والترجمة الطبية:** {translation_ar}"
        )
        await query.message.reply_text(msg)

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("review", review_flashcards))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(button_callback))

    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
