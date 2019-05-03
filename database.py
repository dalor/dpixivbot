import psycopg2
from user import User

class Database:
    def __init__(self, DATABASE_URL, default):
        self.dbname = DATABASE_URL
        self.conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        self.pix = default
        self.create_table()
        self.temp = {}
        
    def create_table(self):
        cur = self.conn.cursor()
        cur.execute('''
        CREATE TABLE IF NOT EXISTS users 
        (chat_id INTEGER NOT NULL PRIMARY KEY,
        login TEXT NOT NULL,
        password TEXT NOT NULL,
        session TEXT,
        tt TEXT,
        last_id INTEGER,
        count INTEGER,
        only_pics INTEGER,
        by_one INTEGER)
        ''')
        self.conn.commit()
        cur.close()
    
    def is_user_exist(self, cur, chat_id):
        cur.execute('SELECT 1 FROM users WHERE chat_id = %s', (chat_id, ))
        return True if cur.fetchone() else False
    
    def set_user(self, chat_id, pix_acc):
        self.set_user_to_temp(chat_id, pix_acc)
        cur = self.conn.cursor()
        if not self.is_user_exist(cur, chat_id):
            cur.execute('INSERT INTO users (chat_id, login, password, session, tt) VALUES (%s, %s, %s, %s, %s)',
                (chat_id, pix_acc.login, pix_acc.password, pix_acc.session, pix_acc.tt))
        else:
            cur.execute('UPDATE users SET login = %s, password = %s, session = %s, tt = %s WHERE chat_id = %s',
                (pix_acc.login, pix_acc.password, pix_acc.session, pix_acc.tt, chat_id))
        self.conn.commit()
        cur.close()
    
    def del_user(self, chat_id):
        cur = self.conn.cursor()
        cur.execute('DELETE FROM users WHERE chat_id = %s', (chat_id, ))
        self.conn.commit()
        cur.close()
    
    def get_user_from_db(self, chat_id):
        cur = self.conn.cursor()
        cur.execute('SELECT login, password, session, tt, last_id, count, only_pics, by_one FROM users WHERE chat_id = %s', (chat_id, ))
        result = cur.fetchone()
        cur.close()
        if result:
            pix_acc = User(*result)
            if pix_acc.tt:
                if pix_acc.session != result[2] or pix_acc.tt != result[3]:
                    self.set_user(chat_id, pix_acc)
                return pix_acc
    
    def save_user_settings(self, chat_id):
        pix_acc = self.get_user_from_temp(chat_id)
        if pix_acc:
            cur = self.conn.cursor()
            cur.execute('UPDATE users SET last_id = %s, count = %s, only_pics = %s, by_one = %s WHERE chat_id = %s',
                    (pix_acc.last_id, pix_acc.count, pix_acc.only_pics, pix_acc.by_one, chat_id))
            self.conn.commit()
            cur.close()

    def set_user_to_temp(self, chat_id, pix_acc):
        self.temp[chat_id] = pix_acc
    
    def get_user_from_temp(self, chat_id):
        return self.temp.get(chat_id)
    
    def get_all_ids(self):
        cur = self.conn.cursor()
        cur.execute('SELECT chat_id FROM users')
        results = cur.fetchall()
        cur.close()
        return [r[0] for r in results]
    
    def get_user(self, chat_id, anyway=True):
        if chat_id is None:
            return self.pix
        user = self.get_user_from_temp(chat_id)
        if user is False:
            return self.pix if anyway else None
        elif not user:
            user = self.get_user_from_db(chat_id)
            self.set_user_to_temp(chat_id, user if user else False)
            if not user:
                return self.pix if anyway else None
        return user
        
    