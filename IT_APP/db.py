import os

DB_MODE = os.getenv("DB_MODE", "LOCAL")  # LOCAL or CLOUD

def get_connection():
    if DB_MODE == "LOCAL":
        import oracledb

        oracledb.init_oracle_client(
            lib_dir=r"D:\App\Zobair\product\11.2.0\client_1"
        )

        return oracledb.connect(
            user="mp_dec25",
            password="a",
            dsn="192.168.21.14:1521/testababil"
        )

    else:
        # Cloud / Render mode (NO Oracle)
        return None
