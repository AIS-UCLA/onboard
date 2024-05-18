import string, sys, os, secrets, sqlite3
from onboard.utils import DB

def add(db, days, desc):
  # generate password
  pw = ''.join(secrets.choice(string.ascii_letters) for i in range(16))
  db.execute("INSERT INTO passwords VALUES (?, ?, ?)", (pw, f"datetime('now', '+{days} days')", desc))
  db.commit()
  print(f"New password: {pw}, expiring in {days} days")

def expired(db):
  expired = db.execute("SELECT * FROM passwords WHERE expire < datetime()").fetchall()
  print(f"There are {len(expired)} expired passwords in the database")

def onboardctl():
  try: db = sqlite3.connect(DB)
  except:
    print("Failed to open onboard database")
    exit(1)
  count_expired(db)
  if len(sys.argv) < 2:
    print("Must specify a command")
    exit(1)
    db.close()
  match sys.argv[1:]:
    case ["add", days, desc]: add(db, days, desc)
    case ["add", *_]:
      print("Invalid arguments for add, should be days until expiration and description")
      db.close()
      exit(1)
    case ["clear" *_]:
      db.execute("DELETE FROM passwords WHERE expire < datetime()")
      db.commit()
    case [cmd, *_]:
      print(f"Unrecognized command: {cmd}")
      db.close()
      exit(1)
  db.close()

