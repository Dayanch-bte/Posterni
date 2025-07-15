import asyncio
import time
import nest_asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

nest_asyncio.apply()

# 👤 ADMIN CONFIGURATION
ADMIN_ID = 8143084360
REQUIRED_CHANNELS = []  # Admin bu ýere goşar

# 🗂️ Session & Scheduling Data
user_sessions = {}
waiting_for = {}
scheduled_posts = []
previous_messages = {}

# 🔧 Membership Check
async def check_membership(user_id, bot):
    for ch in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(ch, user_id)
            if member.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True

# 🔧 Main Menu
def main_menu_keyboard(user_id=None):
    buttons = [
        [InlineKeyboardButton("📤 Reklama Goýmаk", callback_data='reklama')],
        [InlineKeyboardButton("📊 Statistika", callback_data='statistika')],
        [InlineKeyboardButton("📂 Postlarym", callback_data='postlarym')],
    ]
    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data='admin_panel')])
    return InlineKeyboardMarkup(buttons)

# 🚀 /start Handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Agzalyk barlaýarys
    if not await check_membership(user_id, context.bot):
        buttons = [[InlineKeyboardButton(f"➕ {ch}", url=f"https://t.me/{ch[1:]}")] for ch in REQUIRED_CHANNELS]
        buttons.append([InlineKeyboardButton("✅ Agza boldum", callback_data="check_channels")])
        await update.message.reply_text(
            "🔒 Boty ulanmak üçin aşakdaky kanallara agza boluň:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    await update.message.reply_text(
        "👋 Hoş geldiňiz! Aşakdaky menýulardan birini saýlaň:",
        reply_markup=main_menu_keyboard(user_id)
    )

# 🔘 Inline Button Handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    # ✅ Agzalyk tassyklama düwmesi
    if data == 'check_channels':
        if await check_membership(user_id, context.bot):
            await query.edit_message_text("✅ Siz ähli kanallara agza bolduňyz!", reply_markup=main_menu_keyboard(user_id))
        else:
            await query.edit_message_text("❌ Henize çenli ähli kanallara agza bolmadyňyz. Täzeden synanyşyň.")
        return

    # ⚙️ Admin Panel açmak
    if data == 'admin_panel' and user_id == ADMIN_ID:
        await query.edit_message_text(
            "⚙️ Admin Panel:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Kanal goş", callback_data='add_channel')],
                [InlineKeyboardButton("➖ Kanal aýyr", callback_data='remove_channel')],
                [InlineKeyboardButton("📋 Kanallar sanawy", callback_data='list_channels')],
                [InlineKeyboardButton("⬅ Yza", callback_data='back_admin')]
            ])
        )
        return

    # ➕ Kanal goşmak
    if data == 'add_channel' and user_id == ADMIN_ID:
        waiting_for[user_id] = 'add_channel'
        await query.edit_message_text("➕ Goşmaly kanal adyny giriziň: (@kanal_username görnüşinde)")
        return

    # ➖ Kanal aýyrmak
    if data == 'remove_channel' and user_id == ADMIN_ID:
        waiting_for[user_id] = 'remove_channel'
        await query.edit_message_text("➖ Aýyrmaly kanal adyny giriziň: (@kanal_username görnüşinde)")
        return

    # 📋 Kanallaryň sanawy
    if data == 'list_channels' and user_id == ADMIN_ID:
        if not REQUIRED_CHANNELS:
            await query.edit_message_text("📭 Agza bolmaly hiç hili kanal ýok.")
        else:
            text = "📋 Agza bolmaly kanallar sanawy:\n" + "\n".join(REQUIRED_CHANNELS)
            await query.edit_message_text(text)
        return

    # Admin panelden çykmak
    if data == 'back_admin' and user_id == ADMIN_ID:
        await query.edit_message_text("🔙 Admin Panelden çykdyňyz.", reply_markup=main_menu_keyboard(user_id))
        return

    # Agzalyk ýok bolsa -- beýleki düwmeler üçin gatnawlmaz
    if not await check_membership(user_id, context.bot):
        await query.edit_message_text("❌ Ilki kanallara agza boluň!", reply_markup=main_menu_keyboard(user_id))
        return

    # 🎯 Bu ýerde `reklama`, `statistika`, `postlarym` ýaly funksiýalaryň logikasy gelmeli...
    # Meselem:
    # if data == 'reklama': ...
    # elif data == 'statistika': ...
    # elif data.startswith('post_'): ...

# 💬 Text / Photo Handler
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Admin tarapyndan kanal sanawy üýtgedilýän wagtda ýagdaý
    if user_id == ADMIN_ID and user_id in waiting_for:
        step = waiting_for[user_id]
        if step == 'add_channel':
            channel = update.message.text.strip()
            if channel.startswith('@'):
                REQUIRED_CHANNELS.append(channel)
                await update.message.reply_text("✅ Kanal goşuldy.")
            else:
                await update.message.reply_text("⚠️ Kanal ady '@' bilen başlamaly.")
            waiting_for.pop(user_id)
            return
        if step == 'remove_channel':
            channel = update.message.text.strip()
            if channel in REQUIRED_CHANNELS:
                REQUIRED_CHANNELS.remove(channel)
                await update.message.reply_text("❌ Kanal aýryldy.")
            else:
                await update.message.reply_text("⚠️ Kanal sanawda ýok.")
            waiting_for.pop(user_id)
            return

    # Agzalyk barlagy: eger ýok bolsa başga mesajlara degişli bolmaýar
    if not await check_membership(user_id, context.bot):
        return

    # 🛠️ Bu ýerde reklama, postlar taýýarlamak, scheduler, statistika ýaly ähli funksiýasygi girizilýär.

# ✅ MAIN RUN
async def main():
    app = ApplicationBuilder().token("7991348150:AAF75OU3trKi4pVovGZpSOoC7xsVbMlkOt8").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, message_handler))

    # Scheduler we beýleki background tasklar:
    # asyncio.create_task(scheduler(app))

    print("🤖 Bot işläp başlady...")  
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
