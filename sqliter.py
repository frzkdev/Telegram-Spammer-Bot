import sqlite3
import config

class DBConnection(object):
    def __init__(self):
        self.conn = sqlite3.connect(f'{config.DIR}database.db', check_same_thread=False)
        self.c = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        """Создает таблицы в базе данных если их нет"""
        try:
            self.c.execute('''
                CREATE TABLE IF NOT EXISTS CHANNELS (
                    CHANNEL TEXT PRIMARY KEY,
                    ADDITIONAL TEXT
                )
            ''')
            
            self.c.execute('''
                CREATE TABLE IF NOT EXISTS SETTINGS (
                    ID INTEGER PRIMARY KEY,
                    PHOTO TEXT,
                    TEXT TEXT,
                    MESSAGE TEXT,
                    SPAM INTEGER,
                    TIMEOUT INTEGER
                )
            ''')
            
            self.c.execute('''
                CREATE TABLE IF NOT EXISTS ACCOUNTS (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    PHONE TEXT UNIQUE,
                    NAME TEXT,
                    STATUS TEXT DEFAULT 'inactive',
                    SESSION_FILE TEXT,
                    API_ID TEXT,
                    API_HASH TEXT
                )
            ''')
            
            try:
                self.c.execute('ALTER TABLE ACCOUNTS ADD COLUMN API_ID TEXT')
            except:
                pass
            
            try:
                self.c.execute('ALTER TABLE ACCOUNTS ADD COLUMN API_HASH TEXT')
            except:
                pass
            
            settings = self.c.execute('SELECT COUNT(*) FROM SETTINGS').fetchone()[0]
            if settings == 0:
                self.c.execute('''
                    INSERT INTO SETTINGS (ID, PHOTO, TEXT, MESSAGE, SPAM, TIMEOUT) 
                    VALUES (1, '', 'Введите текст для рассылки', 'Введите текст для рассылки', 0, 1)
                ''')
            
            self.conn.commit()
        except Exception as e:
            print(f"Ошибка при создании таблиц: {e}")

    def add_additional_text(self, id , text):
        table = self.c.execute(f'SELECT ADDITIONAL FROM CHANNELS WHERE CHANNEL = "{id}"').fetchone()
        if table == None:
            self.c.execute(f'INSERT INTO CHANNELS(CHANNEL, ADDITIONAL) VALUES (?,?)', [str(id), str(text)])
        else:
            self.c.execute(f'UPDATE CHANNELS SET ADDITIONAL = (?) WHERE CHANNEL = (?)', [str(text),str(id)])
        self.conn.commit()

    def get_additional_text(self, id):
        table = self.c.execute(f'SELECT ADDITIONAL FROM CHANNELS WHERE CHANNEL = "{id}"').fetchone()
        return table

    def change_text(self, text):
        self.c.execute(f'UPDATE SETTINGS SET TEXT = (?) WHERE ID = (?)', [str(text), 1])
        self.conn.commit()

    def change_photo(self, name):
        self.c.execute(f'UPDATE SETTINGS SET PHOTO = (?) WHERE ID = (?)', [str(name), 1])
        self.conn.commit()

    def settings(self):
        table = self.c.execute(f'SELECT * FROM SETTINGS  WHERE ID = (?)', [1]).fetchone()
        return table

    def setSpam(self, spam):
        table = self.c.execute(f'UPDATE SETTINGS SET SPAM = (?) WHERE ID = (?)', [spam,1]).fetchone()
        return table

    def setTimeOut(self, time):
        table = self.c.execute(f'UPDATE SETTINGS SET TIMEOUT = (?) WHERE ID = (?)', [time, 1]).fetchone()
        return table

    def add_chat(self, chat_id, chat_title):
        """Добавляет чат в базу данных"""
        try:
            self.c.execute(f'INSERT OR REPLACE INTO CHANNELS(CHANNEL, ADDITIONAL) VALUES (?, ?)', [str(chat_id), str(chat_title)])
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка при добавлении чата: {e}")
            return False

    def get_all_chats(self):
        """Получает все чаты из базы данных"""
        try:
            chats = self.c.execute('SELECT CHANNEL, ADDITIONAL FROM CHANNELS').fetchall()
            result = []
            for chat in chats:
                chat_id = chat[0]
                additional_text = chat[1] if chat[1] else ""
                title = additional_text if additional_text else f"Chat {chat_id}"
                result.append({'id': chat_id, 'title': title})
            return result
        except Exception as e:
            print(f"Ошибка при получении чатов: {e}")
            return []

    def add_account(self, phone, name, session_file, api_id=None, api_hash=None):
        """Добавляет аккаунт в базу данных"""
        try:
            self.c.execute('INSERT OR REPLACE INTO ACCOUNTS (PHONE, NAME, SESSION_FILE, API_ID, API_HASH) VALUES (?, ?, ?, ?, ?)', 
                         [phone, name, session_file, api_id, api_hash])
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка при добавлении аккаунта: {e}")
            return False

    def get_all_accounts(self):
        """Получает все аккаунты из базы данных"""
        try:
            accounts = self.c.execute('SELECT ID, PHONE, NAME, STATUS, SESSION_FILE, API_ID, API_HASH FROM ACCOUNTS').fetchall()
            return [{
                'id': acc[0], 
                'phone': acc[1], 
                'name': acc[2], 
                'status': acc[3],
                'session_file': acc[4],
                'api_id': acc[5],
                'api_hash': acc[6]
            } for acc in accounts]
        except Exception as e:
            print(f"Ошибка при получении аккаунтов: {e}")
            return []

    def set_account_status(self, account_id, status):
        """Устанавливает статус аккаунта"""
        try:
            self.c.execute('UPDATE ACCOUNTS SET STATUS = ? WHERE ID = ?', [status, account_id])
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка при изменении статуса аккаунта: {e}")
            return False

    def get_account_by_id(self, account_id):
        """Получает аккаунт по ID"""
        try:
            account = self.c.execute('SELECT * FROM ACCOUNTS WHERE ID = ?', [account_id]).fetchone()
            if account:
                return {
                    'id': account[0], 
                    'phone': account[1], 
                    'name': account[2], 
                    'status': account[3], 
                    'session_file': account[4],
                    'api_id': account[5] if len(account) > 5 else None,
                    'api_hash': account[6] if len(account) > 6 else None
                }
            return None
        except Exception as e:
            print(f"Ошибка при получении аккаунта: {e}")
            return None

    def delete_account(self, account_id):
        """Удаляет аккаунт"""
        try:
            self.c.execute('DELETE FROM ACCOUNTS WHERE ID = ?', [account_id])
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка при удалении аккаунта: {e}")
            return False

    def __del__(self):
        self.c.close()
        self.conn.close()