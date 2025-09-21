import config
import asyncio
from pyrogram import Client

clients = {}

async def get_chats():
    try:
        account = await get_active_account()
        if not account:
            print("Нет активного аккаунта")
            return []
        
        client = await create_client_for_account(account)
        if not client:
            print("Ошибка создания клиента")
            return []
        
        if not client.is_connected:
            try:
                await client.start()
            except Exception as e:
                print(f"Ошибка авторизации: {e}")
                return []
        
        chats = []
        try:
            async for dialog in client.get_dialogs(limit=100):
                if dialog.chat.type in ['channel', 'supergroup']:
                    chats.append({
                        'id': dialog.chat.id,
                        'title': dialog.chat.title or "Без названия"
                    })
        except Exception as e:
            print(f"Ошибка получения диалогов: {e}")
        
        if not chats:
            print("Используем каналы из базы данных")
            from sqliter import DBConnection
            db = DBConnection()
            chats = db.get_all_chats()
        
        return chats
    except Exception as e:
        print(f"Ошибка при получении чатов: {e}")
        return []

async def get_active_account():
    """Получает активный аккаунт для рассылки"""
    try:
        from sqliter import DBConnection
        db = DBConnection()
        accounts = db.get_all_accounts()
        
        for account in accounts:
            if account['status'] == 'active':
                return account
        return None
    except Exception as e:
        print(f"Ошибка при получении активного аккаунта: {e}")
        return None

async def create_client_for_account(account):
    """Создает клиент для аккаунта"""
    try:
        session_name = account.get('session_file')
        if not session_name:
            phone = account.get('phone', 'default')
            session_name = f"account_{phone.replace('+', '').replace('-', '').replace(' ', '')}"
        
        api_id = account.get('api_id')
        api_hash = account.get('api_hash')
        
        if not api_id or not api_hash:
            print(f"API_ID или API_HASH не найдены для аккаунта {account.get('name', 'Unknown')}")
            return None
        
        try:
            api_id = int(api_id)
        except ValueError:
            print(f"API_ID должен быть числом для аккаунта {account.get('name', 'Unknown')}")
            return None
        
        if session_name not in clients:
            clients[session_name] = Client(session_name, api_id, api_hash)
        return clients[session_name]
    except Exception as e:
        print(f"Ошибка при создании клиента: {e}")
        return None

async def leave_from_channel(id):
    try:
        account = await get_active_account()
        if not account:
            return False
        
        client = await create_client_for_account(account)
        if not client:
            return False
        
        if not client.is_connected:
            await client.start()
        await client.leave_chat(id)
        return True
    except Exception as e:
        print(f"Ошибка при выходе из канала: {e}")
        return False

async def spamming(spam_list, settings, db, bot):
    try:
        account = await get_active_account()
        if not account:
            await bot.send_message(config.ADMIN, "❌ Нет активного аккаунта! Добавьте и активируйте аккаунт в разделе '👤 Аккаунт'")
            return
        
        client = await create_client_for_account(account)
        if not client:
            await bot.send_message(config.ADMIN, f"❌ Ошибка создания клиента для аккаунта {account['name']}")
            return
        
        if not client.is_connected:
            try:
                await client.start()
            except Exception as auth_error:
                await bot.send_message(config.ADMIN, f"❌ Ошибка авторизации аккаунта {account['name']}: {auth_error}\n\nПроверьте номер телефона и пароль")
                return
        
        total_count = len(spam_list)
        
        progress_msg = await bot.send_message(config.ADMIN, f"🚀 Начинаю рассылку через аккаунт {account['name']} ({account['phone']})...\n\n📊 Прогресс: 0/{total_count}")
        
        sent_count = 0
        
        while settings[4] == 1:
            for chat in spam_list:
                settings = db.settings()
                try:
                    try:
                        chat_info = await client.get_chat(chat['id'])
                    except Exception as check_error:
                        continue
                    
                    with open(f'{config.DIR}{settings[1]}', 'rb') as photo:
                        await client.send_photo(chat['id'], photo, caption=f"{settings[2]}")
                        sent_count += 1
                except Exception as e:
                    try:
                        await client.send_message(chat['id'], f"{settings[2]}")
                        sent_count += 1
                    except Exception as e:
                        pass
                
                try:
                    await progress_msg.edit_text(f"🚀 Рассылка через аккаунт {account['name']} ({account['phone']})...\n\n📊 Прогресс: {sent_count}/{total_count} ✅")
                except:
                    pass
                
                await asyncio.sleep(settings[5]*60)
                if settings[4] != 1:
                    break
                    
        await bot.send_message(config.ADMIN, f"🏁 Рассылка завершена")
    except Exception as e:
        print(f"Ошибка в функции spamming: {e}")
        await bot.send_message(config.ADMIN, f"❌ Критическая ошибка рассылки: {e}")