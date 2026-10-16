import os
import re
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from deep_translator import GoogleTranslator

TOKEN = "8750644059:AAEA-loCMcUkGH_EU-Zd334E7NikGI0KOfs"

# القاموس الشامل للمصطلحات الطبية واللاتينية
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
    "acute": {"ar": "حاد ⟵ مزمن", "en": "Acute ⟵ Chronic"},
    "benign": {"ar": "حميد ⟵ خبيث", "en": "Benign ⟵ Malignant"},
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "مرحباً يا دكتور! 🩺📚\n\n"
        "النظام التفاعلي والاختبارات جاهزة الآن:\n\n"
        "• أرسل أي **نص أو شيت** لتوليد أزرار القراءة والترجمة.\n"
        "• `/review` لعرض بطاقات الاستذكار.\n"
        "• `/quiz` لبدء **الاختبار التفاعلي (اختيار من متعدد)**.\n"
        "• **لإضافة مصطلحات دفعة واحدة:**\n"
        "أرسل بالصيغة:\n"
        "`add:`\n"
        "1. Term - المعنى بالعربي والانجليزي"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

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
                await update.message.reply_text(f"✅ تمت إضافة وترتيب {added_count} بطاقة بنجاح إلى جدول استذكارك!")
                return
        except Exception:
            await update.message.reply_text("❌ خطأ في الصيغة. استخدم النمط: `1. المصطلح - المعنى`")
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
            reply_markup=reply_markup
        )

async def review_flashcards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    cards = user_flashcards.get(user_id, [])
    
    if not cards:
        await update.message.reply_text("📭 قائمة الاستذكار فارغة. تصفح النصوص أو أضف مصطلحات جديدة.")
        return
        
    review_text = "🧠 **بطاقات الاستذكار الطبية:\n\n"
    for idx, card in enumerate(cards, 1):
        review_text += f"{idx}. 📌 ** ⬅️ {card['definition']}\n"
        
    if len(review_text) > 4000:
        for x in range(0, len(review_text), 4000):
            await update.message.reply_text(review_text[x:x+4000])
    else:
        await update.message.reply_text(review_text, parse_mode="Markdown")

async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    # دمج بطاقات المستخدم مع القاموس العالمي لتوفير بنك أسئلة ضخم للاختبار
    all_pool = list(GLOBAL_MEDICAL_DICT.items())
    if user_id in user_flashcards:
        for c in user_flashcards[user_id]:
            all_pool.append((c['term'], {"ar": c['definition'], "en": c['definition']}))
            
    if len(all_pool) < 4:
        await update.message.reply_text("⚠️ يلزم وجود 4 مصطلحات على الأقل لبدء اختبار الاختيار من متعدد. تصفح بعض الشيتات أولاً.")
        return
        
    # اختيار سؤال عشوائي
    correct_item = random.choice(all_pool)
    correct_term = correct_item[0]
    correct_def = correct_item[1]['ar']
    
    # اختيار 3 إجابات خاطئة عشوائية
    wrong_pool = [item[1]['ar'] for item in all_pool if item[0] != correct_term]
    wrong_choices = random.sample(wrong_pool, min(3, len(wrong_pool)))
    
    choices = wrong_choices + [correct_def]
    random.shuffle(choices)
    
    # بناء الأزرار للاختيارات
    keyboard = []
    for choice in choices:
        # وضع علامة مميزة للإجابة الصحيحة في البيانات المشفرة للزر
        is_correct = "1" if choice == correct_def else "0"
        keyboard.append([InlineKeyboardButton(choice, callback_data=f"q_{is_correct}")])
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🎯 **اختبار المصطلحات الطبية (التفاعلي):**\n\nما هو المعنى الصحيح للمصطلح التالي؟\n📌 **{correct_term.upper()}**",
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    if data.startswith("w_"):
        word = data.replace("w_", "")
        word_lower = word.lower()
        
        if word_lower in GLOBAL_MEDICAL_DICT:
            info = GLOBAL_MEDICAL_DICT[word_lower]
            translation = f"العربي: {info['ar']} | الإنجليزي: {info['en']}"
        else:
            try:
                trans_ar = GoogleTranslator(source='auto', target='ar').translate(word)
                trans_en = GoogleTranslator(source='auto', target='en').translate(word)
                translation = f"العربي: {trans_ar} | الإنجليزي: {trans_en}"
            except Exception:
                translation = f"المصطلح: {word}"
        
        context.user_data[f'trans_{word}'] = translation

        keyboard = [
            [
                InlineKeyboardButton("⭐ إضافة إلى الاستذكار", callback_data=f"save_{word}"),
                InlineKeyboardButton("📖 العودة", callback_data="back_to_read")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        msg = f"📌 **{word}**\n📋 {translation}"
        await query.message.reply_text(msg, reply_markup=reply_markup)
        
    elif data.startswith("save_"):
        term = data.replace("save_", "")
        definition = context.user_data.get(f'trans_{term}', "معرّف طبياً")
        
        if user_id not in user_flashcards:
            user_flashcards[user_id] = []
            
        if not any(card['term'].lower() == term.lower() for card in user_flashcards[user_id]):
            user_flashcards[user_id].append({"term": term, "definition": definition})
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text(f"✅ تمت إضافة البطاقة بنجاح:\n📌 **{term}**\n└ {definition}")
        else:
            await query.answer("هذه الكلمة موجودة مسبقاً في بطاقاتك!", show_alert=True)
            
    elif data == "back_to_read":
        last_text = user_last_texts.get(user_id)
        await query.edit_message_reply_markup(reply_markup=None)
        if last_text:
            await query.message.reply_text(f"📄 **العودة للنص:**\n\n{last_text}")
        else:
            await query.message.reply_text("أرسل النص من جديد لمتابعة القراءة.")
            
    elif data.startswith("q_"):
        status = data.replace("q_", "")
        await query.edit_message_reply_markup(reply_markup=None)
        if status == "1":
            await query.message.reply_text("✅ **إجابة صحيحة بامتياز يا دكتور! كفو 🩺🚀**\n\nأرسل `/quiz` لاختبار آخر.")
        else:
            await query.message.reply_text("❌ **إجابة خاطئة، حاول مرة أخرى!**\n\nأرسل `/quiz` لسؤال جديد.")

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("review", review_flashcards))
    application.add_handler(CommandHandler("quiz", start_quiz))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(button_callback))

    print("Interactive Medical Quiz Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
