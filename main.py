from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

import asyncio
import config, user
from sqliter import DBConnection

bot = Bot(token=config.TOKEN)
dp = Dispatcher(storage=MemoryStorage())
db = DBConnection()


def welcome_keyboard():
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text='👤 Аккаунт'))
    keyboard.add(KeyboardButton(text='❓ Доступные каналы'))
    keyboard.add(KeyboardButton(text='🔢 Интервал'))
    keyboard.add(KeyboardButton(text='📑 Пост'))
    keyboard.add(KeyboardButton(text='➡️ START'))
    keyboard.adjust(2)
    return keyboard.as_markup(resize_keyboard=True)

@dp.message(Command("start"))
async def process_start_command(message: types.Message):
    if message.chat.id == config.ADMIN:
        await message.answer("💾 Рассылка сообщений по групам:\n\n", reply_markup=welcome_keyboard())
    else:
        await message.answer("❌ Вам запрещенно использовать данного бота.")

class AdditionStates(StatesGroup):
    id = State()

class PostStates(StatesGroup):
    text = State()

class TimeStates(StatesGroup):
    timeout = State()

class AddChatStates(StatesGroup):
    chat_id = State()

class AccountStates(StatesGroup):
    phone = State()
    name = State()
    api_id = State()
    api_hash = State()
    code = State()
    password = State()

@dp.message(AdditionStates.id)
async def input_additional_text(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        channel_id = data['channel_id']
        db.add_additional_text(channel_id, message.text)
        await message.answer(f'☑️ Текст для {channel_id} был успешно обновлен.')
        await state.clear()
    except:
        await message.answer(f'❌ Текст для {channel_id} не был обновлен.')

@dp.message(PostStates.text)
async def input_post_text(message: types.Message, state: FSMContext):
    db.change_text(message.text)
    await message.answer('☑️ Текст для поста был обновлен.')
    await state.clear()

@dp.message(TimeStates.timeout)
async def input_timeout(message: types.Message, state: FSMContext):
    try:
        if int(message.text) > 1:
            db.setTimeOut(message.text)
            await message.answer('☑️ Интервал рассылки был успешно обновлен.')
        else:
            await message.answer('❌ Введите число больше 1.')
    except:
        await message.answer('❌ Введите число.')
    await state.clear()

@dp.message(F.text == '❓ Доступные каналы')
async def show_channels(message: types.Message):
    keyboard = InlineKeyboardBuilder()
    
    chats = db.get_all_chats()
    
    if not chats:
        keyboard.add(InlineKeyboardButton(text='➕ Добавить чат', callback_data='ADD_CHAT'))
        await message.answer('Нет доступных каналов. Добавьте чаты для рассылки:', reply_markup=keyboard.as_markup())
    else:
        for chat in chats:
            keyboard.add(InlineKeyboardButton(text=chat["title"], callback_data=f'EDIT_ID:{chat["id"]}'))
        keyboard.add(InlineKeyboardButton(text='➕ Добавить чат', callback_data='ADD_CHAT'))
        keyboard.adjust(1)
        await message.answer('Все доступные каналы:', reply_markup=keyboard.as_markup())

@dp.message(F.text == '➡️ START')
async def start_spam_command(message: types.Message):
    db.setSpam(1)
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text='🛑 Остановить спам'))
    await message.answer('😊 Спам был успешно запущен.', reply_markup=keyboard.as_markup(resize_keyboard=True))
    await start_spam("Заказать тг бота - @peacefulb")

@dp.message(F.text == '🛑 Остановить спам')
async def stop_spam(message: types.Message):
    db.setSpam(0)
    await message.answer('😊 Отправляю последние сообщения и закругляюсь', reply_markup=welcome_keyboard())

@dp.message(F.text == '🔢 Интервал')
async def show_interval(message: types.Message):
    settings = db.settings()
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text='🕘 Изменить интервал', callback_data='INTERVAL'))
    await message.answer(f'🔃 Текущий интервал {settings[5]} минут(а)', reply_markup=keyboard.as_markup())

@dp.message(F.text == '👤 Аккаунт')
async def show_accounts(message: types.Message):
    accounts = db.get_all_accounts()
    keyboard = InlineKeyboardBuilder()
    
    if not accounts:
        keyboard.add(InlineKeyboardButton(text='➕ Добавить аккаунт', callback_data='ADD_ACCOUNT'))
        await message.answer('Нет добавленных аккаунтов. Добавьте аккаунт для рассылки:', reply_markup=keyboard.as_markup())
    else:
        for account in accounts:
            status_emoji = "🟢" if account['status'] == 'active' else "🔴"
            keyboard.add(InlineKeyboardButton(
                text=f"{status_emoji} {account['name']} ({account['phone']})", 
                callback_data=f'ACCOUNT_{account["id"]}'
            ))
        keyboard.add(InlineKeyboardButton(text='➕ Добавить аккаунт', callback_data='ADD_ACCOUNT'))
        keyboard.adjust(1)
        await message.answer('Управление аккаунтами:', reply_markup=keyboard.as_markup())

