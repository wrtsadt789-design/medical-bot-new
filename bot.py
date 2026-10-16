import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = "8750644059:AAEA-loCMcUkGH_EU-Zd334E7NikGI0KOf"

# قاموس طبي فوري
MEDICAL_DICT = {
    "cardiovascular": "قلبي وعائي",
    "system": "جهاز / نظام",
    "comprises": "يتكون من / يشتمل على",
    "heart": "القلب",
    "blood": "دم",
    "vessels": "أوعية",
    "cardiology": "علم القلب",
    "medical": "طبي",
    "specialty": "تخصص",
    "dealing": "يتعامل مع",
    "with": "مع",
    "disorders": "اضطرابات / أمراض",
    "common": "شائع",
    "conditions": "حالات",
    "include": "تشمل",
    "atherosclerosis": "تصلب الشرايين",
    "hypertension": "ارتفاع ضغط الدم",
    "myocardial": "عضلة القلب",
    "infarction": "احتشاء / جلطة",
    "inflammation": "التهاب",
    "muscle": "عضلة",
    "sternum": "عظمة القص"
}

# تخزين مؤقت لبطاقات الاستذكار لكل مستخدم
user_flashcards = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "مرحباً بك يا دكتور! 🩺✨\n"
        "البوت جاهز لمراجعة شيتاتك كاملة بدون نقصان، وترجمة المصطلحات، بالإضافة إلى **بطاقات الاستذكار (Flashcards)**!\n\n"
        "📌 **الأوامر المتاحة:**\n"
        "• أرسل أي شيت وسأقسمه لك كأزرار شبكية.\n"
        "• لإضافة بطاقة استذكارية جديدة أرسل هكذا:\n"
        "`add: المصطلح | التعريف`\n"
        "• لمراجعة البطاقات أرسل الأمر: `/review`"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_content = update.message.text
    user_id = update.message.from_user.id
    
    # التحقق مما إذا كان المستخدم يريد إضافة بطاقة استذكارية جديدة من الخارج
    if text_content.lower().startswith("add:"):
        try:
            parts = text_content.replace("add:", "").split("|")
            if len(parts) == 2:
                term = parts[0].strip()
                definition = parts[1].strip()
                
                if user_id not in user_flashcards:
                    user_flashcards[user_id] = []
                
                user_flashcards[user_id].append({"term": term, "definition": definition})
                
                await update.message.reply_text(
                    f"✅ تم إضافة بطاقة الاستذكار بنجاح!\n\n"
                    f"📌 **المصطلح:** `{term}`\n"
                    f"📖 **التعريف:** {definition}\n\n"
                    f"يمكنك مراجعة بطاقاتك في أي وقت بإرسال الأمر `/review`"
                )
                return
            else:
                await update.message.reply_text("❌ صيغة غير صحيحة. يرجى الإرسال بهذا الشكل:\n`add: المصطلح | التعريف`", parse_mode="Markdown")
                return
        except Exception:
            await update.message.reply_text("❌ حدث خطأ أثناء إضافة البطاقة. تأكد من استخدام الفاصلة `|`")
            return

    # معالجة الشيت النصي وإرساله كاملاً مقسماً كأزرار شبكية
    words = re.findall(r'\b[A-Za-z]{3,}\b', text_content)
    
    if not words:
        await update.message.reply_text("لم ألاحظ كلمات إنجليزية واضحة في النص. أو أرسل بطاقة جديدة بـ `add: المصطلح | التعريف`")
        return

    chunk_size = 30
    for i in range(0, len(words), chunk_size):
        chunk = words[i:i + chunk_size]
        
        keyboard = []
        row = []
        for word in chunk:
            row.append(InlineKeyboardButton(word, callback_data=f"w_{word.lower()}"))
            if len(row) == 3:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        reply_markup = InlineKeyboardMarkup(keyboard)
        part_num = (i // chunk_size) + 1
        
        await update.message.reply_text(
            f"📄 **الجزء ({part_num}) من الشيت الكامل:**\nاضغط على أي كلمة لترجمتها:",
            reply_markup=reply_markup
        )

async def review_flashcards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    cards = user_flashcards.get(user_id, [])
    
    if not cards:
        await update.message.reply_text("📭 ليس لديك أي بطاقات استذكارية مضافة حتى الآن.\nأضف بطاقة جديدة باستخدام:\n`add: المصطلح | التعريف`", parse_mode="Markdown")
        return
        
    review_text = "🧠 **بطاقات الاستذكار الخاصة بك للمراجعة:\n\n"
    for idx, card in enumerate(cards, 1):
        review_text += f"{idx}. 📌 ** ➡️ {card['definition']}\n"
        
    await update.message.reply_text(review_text, parse_mode="Markdown")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("w_"):
        word = data.replace("w_", "")
        translation_ar = MEDICAL_DICT.get(word, f"مصطلح تخصصي: {word}")
            
        msg = (
            f"📌 **الكلمة:** `{word.capitalize()}`\n"
            f"🔹 **الترجمة العربية:** {translation_ar}"
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
