import sqlite3


class Database:
    def __init__(self) -> None:
        self.db = sqlite3.connect("database.db")
        self.cursor = self.db.cursor()

    def __del__(self) -> None:
        self.cursor.close()
        self.db.close()

    def setup(self) -> None:
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS server (
                id INTEGER PRIMARY KEY,
                welcome_channel_id INTEGER,
                one_piece_channel_id INTEGER,
                role_message_id INTEGER
            )
            """
        )
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS data (
                id INTEGER PRIMARY KEY,
                value TEXT
            )
            """
        )
        self.db.commit()

    def get_welcome_channel_id(self, guild_id: int) -> int | None:
        self.cursor.execute(
            f"""
            SELECT welcome_channel_id
            FROM server
            WHERE id = {guild_id}
            """
        )
        value = self.cursor.fetchone()
        return value[0] if value is not None else None

    def set_welcome_channel_id(self, guild_id: int, welcome_channel_id: int | None) -> None:
        self.cursor.execute(
            f"""
            INSERT INTO server (id, welcome_channel_id)
            VALUES ({guild_id}, {welcome_channel_id or "NULL"})
            ON CONFLICT(id) DO UPDATE SET welcome_channel_id = {welcome_channel_id or "NULL"}
            """
        )
        self.db.commit()

    def get_one_piece_channels_id(self) -> list[int]:
        self.cursor.execute(
            """
            SELECT one_piece_channel_id
            FROM server
            """
        )
        return [value[0] for value in self.cursor.fetchall() if value[0] is not None]

    def set_one_piece_channel_id(self, guild_id: int, one_piece_channel_id: int | None) -> None:
        self.cursor.execute(
            f"""
            INSERT INTO server (id, one_piece_channel_id)
            VALUES ({guild_id}, {one_piece_channel_id or "NULL"})
            ON CONFLICT(id) DO UPDATE SET one_piece_channel_id = {one_piece_channel_id or "NULL"}
            """
        )
        self.db.commit()

    def get_one_piece_chapter(self) -> int | None:
        self.cursor.execute(
            """
            SELECT value
            FROM data
            WHERE id = 0
            """
        )
        value = self.cursor.fetchone()
        return int(value[0]) if value is not None else None

    def set_one_piece_chapter(self, chapter: int) -> None:
        self.cursor.execute(
            f"""
            INSERT INTO data (id, value)
            VALUES (0, {chapter})
            ON CONFLICT(id) DO UPDATE SET value = {chapter}
            """
        )
        self.db.commit()

    def get_role_message_id(self, guild_id: int) -> int | None:
        self.cursor.execute(
            f"""
            SELECT role_message_id
            FROM server
            WHERE id = {guild_id}
            """
        )
        value = self.cursor.fetchone()
        return value[0] if value is not None else None

    def set_role_message_id(self, guild_id: int, message_id: int | None) -> None:
        self.cursor.execute(
            f"""
            INSERT INTO server (id, role_message_id)
            VALUES ({guild_id}, {message_id or "NULL"})
            ON CONFLICT(id) DO UPDATE SET role_message_id = {message_id or "NULL"}
            """
        )
        self.db.commit()


db = Database()
