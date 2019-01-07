import psycopg2
from dpixiv import DPixivIllusts

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
        last_id INTEGER)
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
                (chat_id, pix_acc.login, pix_acc.password, pix_acc.get_session(), pix_acc.tt))
        else:
            cur.execute('UPDATE users SET chat_id = %s, login = %s, password = %s, session = %s, tt = %s WHERE chat_id = %s',
                (pix_acc.login, pix_acc.password, pix_acc.get_session(), pix_acc.tt, chat_id))
        self.conn.commit()
        cur.close()
    
    def del_user(self, chat_id):
        cur = self.conn.cursor()
        cur.execute('DELETE FROM users WHERE chat_id = %s', (chat_id, ))
        self.conn.commit()
        cur.close()
    
    def get_user_from_db(self, chat_id):
        cur = self.conn.cursor()
        cur.execute('SELECT login, password, session, tt FROM users WHERE chat_id = %s', (chat_id, ))
        result = cur.fetchone()
        cur.close()
        if result:
            pix_acc = DPixivIllusts(*result)
            if pix_acc.tt:
                if pix_acc.get_session() != result[2] or pix_acc.tt != result[3]:
                    self.set_user(chat_id, pix_acc)
                return pix_acc

    def set_user_to_temp(self, chat_id, pix_acc):
        self.temp[chat_id] = pix_acc
    
    def get_user_from_temp(self, chat_id):
        return self.temp.get(chat_id)
    
    def get_user(self, chat_id, anyway=True):
        user = self.get_user_from_temp(chat_id)
        if user is False:
            return self.pix if anyway else None
        elif not user:
            user = self.get_user_from_db(chat_id)
            self.set_user_to_temp(chat_id, user if user else False)
            if not user:
                return self.pix if anyway else None
        return user
        
    