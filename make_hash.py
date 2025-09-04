import sys
from passlib.hash import bcrypt
from getpass import getpass

# Se vier argumento, usa; senão pede no terminal sem eco
pwd = sys.argv[1] if len(sys.argv) > 1 else getpass("panico13")
print(bcrypt.hash(pwd))
