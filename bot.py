import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = "8750644059:AAEA-loCMcUkGH_EU-Zd334E7NikGI0KOf"

# قاموس شامل ومباشر للمترجمة الفورية (أضف هنا أي مصطلح لاتيني وطبي تدرسه)
DIRECT_DICT = {
    "cardiovascular": {
        "ar": "قَلْبِيّ وِعَائِيّ (الجهاز القلبي الوعائي)",
        "system": "جهاز / نظام",
        "comprises": "يتكون من / يشتمل على",
        "heart": "القلب",
        "blood": "الدم",
        "vessels": "الأوعية",
        "cardiology": "علم القلب",
        "medical": "طبي",
        "sternum": "عظمة القص",
        "days": "أيام",
        "early": "مبكرا / مبكرا",
        "studying": "الدراسة",
        "night": "الليل",
        "useless": "عديم الفائدة",
        "boring": "ممل",
        "helpful": "مفيد",
        "concentration": "التركيز",
        "reading": "قراءة",
        "books": "كتب",
        "sleepy": "نعسان"
    }
}

# تخزين البطاقات والنصوص لكل مستخدم
user_flashcards = {}
user_last_texts = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحباً يا دكتور! 🩺\nأرسل الشيت لنبدأ القراءة المباشرة والترجمة الفورية لأي مصطلح أو كلمة لاتينية.",
        parse_mode="Markdown"
    )

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
                await update.message.reply_text(f"✅ تم الحفظ: {term} ⬅️ {definition}")
                return
        except Exception:
            pass

    user_last_texts[user_id] = text_content
    words = re.findall(r'\b[A-Za-z]{3,}\b', text_content)
    
    if not words:
        await update.message.reply_text("لم ألاحظ كلمات إنجليزية أو لاتينية واضحة.")
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
        await update.message.reply_text("📭 قائمة الاستذكار فارغة حتى الآن.")
        return
        
    review_text = "🧠 **قائمة بطاقات الاستذكار:\n\n"
    for idx, card in enumerate(cards, 1):
        review_text += f"{idx}. 📌 ** ⬅️ {card['definition']}\n"
        
    await update.message.reply_text(review_text)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    if data.startswith("w_"):
        word = data.replace("w_", "")
        word_lower = word.lower()
        
        # البحث المباشر في القاموس الطبي المخصص
        if word_lower in DIRECT_DICT:
            info = DIRECT_DICT[word_lower]
            if isinstance(info, dict):
                translation = info.get("ar", "مصطلح تخصصي")
            else:
                translation = info
        else:
            translation = f"مصطلح تخصصي: {word}"
        
        # حفظ الترجمة مؤقتاً للزر
        context.user_data[f'trans_{word}'] = translation

        keyboard = [
            [
                InlineKeyboardButton("⭐ إضافة إلى الاستذكار", callback_data=f"save_{word}"),
                InlineKeyboardButton("📖 العودة إلى القراءة", callback_data="back_to_read")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        msg = f"📌 **{word}**\n🇸🇦 {translation}"
        await query.message.reply_text(msg, reply_markup=reply_markup)
        
    elif data.startswith("save_"):
        term = data.replace("save_", "")
        definition = context.user_data.get(f'trans_{term}', "ترجمة طبية")
        
        if user_id not in user_flashcards:
            user_flashcards[user_id] = []
            
        # التحقق من عدم التكرار
        if not any(card['term'].lower() == term.lower() for card in user_flashcards[user_id]):
            user_flashcards[user_id].append({"term": term, "definition": definition})
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text(f"✅ تم الحفظ بنجاح:\n📌 **{term}** ⬅️ {definition}")
        else:
            await query.answer("هذه الكلمة موجودة مسبقاً في بطاقاتك!", show_alert=True)
            
    elif data == "back_to_read":
        last_text = user_last_texts.get(user_id)
        await query.edit_message_reply_markup(reply_markup=None)
        if last_text:
            await query.message.reply_text(f"📄 **العودة إلى الشيت:**\n\n{last_text}")
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
