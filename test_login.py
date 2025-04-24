# test_login.py

from werkzeug.security import check_password_hash
from dotenv import load_dotenv
import os

load_dotenv()  # Load .env from current folder

username_input = input("Enter username: ")
password_input = input("Enter password: ")

USERNAME = os.getenv("USERNAME")
PASSWORD_HASH = os.getenv("PASSWORD_HASH")

print("\n--- Debug Output ---")
print("Expected Username:", USERNAME)
print("Expected Hash:", PASSWORD_HASH)
print("You entered:", username_input, password_input)

# Validate
if username_input == USERNAME and check_password_hash(PASSWORD_HASH, password_input):
    print("\n✅ Login Successful!")
else:
    print("\n❌ Login Failed. Check username or password.")
