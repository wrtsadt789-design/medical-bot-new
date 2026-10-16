import os
import re
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from deep_translator import GoogleTranslator

TOKEN = "8750644059:AAEA-loCMcUkGH_EU-Zd334E7NikGI0KOfs"

# القاموس الشامل والنهائي للمصطلحات الطبية واللاتينية من الشيتات الثمانية
GLOBAL_MEDICAL_DICT = {
    "prescribe": {"ar": "يصف (دواء/علاج)", "en": "To suggest a medicine or treatment"},
    "examine": {"ar": "يفحص / يكشف", "en": "Inspect / Look at a patient"},
    "bleed": {"ar": "ينزف", "en": "Lose blood from the body"},
    "medicate": {"ar": "يعالج بالدواء", "en": "Treat with medicine"},
    "diagnose": {"ar": "يشخص مرض", "en": "Identify the nature of an illness"},
    "clavicle": {"ar": "عظمة الترقوة", "en": "Collarbone"},
    "larynx": {"ar": "الحنجرة (صندوق الصوت)", "en": "Voice box"},
    "patella": {"ar": "صابونة الركبة", "en": "Kneecap"},
    "phalanges": {"ar": "سلاميات (الأصابع)", "en": "Bones of a finger or toe"},
    "scapula": {"ar": "لوح الكتف", "en": "Shoulder blade"},
    "sternum": {"ar": "عظمة القص", "en": "Breastbone"},
    "trachea": {"ar": "القصبة الهوائية", "en": "Windpipe"},
    "uterus": {"ar": "الرحم", "en": "Womb"},
    "vertebral column": {"ar": "العمود الفقري", "en": "Spine"},
    "acute": {"ar": "حاد (مقابل مزمن)", "en": "Acute (opp. chronic)"},
    "benign": {"ar": "حميد (مقابل خبيث)", "en": "Benign (opp. malignant)"},
    "anticoagulant": {"ar": "مضاد تخثر / مسيل للدم", "en": "Blood thinner / prevents clots"},
    "antiseptic": {"ar": "مطهر", "en": "Prevents infection / kills bacteria"},
    "aspirin": {"ar": "أسبرين (مسكن/خافض حرارة)", "en": "Pain reliever & reduces fever"},
    "insulin": {"ar": "إنسولين لعلاج السكري", "en": "Hormone used to treat diabetes"},
    "penicillin": {"ar": "بنسيللين (مضاد حيوي)", "en": "Antibiotic for bacterial infections"},
    "-itis": {"ar": "التهاب", "en": "Inflammation"},
    "hyper-": {"ar": "فرط / زيادة", "en": "Excessive / Above normal"},
    "hypo-": {"ar": "نقص / انخفاض", "en": "Deficient / Below normal"},
    "-plasty": {"ar": "جراحة تجميلية / إصلاح", "en": "Surgical repair"},
    "rhinoplasty": {"ar": "تجميل الأنف", "en": "Plastic surgery of the nose"},
    "gastrodynia": {"ar": "ألم المعدة", "en": "Stomach pain"},
    "hypertension": {"ar": "ارتفاع ضغط الدم", "en": "High blood pressure"},
    "thrombus": {"ar": "خثرة دموية", "en": "Blood clot"}
}

user_flashcards = {}
user_last_texts = {}

