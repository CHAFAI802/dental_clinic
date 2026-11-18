import os
from urllib.parse import unquote, urlsplit

import psycopg2
from psycopg2 import sql


ADMIN_USER = "dental"
DATABASE = "dental"

ROLE_CONFIG = {
    "dental_migrator": {
        "url_variable": "DATABASE_URL_MIGRATOR",
    },
    "dental_runtime": {
        "url_variable": "DATABASE_URL_RUNTIME",
    },
}


def get_url_password(variable, expected_user):
    value = os.environ.get(variable)
    if not value:
        raise RuntimeError(f"Variable {variable} absente.")

    parsed = urlsplit(value)

    if parsed.username != expected_user:
        raise RuntimeError(f"Utilisateur inattendu dans {variable}.")

    if parsed.hostname != "db" or parsed.port != 5432:
        raise RuntimeError(f"Connexion inattendue dans {variable}.")

    if parsed.path != "/dental" or not parsed.password:
        raise RuntimeError(f"URL invalide dans {variable}.")

    return unquote(parsed.password)


def ensure_role(cursor, role, password):
    cursor.execute(
        "SELECT 1 FROM pg_roles WHERE rolname = %s",
        (role,),
    )

    if cursor.fetchone() is None:
        cursor.execute(
            sql.SQL("CREATE ROLE {}").format(sql.Identifier(role))
        )

    cursor.execute(
        sql.SQL(
            """
            ALTER ROLE {}
            WITH LOGIN
            NOSUPERUSER
            NOCREATEDB
            NOCREATEROLE
            NOREPLICATION
            NOBYPASSRLS
            PASSWORD {}
            """
        ).format(
            sql.Identifier(role),
            sql.Literal(password),
        )
    )

    print(f"Rôle {role} configuré.")


def main():
    admin_password = os.environ.get("POSTGRES_PASSWORD")
    if not admin_password:
        raise RuntimeError("POSTGRES_PASSWORD absente.")

    passwords = {
        role: get_url_password(config["url_variable"], role)
        for role, config in ROLE_CONFIG.items()
    }

    connection = psycopg2.connect(
        host="db",
        port=5432,
        dbname=DATABASE,
        user=ADMIN_USER,
        password=admin_password,
        connect_timeout=10,
    )

    try:
        connection.autocommit = False

        with connection.cursor() as cursor:
            for role, password in passwords.items():
                ensure_role(cursor, role, password)

            cursor.execute(
                "ALTER DATABASE dental OWNER TO dental_migrator"
            )

            cursor.execute(
                "REVOKE ALL PRIVILEGES ON DATABASE dental FROM PUBLIC"
            )

            cursor.execute(
                "GRANT CONNECT ON DATABASE dental TO dental_runtime"
            )

            cursor.execute(
                "ALTER SCHEMA public OWNER TO dental_migrator"
            )

            cursor.execute(
                "REVOKE ALL ON SCHEMA public FROM PUBLIC"
            )

            cursor.execute(
                "GRANT USAGE, CREATE ON SCHEMA public TO dental_migrator"
            )

            cursor.execute(
                "GRANT USAGE ON SCHEMA public TO dental_runtime"
            )

            cursor.execute(
                """
                GRANT SELECT, INSERT, UPDATE, DELETE
                ON ALL TABLES IN SCHEMA public
                TO dental_runtime
                """
            )

            cursor.execute(
                """
                GRANT USAGE, SELECT, UPDATE
                ON ALL SEQUENCES IN SCHEMA public
                TO dental_runtime
                """
            )

            cursor.execute(
                """
                ALTER DEFAULT PRIVILEGES
                FOR ROLE dental_migrator
                IN SCHEMA public
                GRANT SELECT, INSERT, UPDATE, DELETE
                ON TABLES TO dental_runtime
                """
            )

            cursor.execute(
                """
                ALTER DEFAULT PRIVILEGES
                FOR ROLE dental_migrator
                IN SCHEMA public
                GRANT USAGE, SELECT, UPDATE
                ON SEQUENCES TO dental_runtime
                """
            )

        connection.commit()
        print("Initialisation PostgreSQL terminée.")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()