@dp.message(F.text == '📑 Пост')
async def show_post(message: types.Message):
    import os
    settings = db.settings()
    
    photo_path = settings[1] if settings[1] else None
    text = settings[2] if settings[2] else "Текст не установлен"
    
    try:
        if photo_path and photo_path.strip() and os.path.exists(f'{config.DIR}{photo_path}'):
            from aiogram.types import FSInputFile
            photo_file = FSInputFile(f'{config.DIR}{photo_path}')
            await message.answer_photo(photo_file, caption=text)
        else:
            await message.answer(f"📄 Текст поста:\n\n{text}")
    except Exception as e:
        await message.answer(f"📄 Текст поста:\n\n{text}")
        print(f"Ошибка при показе фото: {e}")

    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text='🌆 Изменить фото', callback_data='EDIT_PHOTO'))
    keyboard.add(InlineKeyboardButton(text='📜 Изменить текст', callback_data='EDIT_TEXT'))
    keyboard.adjust(1)
    await message.answer('🔼 Ваш пост выглядит вот так 🔼', reply_markup=keyboard.as_markup())

@dp.callback_query(F.data.startswith('EDIT_ID:'))
async def handle_edit_id(callback: types.CallbackQuery, state: FSMContext):
    channel_id = callback.data.split(':')[1]
    try:
        addit_text = db.get_additional_text(channel_id)[0]
    except:
        addit_text = None
    
    channel_title = "Неизвестный канал"
    try:
        chats = db.get_all_chats()
        for chat in chats:
            if str(chat['id']) == str(channel_id):
                channel_title = chat['title']
                break
    except:
        pass
    
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text='❌ Покинуть чат', callback_data=f'LFC:{channel_id}'))
    
    keyboard.add(InlineKeyboardButton(text='✏️ Изменить название', callback_data=f'ADD_ADDITIONAL:{channel_id}'))
    await callback.message.answer(f'Текущее название: "{channel_title}"', reply_markup=keyboard.as_markup())
    
    await callback.answer()

@dp.callback_query(F.data.startswith('ADD_ADDITIONAL:'))
async def handle_add_additional(callback: types.CallbackQuery, state: FSMContext):
    channel_id = callback.data.split(':')[1]
    await state.update_data(channel_id=channel_id)
    await callback.message.answer(f'✏️ Введите новое название:')
    await state.set_state(AdditionStates.id)
    await callback.answer()

@dp.callback_query(F.data.startswith('LFC:'))
async def handle_leave_from_channel(callback: types.CallbackQuery):
    log = await user.leave_from_channel(callback.data.split(':')[1])
    if log:
        text = '☑️ Вы успешно покинули данный канал.'
    else:
        text = '❌ Возникли некие трудности при выходе.'
    await callback.message.answer(text)
    await callback.answer()

