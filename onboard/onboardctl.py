import string, sys, os, secrets, sqlite3
from onboard.utils import DB

def add(days, desc):
  # generate password
  pw = ''.join(secrets.choice(string.ascii_letters) for i in range(16))
  db = sqlite3.connect(DB)
  db.execute("INSERT INTO passwords VALUES (?, ?, ?)", (pw, f"datetime('now', '+{days} days')", desc))
  db.commit()
  db.close()
  print(f"New password: {pw}, expiring in {days} days")

def onboardctl():
  if os.geteuid() != 0:
    print("Must be run as root.")
    exit(1)
  if len(sys.argv) < 2:
    print("Must specify a command")
    exit(1)
  match sys.argv[1:]:
    case ["add", days, desc]: add(days, desc)
    case ["add", *_]:
      print("Invalid arguments for add, should be days until expiration and description")
      exit(1)
    case [cmd, *_]:
      print(f"Unrecognized command: {cmd}")
      exit(1)

