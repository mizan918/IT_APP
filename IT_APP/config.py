import oracledb

# Oracle DB configuration
DB_USER = "me_aug25"          # e.g., system or IT_APP_USER
DB_PASSWORD = "a"  # replace with your real password
DB_HOST = "192.168.21.15"         # application server IP
DB_PORT = 1521
DB_SERVICE = "ORCL"               # replace with your actual service name if different

def get_connection():
    """
    Create and return a database connection.
    """
    dsn = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
    conn = oracledb.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        dsn=dsn
    )
    return conn
