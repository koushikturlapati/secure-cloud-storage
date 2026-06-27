from cryptography.fernet import Fernet
key = Fernet.generate_key()
with open("secret.key", "wb")as file:
    file.write(key)
cipher = Fernet(key)
print(key)
with open("hello.txt", "rb") as file:
    data = file.read()
encrypted_data = cipher.encrypt(data)
print(type(encrypted_data))
print("File encrypted successfully")
with open("encrypted.bin", "wb") as file:
    file.write(encrypted_data)
with open("encrypted.bin", "rb") as file:
    data = file.read()
decrypted_data = cipher.decrypt(data)
print(decrypted_data)