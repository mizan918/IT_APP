import os
import oracledb

def get_connection():

    db_mode = os.getenv("DB_MODE", "LOCAL").upper()

    if db_mode == "LOCAL":
        oracle_client_path = os.getenv("ORACLE_CLIENT_PATH")

        if not oracle_client_path:
            raise RuntimeError("ORACLE_CLIENT_PATH not set for LOCAL mode")

        try:
            oracledb.init_oracle_client(lib_dir=oracle_client_path)
        except oracledb.ProgrammingError:
            pass

    return oracledb.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        dsn=os.getenv("DB_DSN")
    )
