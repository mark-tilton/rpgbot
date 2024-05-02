import sqlite3
from sqlite3 import Cursor

from game.adventure import Adventure, AdventureGroup, AdventureStep
from game.tags import TagType, TagCollection
from game.quests import QUESTS


class StorageTransaction:
    def __init__(self, cursor: Cursor):
        self._cursor = cursor
        self._rollback = False

    def cancel(self):
        self._rollback = True

    def start_adventure(
        self, user_id: int, zone_id: str, start_time: int, thread_id: int
    ) -> Adventure:
        self._cursor.execute(
            "INSERT INTO player_adventure VALUES(?, ?, ?, ?, ?)",
            (None, user_id, zone_id, start_time, thread_id),
        )
        if not self._cursor.lastrowid:
            raise Exception("Lost rowid for new activity")
        return Adventure(
            adventure_id=self._cursor.lastrowid,
            user_id=user_id,
            zone_id=zone_id,
            last_updated=start_time,
            thread_id=thread_id,
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

    def increment_or_insert_quest_group(self, adventure_id: int, group_id: str):
        result = self._cursor.execute(
            """
            SELECT count 
            FROM quest_group_info 
            WHERE adventure_id = ? AND group_id = ?
            """,
            (adventure_id, group_id),
        )
        if result.fetchone() is None:
            self._cursor.execute(
                """
                INSERT INTO quest_group_info
                VALUES(?, ?, ?, ?)
                """,
                (adventure_id, group_id, 1, None),
            )
            return
        self._cursor.execute(
            """
            UPDATE quest_group_info
            SET count = count + 1
            WHERE adventure_id = ? AND group_id = ?
            """,
            (adventure_id, group_id),
        )

    def add_group_message(self, adventure_id: int, group_id: str, message_id: int):
        result = self._cursor.execute(
            """
            SELECT * 
            FROM quest_group_info 
            WHERE adventure_id = ? AND group_id = ?
            """,
            (adventure_id, group_id),
        )
        if result.fetchone() is None:
            raise Exception(
                f"No entry found for adventure: {adventure_id}, group: {group_id}"
            )
        self._cursor.execute(
            """
            UPDATE quest_group_info
            SET message_id = ?
            WHERE adventure_id = ? AND group_id = ?
            """,
            (message_id, adventure_id, group_id),
        )

    # TODO: Find a way to merge this with add_remove_tag
    def update_adventure_results(
        self,
        adventure_id: int,
        group_id: str,
        quest_id: str,
        tag_type: TagType,
        tag: str,
        quantity: int,
    ) -> bool:
        if quantity == 0:
            return True
        result = self._cursor.execute(
            """
            SELECT quantity
            FROM adventure_results
            WHERE 
                adventure_id = ? AND 
                group_id = ? AND 
                quest_id = ? AND 
                type = ? AND 
                tag = ?
            """,
            (adventure_id, group_id, quest_id, tag_type.value, tag),
        )

        current_quantity = result.fetchone()
        if current_quantity is None:
            self._cursor.execute(
                """INSERT INTO adventure_results VALUES(?, ?, ?, ?, ?, ?)""",
                (adventure_id, group_id, quest_id, tag_type.value, tag, quantity),
            )
            return True
        new_quantity = current_quantity[0] + quantity

        if new_quantity == 0:
            result = self._cursor.execute(
                """
                DELETE FROM adventure_results
                WHERE 
                    adventure_id = ? AND 
                    group_id = ? AND 
                    quest_id = ? AND 
                    type = ? AND 
                    tag = ?
                """,
                (adventure_id, group_id, quest_id, tag_type.value, tag),
            )
            return True

        self._cursor.execute(
            """
            UPDATE adventure_results
            SET quantity = ?
            WHERE 
                adventure_id = ? AND 
                group_id = ? AND 
                quest_id = ? AND 
                type = ? AND 
                tag = ?
            """,
            (new_quantity, adventure_id, group_id, quest_id, tag_type.value, tag),
        )
        return True


class StorageModel:
    def __init__(self):
        self._connection = sqlite3.connect("game_data.db")
        cursor = self._connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_adventure(
                adventure_id INTEGER PRIMARY KEY ASC,
                user_id INT,
                zone_id STR,
                last_updated INT,
                thread_id INT
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
            CREATE TABLE IF NOT EXISTS quest_group_info(
                adventure_id INT,
                group_id STR,
                count INT,
                message_id INT
            )
            """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS adventure_results(
                adventure_id INT,
                group_id STR,
                quest_id STR,
                type STR,
                tag STR,
                quantity INT
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
        adventure_id, user_id, zone_id, last_updated, thread_id = row
        return Adventure(
            adventure_id=adventure_id,
            user_id=user_id,
            zone_id=zone_id,
            last_updated=last_updated,
            thread_id=thread_id,
        )

    def get_player_tags(self, user_id: int) -> TagCollection:
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

        tag_collection = TagCollection()
        for tag, quantity, type in result.fetchall():
            tag_type = TagType(type)
            tag_collection.add_tag(tag_type, tag, quantity)
        return tag_collection

    def get_group_info(
        self, adventure_id: int, group_id: str
    ) -> tuple[int, int | None]:
        cursor = self._connection.cursor()
        result = cursor.execute(
            """
            SELECT
                count,
                message_id
            FROM quest_group_info
            WHERE adventure_id = ? AND group_id = ?
            """,
            (adventure_id, group_id),
        )
        row = result.fetchone()
        if row is None:
            return 0, None
        count, message_id = row
        return count, message_id

    def get_adventure_results(self, adventure_id: int, group_id: str) -> AdventureGroup:
        cursor = self._connection.cursor()
        result = cursor.execute(
            """
            SELECT 
                quest_id,
                type,
                tag,
                quantity
            FROM adventure_results
            WHERE 
                adventure_id = ? AND 
                group_id = ? 
            """,
            (adventure_id, group_id),
        )
        quest_map: dict[str, TagCollection] = {}
        for quest_id, tag_type, tag, quantity in result.fetchall():
            quest_tags = quest_map.get(quest_id, TagCollection())
            quest_tags.add_tag(TagType(tag_type), tag, quantity)
            quest_map[quest_id] = quest_tags
        adventure_steps: list[AdventureStep] = []
        for quest_id in group_id.split(","):
            changed_tags = quest_map.get(quest_id, TagCollection())
            adventure_step = AdventureStep(
                QUESTS[quest_id],
                tags_changed=changed_tags,
            )
            adventure_steps.append(adventure_step)
        return AdventureGroup(adventure_steps)