@dp.callback_query(F.data == 'EDIT_TEXT')
async def handle_edit_text(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer('📄 Введите текст поста:')
    await state.set_state(PostStates.text)
    await callback.answer()

@dp.callback_query(F.data == 'EDIT_PHOTO')
async def handle_edit_photo(callback: types.CallbackQuery):
    await callback.message.answer('📄 Отправь мне фото для изменения:')
    await callback.answer()

@dp.callback_query(F.data == 'INTERVAL')
async def handle_interval(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer('📄 Отправь мне интервал рассылки между чатами (в минутах):')
    await state.set_state(TimeStates.timeout)
    await callback.answer()

@dp.callback_query(F.data == 'ADD_CHAT')
async def handle_add_chat(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer('📄 Отправь мне ссылку на канал/группу или юзернейм:\n\nПримеры:\n• https://t.me/channel_name\n• t.me/channel_name\n• @channel_name\n• channel_name\n\n⚠️ Бот должен быть добавлен в канал как администратор!')
    await state.set_state(AddChatStates.chat_id)
    await callback.answer()

@dp.message(AddChatStates.chat_id)
async def input_chat_id(message: types.Message, state: FSMContext):
    try:
        chat_input = message.text.strip()
        
        if chat_input.startswith('https://t.me/'):
            username = chat_input.replace('https://t.me/', '').split('/')[0]
        elif chat_input.startswith('t.me/'):
            username = chat_input.replace('t.me/', '').split('/')[0]
        elif chat_input.startswith('@'):
            username = chat_input[1:]
        else:
            username = chat_input
        if username.startswith('@'):
            username = username[1:]
        
        try:
            chat = await bot.get_chat(f'@{username}')
            chat_id = str(chat.id)
            chat_title = chat.title or chat.first_name or f"Chat {username}"
            
            db.add_chat(chat_id, chat_title)
            await message.answer(f'✅ Канал "{chat_title}" (@{username}) успешно добавлен!\nID: {chat_id}')
            
        except Exception as e:
            await message.answer(f'❌ Не удалось найти канал @{username}. Проверьте:\n• Правильность написания\n• Что бот добавлен в канал\n• Что канал публичный или бот имеет доступ')
        
        await state.clear()
    except Exception as e:
        await message.answer(f'❌ Ошибка при добавлении чата: {e}')
        await state.clear()

@dp.callback_query(F.data == 'ADD_ACCOUNT')
async def handle_add_account(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer('📱 Введите номер телефона:')
    await state.set_state(AccountStates.phone)
    await callback.answer()

@dp.message(AccountStates.phone)
async def input_phone(message: types.Message, state: FSMContext):
    phone = message.text.strip()
    await state.update_data(phone=phone)
    await message.answer('👤 Введите имя для аккаунта:')
    await state.set_state(AccountStates.name)

@dp.message(AccountStates.name)
async def input_name(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        phone = data['phone']
        name = message.text.strip()
        
        await state.update_data(name=name)
        
        await asyncio.sleep(2)
        await message.answer(
            "🔑 Введите API_ID:\n\n"
            "Получить можно на https://my.telegram.org/auth\n\n"
            "⚠️ Рекомендуется подождать 5-10 минут между добавлением аккаунтов"
        )
        await state.set_state(AccountStates.api_id)
    except Exception as e:
        await message.answer(f'❌ Ошибка: {e}')
        await state.clear()

@dp.message(AccountStates.api_id)
async def input_api_id(message: types.Message, state: FSMContext):
    try:
        api_id = message.text.strip()
        
        if not api_id.isdigit():
            await message.answer("❌ API_ID должен быть числом! Попробуйте еще раз:")
            return
        
        await state.update_data(api_id=api_id)
        
        await message.answer(
            "🔑 Введите API_HASH:\n\n"
            "Получить можно на https://my.telegram.org/auth"
        )
        await state.set_state(AccountStates.api_hash)
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
        await state.clear()

@dp.message(AccountStates.api_hash)
async def input_api_hash(message: types.Message, state: FSMContext):
    try:
        api_hash = message.text.strip()
        
        await state.update_data(api_hash=api_hash)
        
        data = await state.get_data()
        phone = data['phone']
        name = data['name']
        api_id = data['api_id']
        api_hash = data['api_hash']
        
        session_file = f"account_{phone.replace('+', '').replace('-', '').replace(' ', '')}"
        
        await state.update_data(session_file=session_file)
        temp_account = {
            'phone': phone, 
            'name': name, 
            'session_file': session_file,
            'api_id': api_id,
            'api_hash': api_hash
        }
        
        from telegram_auth import TelegramAuth
        auth = TelegramAuth(temp_account, bot, config.ADMIN)
        unique_key = f"auth_{phone}_{name}"
        await state.update_data(auth=auth, unique_key=unique_key)
        
        success = await auth.start_auth()
        if success:
            await state.set_state(AccountStates.code)
        else:
            await message.answer('❌ Ошибка при начале авторизации')
            await state.clear()
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
        await state.clear()

@dp.message(AccountStates.code)
async def input_code(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        auth = data['auth']
        code = message.text.strip()
        
        result = await auth.verify_code(code)
        
        if result == True:
            phone = data['phone']
            name = data['name']
            session_file = data['session_file']
            api_id = data['api_id']
            api_hash = data['api_hash']
            
            if db.add_account(phone, name, session_file, api_id, api_hash):
                await message.answer(f'✅ Аккаунт "{name}" ({phone}) успешно добавлен и авторизован!')
            else:
                await message.answer('❌ Ошибка при добавлении аккаунта в базу')
            
            await state.clear()
        elif result == "password_needed":
            await state.set_state(AccountStates.password)
        elif result == "new_code_sent":
            pass
        else:
            await message.answer("❌ Неверный код. Попробуйте еще раз:")
            
    except Exception as e:
        await message.answer(f'❌ Ошибка: {e}')
        await state.clear()

@dp.message(AccountStates.password)
async def input_password(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        auth = data['auth']
        password = message.text.strip()
        
        result = await auth.verify_password(password)
        
        if result:
            phone = data['phone']
            name = data['name']
            session_file = data['session_file']
            api_id = data['api_id']
            api_hash = data['api_hash']
            
            if db.add_account(phone, name, session_file, api_id, api_hash):
                await message.answer(f'✅ Аккаунт "{name}" ({phone}) успешно добавлен и авторизован!')
            else:
                await message.answer('❌ Ошибка при добавлении аккаунта в базу')
            
            await state.clear()
        else:
            await message.answer("❌ Неверный пароль. Попробуйте еще раз:")
            
    except Exception as e:
        await message.answer(f'❌ Ошибка: {e}')
        await state.clear()

@dp.callback_query(F.data.startswith('ACCOUNT_'))
async def handle_account_click(callback: types.CallbackQuery):
    account_id = callback.data.split('_')[1]
    account = db.get_account_by_id(account_id)
    
    if account:
        keyboard = InlineKeyboardBuilder()
        
        if account['status'] == 'active':
            keyboard.add(InlineKeyboardButton(text='🔴 Деактивировать', callback_data=f'DEACTIVATE_{account_id}'))
        else:
            keyboard.add(InlineKeyboardButton(text='🟢 Активировать', callback_data=f'ACTIVATE_{account_id}'))
        
        keyboard.add(InlineKeyboardButton(text='🗑 Удалить', callback_data=f'DELETE_ACCOUNT_{account_id}'))
        keyboard.adjust(1)
        
        status_text = "Активен" if account['status'] == 'active' else "Неактивен"
        api_status = "✅ Настроен" if account.get('api_id') and account.get('api_hash') else "❌ Не настроен"
        await callback.message.answer(
            f'👤 Аккаунт: {account["name"]}\n📱 Телефон: {account["phone"]}\n📊 Статус: {status_text}\n🔑 API: {api_status}',
            reply_markup=keyboard.as_markup()
        )
    await callback.answer()

@dp.callback_query(F.data.startswith('ACTIVATE_'))
async def handle_activate_account(callback: types.CallbackQuery):
    account_id = callback.data.split('_')[1]
    if db.set_account_status(account_id, 'active'):
        await callback.message.answer('✅ Аккаунт активирован!')
    else:
        await callback.message.answer('❌ Ошибка при активации аккаунта')
    await callback.answer()

@dp.callback_query(F.data.startswith('DEACTIVATE_'))
async def handle_deactivate_account(callback: types.CallbackQuery):
    account_id = callback.data.split('_')[1]
    if db.set_account_status(account_id, 'inactive'):
        await callback.message.answer('✅ Аккаунт деактивирован!')
    else:
        await callback.message.answer('❌ Ошибка при деактивации аккаунта')
    await callback.answer()

@dp.callback_query(F.data.startswith('DELETE_ACCOUNT_'))
async def handle_delete_account(callback: types.CallbackQuery):
    account_id = callback.data.split('_')[2]
    
    account = db.get_account_by_id(account_id)
    if not account:
        await callback.message.answer('❌ Аккаунт не найден')
        await callback.answer()
        return
    if db.delete_account(account_id):
        session_file = account.get('session_file')
        if session_file:
            try:
                import os
                session_path = f"{session_file}.session"
                if os.path.exists(session_path):
                    os.remove(session_path)
                    print(f"✅ Файл сессии {session_path} удален")
                else:
                    print(f"⚠️ Файл сессии {session_path} не найден")
            except Exception as e:
                print(f"❌ Ошибка при удалении файла сессии: {e}")
        
        await callback.message.answer('✅ Аккаунт и файл сессии удалены!')
    else:
        await callback.message.answer('❌ Ошибка при удалении аккаунта')
    await callback.answer()

@dp.message(F.photo)
async def download_photo(message: types.Message):
    try:
        settings = db.settings()
        old_photo_path = settings[1] if settings[1] else None
        
        photo = message.photo[-1]
        file_id = photo.file_id
        
        file = await bot.get_file(file_id)
        file_path = f"photos/photo_{file_id}.jpg"
        
        import os
        os.makedirs("photos", exist_ok=True)
        
        await bot.download_file(file.file_path, file_path)
        
        db.change_photo(file_path)
        if (old_photo_path and old_photo_path.strip() and 
            os.path.exists(old_photo_path) and 
            old_photo_path != file_path):
            try:
                os.remove(old_photo_path)
                print(f"Удалено старое фото: {old_photo_path}")
            except Exception as delete_error:
                print(f"Ошибка при удалении старого фото: {delete_error}")
        
        await message.answer('🖼 Фото было успешно обновлено!')
        
    except Exception as e:
        await message.answer(f'❌ Ошибка при загрузке фото: {e}')
        print(f"Ошибка загрузки фото: {e}")


async def start_spam(x):
    if db.settings()[4] == 1:
        spam_list = []
        for i in await user.get_chats():
            try:
                addit_text = db.get_additional_text(i['id'])[0]
            except:
                addit_text = ''
            i['text'] = addit_text
            spam_list.append(i)
        settings = db.settings()
        tksNumber = asyncio.create_task(user.spamming(spam_list, settings, db, bot))

async def main():
    try:
        print("🚀 Запуск бота...")
        await dp.start_polling(bot)
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен пользователем")
    except Exception as e:
        print(f"Критическая ошибка: {e}")
