import asyncio
from telethon import TelegramClient, errors

api_id = 24836372  # замените
api_hash = 'e315c2f7039188ae46bf3f106f94a92b'
phone = '+79776751154'

FOLDER_NAME = "Amo's chats✅"
DEFAULT_TEXT = "привет всем, ищу работников в сфере телеграмма\nприбыль : от 300 рублей до неограниченной суммы\nбез вложений, пишите"
DEFAULT_INTERVAL = 300

client = TelegramClient('session', api_id, api_hash)

current_text = DEFAULT_TEXT
current_interval = DEFAULT_INTERVAL
running = True

async def send_log_to_me(text):
    """Отправляет сообщение в Избранное"""
    try:
        await client.send_message('me', text)
    except:
        pass  # если не отправилось, игнорируем

async def send_to_folder():
    dialogs = await client.get_dialogs()
    folder = None
    for d in dialogs:
        if d.folder and d.folder.title == FOLDER_NAME:
            folder = d.folder
            break
    if not folder:
        await send_log_to_me(f"❌ Папка '{FOLDER_NAME}' не найдена")
        return

    chats = [d for d in dialogs if d.folder and d.folder.id == folder.id]
    if not chats:
        await send_log_to_me("❌ В папке нет чатов")
        return

    success_count = 0
    error_count = 0
    skip_count = 0
    log_lines = []

    for chat in chats:
        try:
            await client.send_message(chat.entity, current_text)
            success_count += 1
            # Можно залогировать каждую успешную отправку, но чтобы не спамить — только итог
            # Если хотите видеть каждую — раскомментируйте следующую строку
            # await send_log_to_me(f"✅ Отправлено в {chat.name}")
        except errors.rpcerrorlist.ChatWriteForbiddenError:
            error_count += 1
            log_lines.append(f"⛔ Нет прав: {chat.name}")
        except errors.rpcerrorlist.MessageTooLongError:
            error_count += 1
            log_lines.append(f"📏 Слишком длинное: {chat.name}")
        except errors.rpcerrorlist.MessageEmptyError:
            error_count += 1
            log_lines.append(f"📭 Пустое сообщение: {chat.name}")
        except Exception as e:
            error_text = str(e).lower()
            if 'stars' in error_text or 'paid' in error_text or 'звезд' in error_text:
                skip_count += 1
                log_lines.append(f"⭐ Пропущено (платный чат): {chat.name}")
            else:
                error_count += 1
                log_lines.append(f"⚠️ Ошибка: {chat.name} — {e}")
        await asyncio.sleep(1.5)  # пауза между чатами

    # Итоговый отчёт
    summary = f"📊 Рассылка завершена\n✅ Успешно: {success_count}\n❌ Ошибок: {error_count}\n⭐ Пропущено (платных): {skip_count}"
    if log_lines:
        # Ограничим длину, чтобы не превысить лимит сообщения
        details = "\n".join(log_lines[:20])  # первые 20 строк
        if len(log_lines) > 20:
            details += f"\n... и ещё {len(log_lines)-20} ошибок"
        summary += "\n\nПодробности:\n" + details
    await send_log_to_me(summary)

async def scheduler():
    while True:
        if running:
            await send_to_folder()
        else:
            await send_log_to_me("⏸️ Рассылка приостановлена")
        await asyncio.sleep(current_interval)

@client.on(events.NewMessage(from_users='me'))
async def command_handler(event):
    global current_text, current_interval, running
    msg = event.message.text.strip()
    if msg.startswith('/'):
        parts = msg.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ''

        if cmd == '/interval':
            try:
                new_int = int(arg)
                if new_int < 10:
                    await event.reply('❌ Минимум 10 секунд')
                else:
                    current_interval = new_int
                    await event.reply(f'✅ Интервал: {current_interval} сек')
            except:
                await event.reply('❌ Формат: /interval 300')

        elif cmd == '/text':
            if arg:
                current_text = arg
                await event.reply('✅ Текст обновлён')
            else:
                await event.reply('❌ Укажите текст')

        elif cmd == '/stop':
            running = False
            await event.reply('⏸️ Рассылка остановлена')

        elif cmd == '/start':
            running = True
            await event.reply('▶️ Рассылка возобновлена')

        elif cmd == '/list':
            dialogs = await client.get_dialogs()
            folder = None
            for d in dialogs:
                if d.folder and d.folder.title == FOLDER_NAME:
                    folder = d.folder
                    break
            if not folder:
                await event.reply('❌ Папка не найдена')
                return
            chats = [d.name for d in dialogs if d.folder and d.folder.id == folder.id]
            await event.reply('📋 Чаты:\n' + '\n'.join(chats) if chats else 'Пусто')

        elif cmd == '/status':
            status = 'активна' if running else 'остановлена'
            await event.reply(f'📌 Статус: {status}\n⏱ Интервал: {current_interval} сек\n📝 Текст: {current_text[:60]}...')

        else:
            await event.reply('Доступно: /interval, /text, /stop, /start, /list, /status')

async def main():
    await client.start(phone=phone)
    print('Запущено. Команды в Избранное.')
    await asyncio.gather(scheduler(), client.run_until_disconnected())

if __name__ == '__main__':
    asyncio.run(main())
