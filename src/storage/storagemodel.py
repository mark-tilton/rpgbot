import sqlite3
from sqlite3 import Cursor
from typing import List, Optional, Mapping
from game.adventure import Adventure


class StorageTransaction:
    def __init__(self, cursor: Cursor):
        self._cursor = cursor
        self._rollback = False

    def cancel(self):
        self._rollback = True

    def start_adventure(
            self,
            user_id: int,
            zone_id: int,
            start_time: int) -> Adventure:
        self._cursor.execute(
            "INSERT INTO player_adventure VALUES(?, ?, ?, ?)",
            (None,
             user_id,
             zone_id,
             start_time))
        if not self._cursor.lastrowid:
            raise Exception("Lost rowid for new activity")
        return Adventure(
            adventure_id=self._cursor.lastrowid,
            user_id=user_id,
            zone_id=zone_id,
            last_updated=start_time)

    def update_adventure(self, adventure_id: int, last_updated: int):
        self._cursor.execute("""
            UPDATE player_adventure
            SET last_updated = ?
            WHERE adventure_id = ?
            """, (last_updated, adventure_id))

    def add_remove_item(
            self,
            user_id: int,
            item_id: int,
            quantity: int) -> bool:
        if quantity == 0:
            return True
        result = self._cursor.execute("""
            SELECT quantity
            FROM player_items
            WHERE user_id = ? AND item_id = ?
            """, (user_id, item_id))
        current_quantity = result.fetchone()
        if current_quantity is None:
            if quantity < 0:
                return False
            self._cursor.execute(
                """INSERT INTO player_items VALUES(?, ?, ?)""",
                (user_id, item_id, quantity))
            return True
        new_quantity = current_quantity[0] + quantity
        if new_quantity < 0:
            return False
        self._cursor.execute("""
            UPDATE player_items
            SET quantity = ?
            WHERE user_id = ? AND item_id = ?
            """, (
            current_quantity[0] + quantity,
            user_id,
            item_id,
        ))
        return True

    def set_open_quests(self, user_id: int, quests: List[int]):
        self._cursor.execute(
            "DELETE FROM open_quests WHERE user_id = ?", (user_id,))
        self._cursor.executemany(
            "INSERT INTO open_quests VALUES(?, ?, ?)",
            ((user_id, quest, i) for i, quest in enumerate(quests)))

    def set_player_zone(self, user_id: int, zone_id: int, arrival_time: int):
        self._cursor.execute(
            "INSERT INTO player_zone VALUES(?, ?, ?)",
            (user_id,
             zone_id,
             arrival_time))

    def add_zone_access(self, user_id: int, zone_id: int):
        self._cursor.execute(
            "INSERT INTO player_zone_access VALUES(?, ?)",
            (user_id, zone_id))

    def add_finished_quest(self, user_id: int, quest_id: int):
        self._cursor.execute(
            "INSERT INTO finished_quests VALUES(?, ?)",
            (user_id, quest_id))


class StorageModel:
    def __init__(self):
        self._connection = sqlite3.connect("game_data.db")
        cursor = self._connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_adventure(
                adventure_id INTEGER PRIMARY KEY ASC,
                user_id INT,
                zone_id INT,
                last_updated INT
            )
            """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_zone(
                user_id INT,
                zone_id INT,
                arrival_time INT
            )
            """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_zone_access(
                user_id INT,
                zone_id INT
            )
            """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS open_quests(
                user_id INT,
                quest_step_id INT,
                order_idx INT
            )
            """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_items(
                user_id INT,
                item_id INT,
                quantity INT
            )
            """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS finished_quests(
                user_id INT,
                quest_id INT
            )
            """)

        self._connection.commit()
        self._transaction: Optional[StorageTransaction] = None
        self._open_transactions: int = 0

    def __enter__(self) -> StorageTransaction:
        if not self._transaction:
            self._transaction = StorageTransaction(self._connection.cursor())
        self._open_transactions += 1
        return self._transaction

    def __exit__(self, exc_type, exc_value, exc_traceback):  # type: ignore
        self._open_transactions -= 1
        if self._open_transactions == 0:
            if (self._transaction and
                    self._transaction._rollback):  # type: ignore
                self._connection.rollback()
            else:
                self._connection.commit()
            self._transaction = None

    def get_player_items(self, user_id: int) -> Mapping[int, int]:
        cursor = self._connection.cursor()
        result = cursor.execute("""
            SELECT
                item_id,
                quantity
            FROM player_items
            WHERE user_id = ?
        """, (user_id, ))
        items: Mapping[int, int] = {}
        for item_id, quantity in result.fetchall():
            if quantity <= 0:
                continue
            items[item_id] = quantity
        return items

    def get_item_quantity(self, user_id: int, item_id: int) -> int:
        cursor = self._connection.cursor()
        result = cursor.execute("""
            SELECT
                quantity
            FROM player_items
            WHERE user_id = ? AND item_id = ?
        """, (user_id, item_id))
        row = result.fetchone()
        if row is None:
            return 0
        return row[0]

    def get_current_adventure(self, user_id: int) -> Optional[Adventure]:
        cursor = self._connection.cursor()
        result = cursor.execute("""
            SELECT *
            FROM player_adventure
            WHERE user_id = ?
            ORDER BY last_updated DESC
            """, (user_id, ))
        row = result.fetchone()
        if row is None:
            return None
        adventure_id, user_id, zone_id, last_updated = row
        return Adventure(
            adventure_id=adventure_id,
            user_id=user_id,
            zone_id=zone_id,
            last_updated=last_updated)

    def get_player_zone(self, user_id: int) -> Optional[int]:
        cursor = self._connection.cursor()
        result = cursor.execute("""
            SELECT
                zone_id,
                arrival_time
            FROM player_zone
            WHERE user_id = ?
            ORDER BY arrival_time DESC
            """, (user_id, ))
        row = result.fetchone()
        if row is None:
            return None
        zone_id, _ = row
        return zone_id

    def get_player_zone_access(self, user_id: int) -> List[int]:
        cursor = self._connection.cursor()
        result = cursor.execute("""
            SELECT zone_id
            FROM player_zone_access
            WHERE user_id = ?
            """, (user_id, ))
        return [zone_id[0] for zone_id in result.fetchall()]

    def get_open_quests(self, user_id: int) -> List[int]:
        cursor = self._connection.cursor()
        result = cursor.execute("""
            SELECT
                quest_step_id,
                order_idx
            FROM open_quests
            WHERE user_id = ?
            ORDER BY order_idx ASC
            """, (user_id, ))
        return [step_id for step_id, _ in result.fetchall()]

    def get_finished_quests(self, user_id: int) -> List[int]:
        cursor = self._connection.cursor()
        result = cursor.execute("""
            SELECT quest_id
            FROM finished_quests
            WHERE user_id = ?
            """, (user_id, ))
        return [quest_id[0] for quest_id in result.fetchall()]
