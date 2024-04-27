import sqlite3
from collections.abc import Mapping
from enum import Enum
from sqlite3 import Cursor

from game.adventure import Adventure


class TagType(Enum):
    ITEM = "item"


class StorageTransaction:
    def __init__(self, cursor: Cursor):
        self._cursor = cursor
        self._rollback = False

    def cancel(self):
        self._rollback = True

    def start_adventure(self, user_id: int, zone_id: str, start_time: int) -> Adventure:
        self._cursor.execute(
            "INSERT INTO player_adventure VALUES(?, ?, ?, ?)",
            (None, user_id, zone_id, start_time),
        )
        if not self._cursor.lastrowid:
            raise Exception("Lost rowid for new activity")
        return Adventure(
            adventure_id=self._cursor.lastrowid,
            user_id=user_id,
            zone_id=zone_id,
            last_updated=start_time,
        )

    def update_adventure(self, adventure_id: int, last_updated: int):
        self._cursor.execute(
            """
            UPDATE player_adventure
            SET last_updated = ?
            WHERE adventure_id = ?
            """,
            (last_updated, adventure_id),
        )

    def add_remove_tag(
        self, user_id: int, tag_type: TagType, tag: str, quantity: int
    ) -> bool:
        if quantity == 0:
            return True
        result = self._cursor.execute(
            """
            SELECT quantity
            FROM player_tags
            WHERE user_id = ? AND type = ? AND tag = ?
            """,
            (user_id, tag_type.value, tag),
        )

        current_quantity = result.fetchone()
        if current_quantity is None:
            if quantity <= 0:
                return False
            self._cursor.execute(
                """INSERT INTO player_tags VALUES(?, ?, ?, ?)""",
                (user_id, tag_type.value, tag, quantity),
            )
            return True
        new_quantity = current_quantity[0] + quantity

        if new_quantity < 0:
            return False

        if new_quantity == 0:
            result = self._cursor.execute(
                """
                DELETE FROM player_tags
                WHERE user_id = ? AND type = ? AND tag = ?
                """,
                (user_id, tag_type.value, tag),
            )
            return True

        self._cursor.execute(
            """
            UPDATE player_tags
            SET quantity = ?
            WHERE user_id = ? AND type = ? AND tag = ?
            """,
            (
                current_quantity[0] + quantity,
                user_id,
                tag_type.value,
                tag,
            ),
        )
        return True

    def add_zone_access(self, user_id: int, zone_id: str):
        self._cursor.execute(
            "INSERT INTO player_zone_access VALUES(?, ?)", (user_id, zone_id)
        )


class StorageModel:
    def __init__(self):
        self._connection = sqlite3.connect("game_data.db")
        cursor = self._connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_adventure(
                adventure_id INTEGER PRIMARY KEY ASC,
                user_id INT,
                zone_id STR,
                last_updated INT
            )
            """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_tags(
                user_id INT,
                type STR,
                tag STR,
                quantity INT
            )
            """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_zone_access(
                user_id INT,
                zone_id STR
            )
            """)

        self._connection.commit()
        self._transaction: StorageTransaction | None = None
        self._open_transactions: int = 0

    def __enter__(self) -> StorageTransaction:
        if not self._transaction:
            self._transaction = StorageTransaction(self._connection.cursor())
        self._open_transactions += 1
        return self._transaction

    def __exit__(self, exc_type, exc_value, exc_traceback):  # type: ignore
        self._open_transactions -= 1
        if self._open_transactions == 0:
            if self._transaction and self._transaction._rollback:  # type: ignore
                self._connection.rollback()
            else:
                self._connection.commit()
            self._transaction = None

    def get_current_adventure(self, user_id: int) -> Adventure | None:
        cursor = self._connection.cursor()
        result = cursor.execute(
            """
            SELECT *
            FROM player_adventure
            WHERE user_id = ?
            ORDER BY last_updated DESC
            """,
            (user_id,),
        )
        row = result.fetchone()
        if row is None:
            return None
        adventure_id, user_id, zone_id, last_updated = row
        return Adventure(
            adventure_id=adventure_id,
            user_id=user_id,
            zone_id=zone_id,
            last_updated=last_updated,
        )

    def get_player_tags(self, user_id: int) -> Mapping[TagType, Mapping[str, int]]:
        cursor = self._connection.cursor()
        result = cursor.execute(
            """
            SELECT
                tag,
                quantity,
                type
            FROM player_tags
            WHERE user_id = ?
        """,
            (user_id,),
        )

        tag_type_map: dict[TagType, dict[str, int]] = {}
        for tag, quantity, tag_type in result.fetchall():
            tag_quantity = tag_type_map.get(TagType(tag_type), {})
            tag_quantity[tag] = quantity
            tag_type_map[TagType(tag_type)] = tag_quantity

        return tag_type_map

    def get_player_zone_access(self, user_id: int) -> list[str]:
        cursor = self._connection.cursor()
        result = cursor.execute(
            """
            SELECT zone_id
            FROM player_zone_access
            WHERE user_id = ?
            """,
            (user_id,),
        )
        return [zone_id[0] for zone_id in result.fetchall()]
