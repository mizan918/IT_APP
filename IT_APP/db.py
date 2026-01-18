import oracledb

oracledb.init_oracle_client(lib_dir=r"D:\App\Zobair\product\11.2.0\client_1")

# Adjust username, password, and service name
dsn = "192.168.21.14:1521/testababil"   # If service name is different, replace ORCL

def get_connection():
    conn = oracledb.connect(
        user="mp_dec25",           # <-- replace with your Oracle username
        password="a",   # <-- replace with your Oracle password
        dsn=dsn
    )
    return conn
    
    
 
 