from secrets import token_bytes
for i in range(5):
   key = token_bytes(32)
   print(key.hex())