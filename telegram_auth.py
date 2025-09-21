import asyncio
from pyrogram import Client
from pyrogram.errors import FloodWait, PhoneCodeInvalid, PhoneCodeExpired, SessionPasswordNeeded
import config

class TelegramAuth:
    def __init__(self, account, bot, admin_id):
        self.account = account
        self.bot = bot
        self.admin_id = admin_id
        self.client = None
        self.auth_step = 0
        self.phone_code_hash = None
        
    async def start_auth(self):
        """Начинает процесс авторизации"""
        try:
            session_name = self.account.get('session_file')
            if not session_name:
                phone = self.account.get('phone', 'default')
                session_name = f"account_{phone.replace('+', '').replace('-', '').replace(' ', '')}"
            
            api_id = self.account.get('api_id')
            api_hash = self.account.get('api_hash')
            
            if not api_id or not api_hash:
                raise Exception("API_ID или API_HASH не найдены для аккаунта")
            
            try:
                api_id = int(api_id)
            except ValueError:
                raise Exception("API_ID должен быть числом")
            
            self.client = Client(session_name, api_id, api_hash)
            
            await self.bot.send_message(
                self.admin_id, 
                f"🔑 Начинаю авторизацию"
            )
            
            await self.client.connect()
            
            await asyncio.sleep(5)
            sent_code = await self.client.send_code(self.account['phone'])
            self.phone_code_hash = sent_code.phone_code_hash
            
            await self.bot.send_message(
                self.admin_id,
                f"📱 Код подтверждения отправлен на номер {self.account['phone']}\n\n"
                f"Введите код подтверждения:"
            )
            
            return True
            
        except FloodWait as e:
            await self.bot.send_message(
                self.admin_id,
                f"⏳ Слишком много попыток. Подождите {e.value} секунд"
            )
            return False
        except Exception as e:
            await self.bot.send_message(
                self.admin_id,
                f"❌ Ошибка при отправке кода: {e}"
            )
            return False
    
    async def verify_code(self, code):
        """Проверяет код подтверждения"""
        try:
            code_str = str(code).strip()
            
            print(f"DEBUG: Код '{code_str}', phone_code_hash: {self.phone_code_hash[:10] if self.phone_code_hash else 'None'}")
            print(f"DEBUG: Тип phone_code_hash: {type(self.phone_code_hash)}")
            
            if not code_str:
                await self.bot.send_message(
                    self.admin_id,
                    "❌ Код пустой! Попробуйте еще раз."
                )
                return False
            
            await self.client.sign_in(
                phone_number=self.account['phone'],
                phone_code=code_str,
                phone_code_hash=self.phone_code_hash
            )
            
            
            await self.client.disconnect()
            return True
            
        except Exception as e:
            if "PASSWORD_HASH_INVALID" in str(e) or "SESSION_PASSWORD_NEEDED" in str(e):
                await self.bot.send_message(
                    self.admin_id,
                    f"🔐 Включена двухфакторная аутентификация\n\nВведите пароль:"
                )
                return "password_needed"
            elif "PHONE_CODE_EXPIRED" in str(e):
                await self.bot.send_message(
                    self.admin_id,
                    f"⏰ Код подтверждения истек. Отправляю новый код..."
                )
                try:
                    await asyncio.sleep(3)
                    sent_code = await self.client.send_code(self.account['phone'])
                    self.phone_code_hash = sent_code.phone_code_hash
                    await self.bot.send_message(
                        self.admin_id,
                        f"📱 Новый код подтверждения отправлен на номер {self.account['phone']}\n\nВведите код подтверждения:"
                    )
                    return "new_code_sent"
                except Exception as send_error:
                    await self.bot.send_message(
                        self.admin_id,
                        f"❌ Ошибка при отправке нового кода: {send_error}"
                    )
                    return False
            elif "PHONE_CODE_INVALID" in str(e):
                await self.bot.send_message(
                    self.admin_id,
                    f"❌ Неверный код подтверждения. Проверьте правильность ввода."
                )
                return False
            else:
                await self.bot.send_message(
                    self.admin_id,
                    f"❌ Неверный код подтверждения: {e}"
                )
                return False
    
    async def verify_password(self, password):
        """Проверяет пароль двухфакторной аутентификации"""
        try:
            await self.client.check_password(password)
            
            
            await self.client.disconnect()
            return True
            
        except Exception as e:
            return False
