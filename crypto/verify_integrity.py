import hashlib

with open("file_hash.txt", "r") as file:
    original_hash = file.read()

with open("hello.txt", "rb") as file:
    data = file.read()

current_hash = hashlib.sha256(data).hexdigest()

if original_hash == current_hash:
    print("Integrity verified: File is unchanged")
else:
    print("Integrity check failed: File was modified")