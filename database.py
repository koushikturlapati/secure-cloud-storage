import mysql.connector
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="mysql",
        database="secure_cloud"
    )
if __name__ == "__main__":
    connection = get_connection()

    if connection.is_connected():
        print("MySQL connection successful!")

    connection.close()