def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📚 عرض جميع المصطلحات الطبية", callback_data="menu_all_terms")],
        [InlineKeyboardButton("🧠 عرض بطاقات الاستذكار", callback_data="menu_flashcards")],
        [InlineKeyboardButton("🎯 بدء الاختبارات (Quiz)", callback_data="menu_quiz")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🩺 **أهلاً بك يا دكتور في نظامك الطبي الذكي** 📚\n\n"
        "كل شيء جاهز أمامك بالأزرار أدناه:\n"
        "• **عرض جميع المصطلحات الطبية** (من الشيتات الثمانية)\n"
        "• **عرض بطاقات الاستذكار** (المصطلح ⬅️ المعنى عربي وإنجليزي)\n"
        "• **بدء الاختبارات (Quiz)** (تفاعلية مع التصحيح الفوري)\n\n"
        "💡 *لإضافة مصطلحات جديدة بالنسخ واللصق:* أرسل هكذا:\n"
        "`add:`\n"
        "`1. Term - المعنى بالعربي والانجليزي`"
    )
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")
    elif update.callback_query:
        try:
            await update.callback_query.message.edit_text(welcome_text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")
        except Exception:
            await update.callback_query.message.reply_text(welcome_text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_content = update.message.text
    user_id = update.message.from_user.id
    
    if text_content.lower().startswith("add:"):
        try:
            lines = text_content.split("\n")[1:]
            added_count = 0
            if user_id not in user_flashcards:
                user_flashcards[user_id] = []
                
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                cleaned_line = re.sub(r'^\d+[\.\-]\s*', '', line)
                if "-" in cleaned_line:
                    parts = cleaned_line.split("-", 1)
                    term = parts[0].strip()
                    definition = parts[1].strip()
                    user_flashcards[user_id].append({"term": term, "definition": definition})
                    added_count += 1
                elif ":" in cleaned_line:
                    parts = cleaned_line.split(":", 1)
                    term = parts[0].strip()
                    definition = parts[1].strip()
                    user_flashcards[user_id].append({"term": term, "definition": definition})
                    added_count += 1
                    
            if added_count > 0:
                await update.message.reply_text(f"✅ **تمت إضافة وترتيب {added_count} بطاقة جديدة بنجاح!**", parse_mode="Markdown", reply_markup=get_main_menu_keyboard())
                return
        except Exception:
            await update.message.reply_text("❌ خطأ في الصيغة. استخدم النمط: `1. المصطلح - المعنى`", parse_mode="Markdown")
            return

    user_last_texts[user_id] = text_content
    words = re.findall(r'\b[A-Za-z-]{3,}\b', text_content)
    
    if not words:
        await update.message.reply_text("لم ألاحظ كلمات إنجليزية أو لاتينية واضحة في النص.")
        return

    chunk_size = 25
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
            f"📄 **الجزء ({part_num}) من النص الطبي:**",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

async def show_all_terms_action(query):
    text = "📚 **جميع المصطلحات الطبية (الشيتات الثمانية):**\n\n"
    for term, info in GLOBAL_MEDICAL_DICT.items():
        text += f"🔹 **{term.upper()}**\n   🇸🇦 العربي: {info['ar']}\n   🇬🇧 الإنجليزي: {info['en']}\n\n"
        
    keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if len(text) > 4000:
        await query.message.edit_text(text[:4000], parse_mode="Markdown")
        await query.message.reply_text(text[4000:8000], reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await query.message.edit_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def review_flashcards_action(query, user_id):
    review_text = "🧠 **بطاقات الاستذكار الطبية:**\n*(وجه البطاقة: المصطلح | الظهر: المعنى بالعربي والإنجليزي)*\n\n"
    
    idx = 1
    for term, info in GLOBAL_MEDICAL_DICT.items():
        review_text += f"📌 **البطاقة ({idx})**\n   🔸 **الوجه:** `{term.upper()}`\n   🔹 **الظهر:** {info['ar']} | {info['en']}\n\n"
        idx += 1
        
    cards = user_flashcards.get(user_id, [])
    if cards:
        review_text += "━━━━━━━━━━━━━━━━━━━\n⭐ **بطاقاتي الإضافية:**\n\n"
        for card in cards:
            review_text += f"📌 **البطاقة ({idx})**\n   🔸 **الوجه:** `{card['term'].upper()}`\n   🔹 الظهر:\n\n"
            idx += 1
            
    keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if len(review_text) > 4000:
        await query.message.edit_text(review_text[:4000], parse_mode="Markdown")
        await query.message.reply_text(review_text[4000:8000], reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await query.message.edit_text(review_text, reply_markup=reply_markup, parse_mode="Markdown")

async def start_quiz_action(query, user_id, context):
    quiz_pool = []
    for term, info in GLOBAL_MEDICAL_DICT.items():
        quiz_pool.append({
            "term": term, 
            "def": f"🇸🇦 {info['ar']} | 🇬🇧 {info['en']}"
        })
        
    if user_id in user_flashcards:
        for c in user_flashcards[user_id]:
            quiz_pool.append({
                "term": c['term'], 
                "def": c['definition']
            })
            
    if len(quiz_pool) < 4:
        keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="back_to_menu")]]
        await query.message.edit_text("⚠️ **عذراً، يلزم توفر 4 مصطلحات على الأقل لبدء الاختبار.**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return
        
    correct_item = random.choice(quiz_pool)
    correct_term = correct_item['term']
    correct_def = correct_item['def']
    
    context.user_data['current_correct_def'] = correct_def
    
    wrong_pool = [item['def'] for item in quiz_pool if item['term'] != correct_term]
    wrong_choices = random.sample(wrong_pool, min(3, len(wrong_pool)))
    
    choices = wrong_choices + [correct_def]
    random.shuffle(choices)
    
    keyboard = []
    for choice in choices:
        is_correct = "1" if choice == correct_def else "0"
        keyboard.append([InlineKeyboardButton(choice, callback_data=f"q_{is_correct}")])
        
    keyboard.append([InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="back_to_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    quiz_text = (
        f"🎯 **اختبار المصطلحات الطبية (Quiz)**\n\n"
        f"ما هو المعنى الصحيح والدقيق للمصطلح الآتي؟\n\n"
        f"📌 **{correct_term.upper()}**"
    )
    await query.message.edit_text(quiz_text, reply_markup=reply_markup, parse_mode="Markdown")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    if data == "menu_all_terms":
        await show_all_terms_action(query)
    elif data == "menu_flashcards":
        await review_flashcards_action(query, user_id)
    elif data == "menu_quiz":
        await start_quiz_action(query, user_id, context)
    elif data == "back_to_menu":
        await start(update, context)
    elif data.startswith("w_"):
        word = data.replace("w_", "")
        word_lower = word.lower()
        
        if word_lower in GLOBAL_MEDICAL_DICT:
            info = GLOBAL_MEDICAL_DICT[word_lower]
            translation = f"🇸🇦 {info['ar']}\n🇬🇧 {info['en']}"
        else:
            try:
                trans_ar = GoogleTranslator(source='auto', target='ar').translate(word)
                trans_en = GoogleTranslator(source='auto', target='en').translate(word)
                translation = f"🇸🇦 {trans_ar}\n🇬🇧 {trans_en}"
            except Exception:
                translation = f"المصطلح: {word}"
        
        context.user_data[f'trans_{word}'] = translation

        keyboard = [
            [
                InlineKeyboardButton("⭐ إضافة للاستذكار", callback_data=f"save_{word}"),
                InlineKeyboardButton("🔙 العودة للقائمة", callback_data="back_to_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        msg = f"📌 **{word.upper()}**\n\n{translation}"
        await query.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")
        
    elif data.startswith("save_"):
        term = data.replace("save_", "")
        definition = context.user_data.get(f'trans_{term}', "معرّف طبياً")
        
        if user_id not in user_flashcards:
            user_flashcards[user_id] = []
            
        if not any(card['term'].lower() == term.lower() for card in user_flashcards[user_id]):
            user_flashcards[user_id].append({"term": term, "definition": definition})
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text(f"✅ **تمت إضافة البطاقة بنجاح:**\n\n📌 **{term.upper()}**\n{definition}", parse_mode="Markdown", reply_markup=get_main_menu_keyboard())
        else:
            await query.answer("هذه الكلمة موجودة مسبقاً في بطاقاتك!", show_alert=True)
            
    elif data.startswith("q_"):
        status = data.replace("q_", "")
        correct_answer = context.user_data.get('current_correct_def', 'المعلومة متوفرة في القاموس')
        
        keyboard = [
            [InlineKeyboardButton("🔄 سؤال آخر (Quiz)", callback_data="menu_quiz")],
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if status == "1":
            feedback_text = "✅ **إجابة صحيحة بامتياز يا دكتور! كفو 🩺🚀**"
            await query.message.edit_text(feedback_text, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            feedback_text = (
                f"❌ **إجابة خاطئة!**\n\n"
                f"💡 **الإجابة الصحيحة الدقيقة هي:**\n"
                f"`{correct_answer}`"
            )
            await query.message.edit_text(feedback_text, reply_markup=reply_markup, parse_mode="Markdown")

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("review", lambda u, c: review_flashcards_action(u.callback_query if u.callback_query else u, u.message.from_user.id if u.message else u.callback_query.from_user.id)))
    application.add_handler(CommandHandler("quiz", lambda u, c: start_quiz_action(u.callback_query if u.callback_query else u, u.message.from_user.id if u.message else u.callback_query.from_user.id, c)))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(button_callback))

    print("Professional Medical Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
