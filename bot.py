import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = "8750644059:AAEA-loCMcUkGH_EU-Zd334E7NikGI0KOfs"

# قاموس سريع للمصطلحات الأساسية (بالعربي والإنجليزي)
MEDICAL_DICT = {
    "cardiovascular": {
        "type": "medical", 
        "en_term": "Cardiovascular System",
        "breakdown": "Prefix/Root: Cardio (Heart / قلب) + Vascul (Vessel / وعاء)",
        "meaning_ar": "جهاز القلب والأوعية الدموية",
        "meaning_en": "Relating to the heart and blood vessels"
    },
    "system": {"type": "normal", "en_term": "System", "meaning_ar": "جهاز / نظام", "meaning_en": "System"},
    "comprises": {"type": "normal", "en_term": "Comprises", "meaning_ar": "يتكون من / يشتمل على", "meaning_en": "Consists of / Includes"},
    "heart": {"type": "normal", "en_term": "Heart", "meaning_ar": "القلب", "meaning_en": "Heart"},
    "blood": {"type": "normal", "en_term": "Blood", "meaning_ar": "الدم", "meaning_en": "Blood"},
    "vessels": {"type": "normal", "en_term": "Vessels", "meaning_ar": "الأوعية الدموية", "meaning_en": "Blood vessels"},
    "cardiology": {
        "type": "medical", 
        "en_term": "Cardiology",
        "breakdown": "Root: Cardio (Heart / قلب) + Suffix: -ology (Study of / علم)",
        "meaning_ar": "علم القلب وتخصص أمراضه",
        "meaning_en": "The study and treatment of heart disorders"
    },
    "medical": {"type": "normal", "en_term": "Medical", "meaning_ar": "طبي", "meaning_en": "Medical"},
    "sternum": {
        "type": "medical", 
        "en_term": "Sternum",
        "breakdown": "Anatomical Term / مصطلح تشريعي أساسي",
        "meaning_ar": "عظمة القص (في القفص الصدري)",
        "meaning_en": "The breastbone"
    }
}

# لواحق طبية للتحليل (عربي وإنجليزي)
MEDICAL_SUFFIXES = {
    "itis": {"ar": "التهاب", "en": "Inflammation"},
    "ology": {"ar": "علم أو دراسة", "en": "Study of"},
    "ectomy": {"ar": "استئصال جراحي", "en": "Surgical removal"},
    "oscopy": {"ar": "فحص بالمنظار", "en": "Examination using a scope"},
    "pathy": {"ar": "اعتلال أو مرض", "en": "Disease / Disorder"},
    "emia": {"ar": "حالة مرضية في الدم", "en": "Blood condition"},
    "osis": {"ar": "حالة مرضية مزمنة", "en": "Abnormal condition"},
    "plasty": {"ar": "إصلاح أو ترقيع جراحي", "en": "Surgical repair"},
    "algia": {"ar": "ألم", "en": "Pain"}
}

user_flashcards = {}
user_last_texts = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "مرحباً بك يا دكتور! 🩺✨\n"
        "البوت جاهز تماماً لتقديم الترجمة الطبية المزدوجة (عربي وإنجليزي) بشكل منسق واحترافي.\n\n"
        "أرسل شيتك لنبدأ المراجعة الفورية!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_content = update.message.text
    user_id = update.message.from_user.id
    
    if text_content.lower().startswith("add:"):
        try:
            parts = text_content.replace("add:", "").split("|")
            if len(parts) == 2:
                term = parts[0].strip()
                definition = parts[1].strip()
                if user_id not in user_flashcards:
                    user_flashcards[user_id] = []
                user_flashcards[user_id].append({"term": term, "definition": definition})
                await update.message.reply_text(f"✅ تم حفظ البطاقة بنجاح:\n📌 **{term}**\n📖 {definition}")
                return
        except Exception:
            pass

    user_last_texts[user_id] = text_content
    words = re.findall(r'\b[A-Za-z]{3,}\b', text_content)
    
    if not words:
        await update.message.reply_text("لم ألاحظ كلمات إنجليزية واضحة في النص.")
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
            f"📄 **الجزء ({part_num}) من الشيت:**",
            reply_markup=reply_markup
        )

