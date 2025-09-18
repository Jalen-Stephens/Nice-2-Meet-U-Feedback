import pymysql

def main():
    # Replace with your own connection details
    connection = pymysql.connect(
        host="10.128.0.6",       # or your server IP / hostname
        user="dbuser",          # MySQL username
        password="dbuserdbuser",  # MySQL password
        port=3306               # Default MySQL port
    )

    try:
        with connection.cursor() as cursor:
            # Run a simple query
            cursor.execute("show databases;")
            version = cursor.fetchone()
            print("MySQL version:", version[0])

    finally:
        connection.close()

if __name__ == "__main__":
    main()
