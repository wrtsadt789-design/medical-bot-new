import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = "8750644059:AAEA-loCMcUkGH_EU-Zd334E7NikGI0KOfs"

# قاموس طبي فوري للمصطلحات والكلمات الطبية
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "مرحباً بك يا دكتور! 🩺✨\n"
        "أرسل لي الشيت الطويل، وسأقوم بتقسيمه وإرساله لك كاملاً دون أي اختصار أو نقصان كأزرار تفاعلية!"
    )
    await update.message.reply_text(welcome_text)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_content = update.message.text
    
    # تقسيم النص إلى كلمات
    words = re.findall(r'\b[A-Za-z]{3,}\b', text_content)
    
    if not words:
        await update.message.reply_text("لم ألاحظ كلمات إنجليزية واضحة في النص.")
        return

    # تقسيم الكلمات إلى دفعات (كل دفعة 30 كلمة في رسالة) لضمان إرسال النص كاملاً مهما كانت طوله
    chunk_size = 30
    for i in range(0, len(words), chunk_size):
        chunk = words[i:i + chunk_size]
        
        # بناء شبكة الأزرار لكل جزء
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
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(button_callback))

    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
