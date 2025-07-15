import asyncio
import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# 👤 ADMIN & KANAL KONFIGURASIÝASY
ADMIN_ID = 8143084360  # <-- Sanlar düzgün saklanýar
ALLOWED_USERS = set()
REQUIRED_CHANNELS = ['@DaykaVPNS', '@Lion_Servers', '@Baburoff_VPN', '@Dayka_Store_Chatt', '@VPNDAYKA']  # <- Özüňiziň kanallaryňyzy şu ýere ýaz

# 🗂️ Sesssiýa maglumatlary
user_sessions = {}
waiting_for = {}
scheduled_posts = []
previous_messages = {}

# 🔧 Menýu klawiaturasy
def main_menu_keyboard(user_id=None):
    buttons = [
        [InlineKeyboardButton("📤 Reklama Goýmаk", callback_data='reklama')],
        [InlineKeyboardButton("📊 Statistika", callback_data='statistika')],
        [InlineKeyboardButton("📂 Postlarym", callback_data='postlarym')]
    ]
    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data='admin_panel')])
    return InlineKeyboardMarkup(buttons)

# 🚀 START Handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_member_all = True

    for channel in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(channel, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                is_member_all = False
                break
        except:
            is_member_all = False
            break

    if is_member_all:
        ALLOWED_USERS.add(user_id)
        await update.message.reply_text(
            "👋 Hoş geldiňiz! Aşakdaky menýulardan birini saýlaň:",
            reply_markup=main_menu_keyboard(user_id)
        )
    else:
        buttons = [[InlineKeyboardButton(f"➕ {channel}", url=f"https://t.me/{channel[1:]}")] for channel in REQUIRED_CHANNELS]
        buttons.append([InlineKeyboardButton("✅ Agza boldum", callback_data="check_membership")])
        await update.message.reply_text(
            "❗ Iltimas, aşakdaky kanallara goşulyň we soň '✅ Agza boldum' düwmesine basyň:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

# 🔘 BUTTON Handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "check_membership":
        is_member_all = True
        for channel in REQUIRED_CHANNELS:
            try:
                member = await context.bot.get_chat_member(channel, user_id)
                if member.status not in ['member', 'administrator', 'creator']:
                    is_member_all = False
                    break
            except:
                is_member_all = False
                break

        if is_member_all:
            ALLOWED_USERS.add(user_id)
            await query.edit_message_text(
                "🎉 Şowly! Indi botdan peýdalanyp bilersiňiz.",
                reply_markup=main_menu_keyboard(user_id)
            )
        else:
            await query.answer("❗ Käbir kanallara heniz goşulmadyk ýaly!", show_alert=True)
        return

    if data == 'admin_panel' and user_id == ADMIN_ID:
        await query.edit_message_text(
            "⚙️ Admin Panel:\nUlanyjy dolandyryşlaryny saýlaň:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Ulanyjy goş", callback_data='add_user')],
                [InlineKeyboardButton("➖ Ulanyjy aýyr", callback_data='remove_user')],
                [InlineKeyboardButton("📋 Sanawy gör", callback_data='list_users')],
                [InlineKeyboardButton("📢 Bildiriş ugrat", callback_data='broadcast')],
                [InlineKeyboardButton("⬅ Yza", callback_data='back')]
            ])
        )

    elif data == 'add_user' and user_id == ADMIN_ID:
        waiting_for[user_id] = 'add_user'
        await query.edit_message_text("🆔 Goşmaly ulanyjynyň ID-sini giriziň:")

    elif data == 'remove_user' and user_id == ADMIN_ID:
        waiting_for[user_id] = 'remove_user'
        await query.edit_message_text("🆔 Aýyrmaly ulanyjynyň ID-sini giriziň:")

    elif data == 'list_users' and user_id == ADMIN_ID:
        if not ALLOWED_USERS:
            await query.edit_message_text("📭 Hiç hili ulanyjy goşulmady.")
        else:
            text = "✅ Rugsat berlen ulanyjylar:\n"
            for uid in ALLOWED_USERS:
                try:
                    user = await context.bot.get_chat(uid)
                    username = f"@{user.username}" if user.username else "—"
                except:
                    username = "—"
                text += f"{uid} {username}\n"
            await query.edit_message_text(text)

    elif data == 'broadcast' and user_id == ADMIN_ID:
        waiting_for[user_id] = 'broadcast'
        await query.edit_message_text("📢 Ugratmaly bildirişiňizi ýazyp iberiň:")

    elif data == 'back':
        await query.edit_message_text("🔙 Yza gaýdýarys...", reply_markup=main_menu_keyboard(user_id))

    elif data == 'reklama':
        if user_id != ADMIN_ID and user_id not in ALLOWED_USERS:
            await query.edit_message_text("❌ Bu bölüme girmek üçin rugsat ýok.")
            return
        await query.edit_message_text(
            "📌 Post görnüşini saýlaň:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🖼 Surat", callback_data='surat'),
                InlineKeyboardButton("✏ Tekst", callback_data='tekst')
            ]])
        )

    elif data in ['surat', 'tekst']:
        if user_id != ADMIN_ID and user_id not in ALLOWED_USERS:
            await query.edit_message_text("❌ Bu bölüme girmek üçin rugsat ýok.")
            return
        user_sessions[user_id] = {'type': data}
        waiting_for[user_id] = 'photo' if data == 'surat' else 'text'
        prompt = "🖼 Surat ugradyň:" if data == 'surat' else "✍ Tekst giriziň:"
        await query.edit_message_text(prompt)

    elif data == 'statistika':
        kanal_sany = len({p['channel'] for p in scheduled_posts})
        post_sany = len(scheduled_posts)
        await query.edit_message_text(f"📊 Statistik:\n📢 Kanallar: {kanal_sany}\n📬 Postlar: {post_sany}")

    elif data == 'postlarym':
        if user_id != ADMIN_ID and user_id not in ALLOWED_USERS:
            await query.edit_message_text("❌ Bu bölüme girmek üçin rugsat ýok.")
            return
        user_posts = [p for p in scheduled_posts if p['user_id'] == user_id]
        if not user_posts:
            await query.edit_message_text("📭 Siziň postlaryňyz ýok.")
            return
        buttons = [
            [InlineKeyboardButton(
                f"{i+1}) {p['channel']} ({'⏸' if p.get('paused') else '▶'})",
                callback_data=f"post_{i}"
            )] for i, p in enumerate(user_posts)
        ]
        await query.edit_message_text("📂 Postlaryňyz:", reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith('post_'):
        idx = int(data.split('_')[1])
        user_posts = [p for p in scheduled_posts if p['user_id'] == user_id]
        if idx >= len(user_posts): return
        post = user_posts[idx]
        real_idx = scheduled_posts.index(post)
        ctrl = [
            InlineKeyboardButton("🗑 Poz", callback_data=f"delete_{real_idx}"),
            InlineKeyboardButton("▶ Dowam" if post.get('paused') else "⏸ Duruz", callback_data=f"toggle_{real_idx}")
        ]
        await query.edit_message_text(
            f"📤 Kanal: {post['channel']}\n🕒 Minut: {post['minute']}\n📆 Gün: {post['day']}\n📮 Ugradylan: {post['sent_count']}\n🔁 Galyan: {post['max_count'] - post['sent_count']}",
            reply_markup=InlineKeyboardMarkup([ctrl])
        )

    elif data.startswith('delete_'):
        idx = int(data.split('_')[1])
        if idx < len(scheduled_posts):
            scheduled_posts.pop(idx)
        await query.edit_message_text("✅ Post pozuldy.")

    elif data.startswith('toggle_'):
        idx = int(data.split('_')[1])
        if idx < len(scheduled_posts):
            scheduled_posts[idx]['paused'] = not scheduled_posts[idx].get('paused', False)
        await query.edit_message_text("🔄 Status üýtgedildi.")

# 💬 MESSAGE Handler
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in waiting_for:
        return

    step = waiting_for[user_id]

    # ✅ Admin bildiriş ugratmak
    if step == 'broadcast':
        text = update.message.text
        count = 0
        for uid in ALLOWED_USERS.union({ADMIN_ID}):
            try:
                await context.bot.send_message(uid, f"📢 Admin bildirişi:\n\n{text}")
                count += 1
            except:
                pass
        await update.message.reply_text(f"✅ Bildiriş {count} ulanyja ugradyldy.")
        waiting_for.pop(user_id)
        return

    # ✅ Ulanyjy aýyrmak
    elif step == 'remove_user':
        try:
            rem_id = int(update.message.text)
            ALLOWED_USERS.discard(rem_id)
            await update.message.reply_text("❌ Ulanyjy aýryldy.")
        except:
            await update.message.reply_text("⚠️ ID san görnüşinde bolmaly.")
        waiting_for.pop(user_id)
        return

    # ⛔ Ulanyjy rugsat berlen däl bolsa geçme
    if user_id != ADMIN_ID and user_id not in ALLOWED_USERS:
        return

    sess = user_sessions.get(user_id, {})
    
    # ✅ Surat ugratmak ädimi
    if step == 'photo' and update.message.photo:
        sess['photo'] = update.message.photo[-1].file_id
        sess['type'] = 'surat'
        user_sessions[user_id] = sess
        waiting_for[user_id] = 'caption'
        await update.message.reply_text("📝 Surata caption giriziň:")

    # ✅ Caption girizmek
    elif step == 'caption':
        sess['caption'] = update.message.text
        waiting_for[user_id] = 'minute'
        await update.message.reply_text("🕒 Her näçe minutda ugradylsyn?")

    # ✅ Tekst post
    elif step == 'text':
        sess['text'] = update.message.text
        sess['type'] = 'text'
        waiting_for[user_id] = 'minute'
        await update.message.reply_text("🕒 Her näçe minutda ugradylsyn?")

    # ✅ Minut soramak
    elif step == 'minute':
        try:
            sess['minute'] = int(update.message.text)
            waiting_for[user_id] = 'day'
            await update.message.reply_text("📅 Näçe gün dowam etsin?")
        except:
            await update.message.reply_text("⚠️ San bilen giriziň!")

    # ✅ Gün soramak
    elif step == 'day':
        try:
            sess['day'] = int(update.message.text)
            waiting_for[user_id] = 'channel'
            await update.message.reply_text("📢 Haýsy kanal? (@username görnüşinde)")
        except:
            await update.message.reply_text("⚠️ San bilen giriziň!")

    # ✅ Kanal we soňky ýatyrma
    elif step == 'channel':
        sess['channel'] = update.message.text.strip()
        waiting_for.pop(user_id)

        post = {
            'user_id': user_id,
            'type': sess['type'],
            'minute': sess['minute'],
            'day': sess['day'],
            'channel': sess['channel'],
            'next_time': time.time(),
            'sent_count': 0,
            'max_count': (sess['day'] * 24 * 60) // sess['minute']
        }

        if sess['type'] == 'surat':
            post['photo'], post['caption'] = sess['photo'], sess['caption']
        else:
            post['text'] = sess['text']

        scheduled_posts.append(post)
        await update.message.reply_text("✅ Post üstünlikli döredildi.")

# ⏰ Post Scheduler
async def scheduler(app):
    while True:
        now = time.time()
        for post in scheduled_posts:
            if post.get('paused') or post['sent_count'] >= post['max_count']:
                continue
            if post['user_id'] not in ALLOWED_USERS and post['user_id'] != ADMIN_ID:
                post['paused'] = True
                continue
            if now >= post['next_time']:
                try:
                    if post['channel'] in previous_messages:
                        try:
                            await app.bot.delete_message(post['channel'], previous_messages[post['channel']])
                        except:
                            pass
                    if post['type'] == 'surat':
                        msg = await app.bot.send_photo(post['channel'], post['photo'], caption=post['caption'])
                    else:
                        msg = await app.bot.send_message(post['channel'], post['text'])

                    previous_messages[post['channel']] = msg.message_id
                    post['sent_count'] += 1
                    post['next_time'] = now + post['minute'] * 60
                except Exception as e:
                    print(f"Ugradyp bolmady: {e}")
        await asyncio.sleep(30)

# 🔁 Main
async def main():
    app = ApplicationBuilder().token("7991348150:AAF75OU3trKi4pVovGZpSOoC7xsVbMlkOt8").build()  # Bot tokeniňizi şu ýere goýuň

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, message_handler))

    asyncio.create_task(scheduler(app))
    print("🤖 Bot işläp başlady...")
    await app.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
