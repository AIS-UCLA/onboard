from multiprocessing.connection import Listener
from onboard.utils import TMPDIR, ETCDIR, AUTH, FIFO, DB
import subprocess, os, shutil, secrets, sqlite3

def setup_files():
  os.umask(0) # makes setting permissions work
  # first create folders
  if not os.path.exists(TMPDIR): os.mkdir(TMPDIR)
  if not os.path.exists(ETCDIR): os.mkdir(ETCDIR)
  # create authkey file, only accessible by onboard user (and root)
  print(f"Creating AUTHKEY file at {AUTH}.")
  if os.path.exists(AUTH): os.remove(AUTH)
  os.close(os.open(AUTH, flags=os.O_CREAT, mode=0o600))
  shutil.chown(AUTH, user="onboard", group="onboard")
  # write authkey to authfile
  f = open(AUTH, 'wb')
  auth = secrets.token_bytes(16)
  f.write(auth)
  f.close()
  # create db file, only accesible by onboard user (and root)
  if not os.path.exists(DB):
    print(f"Database not found, creating new database at {DB}.")
    os.close(os.open(DB, flags=os.O_CREAT, mode=0o600))
    shutil.chown(DB, user="onboard", group="onboard")
  print(f"Opening database at {DB}.")
  db = sqlite3.connect(DB)
  db.execute("""CREATE TABLE IF NOT EXISTS users(
    username TEXT PRIMARY KEY,
    name TEXT,
    email TEXT,
    phone TEXT,
    add_time TEXT
  ) STRICT""")
  db.execute("""CREATE TABLE IF NOT EXISTS passwords(
    id INTEGER PRIMARY KEY,
    password TEXT,
    expire TEXT,
    desc TEXT
  ) STRICT""")
  db.commit()
  db.close()
  return auth

def daemon():
  print("Onboard daemon starting...")
  if os.getuid() != 0:
    print("Onboard daemon must be run as root.")
    exit(1)
  key = setup_files()
  print("Onboard daemon ready.")
  with Listener(FIFO, authkey=key) as listener:
    while True:
      with listener.accept() as conn:
        pw, name, username, key = conn.recv()
        subprocess.run(["useradd", "-d", "-p", pw, "-c", name, username])
        subprocess.run(["passwd", "--expire", username])
        os.mkdir(f"/home/{username}/.ssh")
        with open("/home/{username}/.ssh/authorized_keys", 'w') as f:
          f.write(key)
          f.write("\n")

