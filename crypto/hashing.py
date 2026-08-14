import hashlib
def get_file_hash(filename):
    with open (filename, "rb") as file:
        data =file.read()
    return hashlib.sha256(data).hexdigest()

if __name__ == "__main__":
    print(get_file_hash("hello.txt"))

