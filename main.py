from crypto.file_manager import upload_file, download_file
def main():
    upload_file("hello.txt")
    download_file("hello.txt.enc")
if __name__ == "__main__":
    main()    