async def review_flashcards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    cards = user_flashcards.get(user_id, [])
    if not cards:
        await update.message.reply_text("📭 ليس لديك بطاقات استذكار مضافة حتى الآن.", parse_mode="Markdown")
        return
        
    review_text = "🧠 **قائمة بطاقات الاستذكار الخاصة بك (عربي / إنجليزي):\n\n"
    for idx, card in enumerate(cards, 1):
        review_text += f"{idx}. 📌 **\n    📖 {card['definition']}\n\n"
    await update.message.reply_text(review_text, parse_mode="Markdown")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    if data.startswith("w_"):
        word = data.replace("w_", "")
        word_lower = word.lower()
        
        analysis_text = ""
        flashcard_definition = ""
        
        if word_lower in MEDICAL_DICT:
            info = MEDICAL_DICT[word_lower]
            if info["type"] == "medical":
                analysis_text = (
                    f"🩺 **المصطلح الطبي / Medical Term:** `{info['en_term']}`\n\n"
                    f"⚙️ **التفكيك / Breakdown:**\n{info['breakdown']}\n\n"
                    f"🇸🇦 **المعنى بالعربي:** {info['meaning_ar']}\n"
                    f"🇬🇧 **Meaning in English:** {info['meaning_en']}"
                )
                flashcard_definition = f"🇸🇦 {info['meaning_ar']} | 🇬🇧 {info['meaning_en']}"
            else:
                analysis_text = (
                    f"📌 **الكلمة / Word:** `{info['en_term']}`\n\n"
                    f"🇸🇦 **الترجمة العربية:** {info['meaning_ar']}\n"
                    f"🇬🇧 **English Meaning:** {info['meaning_en']}"
                )
                flashcard_definition = f"🇸🇦 {info['meaning_ar']} | 🇬🇧 {info['meaning_en']}"
        else:
            # فحص اللواحق الطبية تلقائياً
            found_suffix = None
            for suffix, details in MEDICAL_SUFFIXES.items():
                if word_lower.endswith(suffix):
                    found_suffix = (suffix, details)
                    break
            
            if found_suffix:
                root = word_lower[:-len(found_suffix[0])]
                analysis_text = (
                    f"🩺 **مصطلح طبي تحليل / Medical Term:** `{word.capitalize()}`\n\n"
                    f"⚙️ **التفكيك / Breakdown:**\n• اللاحقة / Suffix: `{found_suffix[0]}`\n• الجذر / Root: `{root}`\n\n"
                    f"🇸🇦 **المعنى بالعربي:** يشير إلى ({found_suffix['details']['ar']}) في منطقة ({root})\n"
                    f"🇬🇧 **Meaning in English:** Refers to {found_suffix['details']['en']} related to ({root})"
                )
                flashcard_definition = f"🇸🇦 {found_suffix['details']['ar']} ({root}) | 🇬🇧 {found_suffix['details']['en']}"
            else:
                analysis_text = (
                    f"📌 **الكلمة / Word:** `{word.capitalize()}`\n\n"
                    f"🇸🇦 **الترجمة العربية:** ترجمة تفصيلية للكلمة\n"
                    f"🇬🇧 **English Definition:** General medical/study term"
                )
                flashcard_definition = f"🇸🇦 ترجمة المصطلح | 🇬🇧 Definition"

        # حفظ النص المؤقت للبطاقة في context data للزر
        context.user_data[f'temp_card_{word}'] = flashcard_definition

        keyboard = [
            [
                InlineKeyboardButton("⭐ إضافة إلى قائمة الاستذكار", callback_data=f"save_{word}"),
                InlineKeyboardButton("📖 العودة إلى القراءة", callback_data="back_to_read")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.reply_text(analysis_text, reply_markup=reply_markup, parse_mode="Markdown")
        
    elif data.startswith("save_"):
        term = data.replace("save_", "")
        definition = context.user_data.get(f'temp_card_{term}', "🇸🇦 ترجمة طبية | 🇬🇧 Medical Definition")
        
        if user_id not in user_flashcards:
            user_flashcards[user_id] = []
            
        if not any(card['term'].lower() == term.lower() for card in user_flashcards[user_id]):
            user_flashcards[user_id].append({"term": term, "definition": definition})
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text(
                f"✅ **تم الحفظ في قائمة الاستذكار بنجاح!**\n\n"
                f"📌 **المصطلح:** `{term}`\n"
                f"📖 **الترجمة (عربي / إنجليزي):**\n{definition}"
            )
        else:
            await query.answer("هذه الكلمة موجودة مسبقاً في بطاقاتك!", show_alert=True)
            
    elif data == "back_to_read":
        last_text = user_last_texts.get(user_id)
        await query.edit_message_reply_markup(reply_markup=None)
        if last_text:
            await query.message.reply_text(f"📄 **العودة إلى الشيت الخاص بك:**\n\n{last_text}")
        else:
            await query.message.reply_text("أرسل الشيت من جديد لمتابعة القراءة.")

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
