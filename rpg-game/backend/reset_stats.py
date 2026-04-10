import sqlite3, os

# Base stats per class (from routes/character.py CLASS_STATS)
CLASS_STATS = {
    'Tauran':   dict(str_=14, dex=4,  con=12, int_=2,  wis=3,  cha=5),
    'Gnombaf':  dict(str_=3,  dex=5,  con=4,  int_=13, wis=11, cha=4),
    'Arachnid': dict(str_=5,  dex=15, con=4,  int_=6,  wis=5,  cha=5),
    'Angel':    dict(str_=4,  dex=6,  con=6,  int_=7,  wis=12, cha=11),
}

db = os.path.join(os.path.dirname(__file__), 'rpg.db')
conn = sqlite3.connect(db)
cur = conn.cursor()

cur.execute('SELECT c.id, c.char_class FROM characters c JOIN users u ON c.user_id = u.id WHERE u.username = ?', ('test',))
row = cur.fetchone()
if not row:
    print('User test not found')
    conn.close()
    exit()

char_id, char_class = row
print(f'Class: {char_class}')

s = CLASS_STATS.get(char_class)
if not s:
    print(f'Unknown class: {char_class}')
    conn.close()
    exit()

cur.execute('''
    UPDATE characters SET
        "str" = ?, dex = ?, con = ?, "int" = ?, wis = ?, cha = ?
    WHERE id = ?
''', (s['str_'], s['dex'], s['con'], s['int_'], s['wis'], s['cha'], char_id))
conn.commit()

cur.execute('SELECT "str", dex, con, "int", wis, cha FROM characters WHERE id = ?', (char_id,))
print('Reset to:', cur.fetchone())
conn.close()
