from getpass import getpass
from pwd import getpwall
from crypt import crypt
from multiprocessing.connection import Client
import re, secrets, subprocess, sqlite3

from onboard.utils import AUTH, DB, FIFO

PW_RE       = r"^[a-zA-Z]{16}$"
USERNAME_RE = r"^[a-z_]([a-z0-9_-]{0,31}|[a-z0-9_-]{0,30}\$)$"
NAME_RE     = r"^[A-Z]\w* ([A-Z]\w* ?)+$"
EMAIL_RE    = r"^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$"
PHONE_RE    = r"^[0-9]{10}$"
KEY_RE      = r"^ssh-(ed25519|rsa|dss|ecdsa) AAAA(?:[A-Za-z0-9+\/]{4})*(?:[A-Za-z0-9+\/]{2}==|[g$A-Za-z0-9+\/]{3}=|[A-Za-z0-9+\/]{4})( [^@]+@[^@]+)?$"


def check_pw(pw):
  db = sqlite3.connect(DB)
  query = db.execute("""SELECT id FROM passwords
  WHERE password = ? AND expire > datetime()""", (pw,)).fetchone()
  # TODO: Log failed attempts...
  if not query:
    db.close()
    return False
  db.execute("DELETE FROM passwords WHERE id = ?", (query[0],))
  db.commit()
  db.close()
  return True

def get_authkey():
  with open(AUTH, 'rb') as f: return f.read()

def lambdaify(v):
  if callable(v): return v
  # check if v is a regex (str)
  if isinstance(v, str): return lambda s: bool(re.match(v, s))
  print("FATAL ERROR, contact administrator")
  exit(1)

def input_verify(prompt, *verifiers):
  verifiers = [(lambdaify(v), err) for (v, err) in verifiers]
  while True:
    i = input(prompt)
    if all([True if v(i) else print(err) for (v, err) in verifiers]):
      break
  return i

def create_user():
  print("Beginning account creation.")
  print()
  print("As part of this server's acceptable use policy, please note that")
  print("your account may be terminated at any time, for any reason, including,")
  print("but not limited to, entering incorrect information during this setup")
  print("process.")
  print()

  username = input_verify("Enter your desired username (eg. joe): ",
                          (USERNAME_RE, "Invalid username"),
                          (lambda s: s not in [e.pw_name for e in getpwall()], "Username taken."))
  password = secrets.token_urlsafe(8)
  name = input_verify("Enter your full name (eg. Joe Bruin): ", (NAME_RE, "Invalid name"))
  email = input_verify("Enter your email (visible to other server users): ", (EMAIL_RE, "Invalid email"))
  phone = input_verify("Enter your phone number (only visible to admins) (eg. 6175551234): " (PHONE_RE, "Invalid phone"))

  print("In order to access this server, you must first setup an ssh key.")
  print("If you do not already have an ssh key, you must create one to proceed.")
  print("Choose one of the guides below based on your prefered ssh client:")
  print("  PuTTY on Windows: https://www.ssh.com/academy/ssh/putty/windows/puttygen")
  print("  OpenSSH (choose this if unsure): https://www.ssh.com/academy/ssh/keygen")
  print("Note: This server supports ed25519, rsa, dss, and ecdsa.")
  print("After completing one of the above guides, you should have a .pub file,") 
  print("containing your public key. Copy the contents of this file.")
  key = input_verify("Paste your ssh (public) key here: ",
                     (KEY_RE, "Invalid ssh key (supports ed25519, rsa, dss, ecdsa)"))

  with Client(FIFO, authkey=get_authkey()) as conn:
    conn.send([crypt(password, '22'), name, username, key])

  db = sqlite3.connect(DB)
  db.execute("INSERT INTO users VALUES (?, ?, ?, ?, datetime())", (username, name, email, phone))
  db.commit()
  db.close()

  print(f"User account created, temporary password: {password}")
  print("Please login to new user and reset password to prevent automatic account termination.")


def onboard():
  print("Welcome to AI Safety at UCLA's automated onboarding tool.")
  pw = input_verify("Please enter your password: ", (PW_RE, "Invalid password"))
  if check_pw(pw):
    print("Password authenticated...")
    create_user()
  else:
    print("Password not recognized")
    exit(1)

