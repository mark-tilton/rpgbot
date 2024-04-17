import sqlite3
import time
from math import floor
from sqlite3 import Cursor
from typing import Optional, Mapping
from storage.activity import Activity, ActivityReward, ActivityType, Item


class StorageTransaction:
    def __init__(self, cursor: Cursor):
        self.cursor = cursor
        self.current_tick = floor(time.time())
    
    def start_activity(self, user_id: int, activity_type: ActivityType) -> Activity:
        self.cursor.execute("INSERT INTO player_activity VALUES(?, ?, ?, ?, ?)", 
            (None,
            user_id, 
            activity_type.value, 
            self.current_tick, 
            self.current_tick))
        if not self.cursor.lastrowid:
            raise Exception("Lost rowid for new activity")
        return Activity(
            activity_id=self.cursor.lastrowid, 
            user_id=user_id, 
            activity_type=activity_type, 
            start_tick=self.current_tick,
            last_updated=self.current_tick)
    
    def start_woodcutting(self, activity_id: int, log_type: Item):
        self.cursor.execute("INSERT INTO woodcutting_activity VALUES(?, ?)", 
            (activity_id, log_type.value))
    
    def update_activity(self, activity: Activity):
        self.cursor.execute("""
            UPDATE player_activity
            SET last_updated = ?
            WHERE activity_id = ?
            """, (self.current_tick, activity.activity_id))

    def apply_reward(self, activity: Activity, reward: ActivityReward):
        user_id = activity.user_id
        for item, quantity in reward.items.items():
            item_id = item.value
            res = self.cursor.execute("""
                SELECT quantity 
                FROM player_items 
                WHERE user_id = ? AND item_id = ?
                """, (user_id, item_id))
            current_quantity = res.fetchone()
            if current_quantity is None:
                self.cursor.execute("INSERT INTO player_items VALUES(?, ?, ?)", (user_id, item_id, quantity))
                continue
            self.cursor.execute("""
                UPDATE player_items 
                SET quantity = ? 
                WHERE user_id = ? AND item_id = ?
                """, (
                    current_quantity[0] + quantity,
                    user_id, 
                    item_id,
                ))


class StorageModel:
    def __init__(self):
        self._connection = sqlite3.connect("game_data.db")
        cursor = self._connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_activity(
                activity_id INTEGER PRIMARY KEY ASC,
                user_id INT, 
                activity_type INT, 
                start_tick INT,
                last_updated INT
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
            CREATE TABLE IF NOT EXISTS player_equipment(
                user_id INT,
                woodcutting_axe INT
            )
            """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS woodcutting_activity(
                activity_id INT,
                log_type INT
            )
            """)
        self._connection.commit()
        self._transaction:Optional[StorageTransaction] = None
        self._open_transactions:int = 0
    
    def __enter__(self) -> StorageTransaction:
        if not self._transaction:
            self._transaction = StorageTransaction(self._connection.cursor())
        self._open_transactions += 1
        return self._transaction

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._open_transactions -= 1
        if self._open_transactions == 0:
            self._connection.commit()
            self._transaction = None

    def get_player_items(self, user_id: int) -> Mapping[Item, int]:
        cursor = self._connection.cursor()
        result = cursor.execute("""
            SELECT 
                item_id,
                quantity 
            FROM player_items
            WHERE user_id = ?
        """, (user_id, ))
        items: Mapping[Item, int] = {}
        for item_id, quantity in result.fetchall():
            items[Item(item_id)] = quantity
        return items
    
    def get_woodcutting_info(self, activity_id:int) -> Optional[Item]:
        cursor = self._connection.cursor()
        result = cursor.execute("""
            SELECT log_type 
            FROM woodcutting_activity 
            WHERE activity_id = ?
            """, (activity_id, ))
        log_id = result.fetchone()
        if not log_id:
            return None
        return Item(log_id[0])

    def get_current_activity(self, user_id: int) -> Optional[Activity]:
        cursor = self._connection.cursor()
        result = cursor.execute("""
            SELECT 
                activity_id,
                user_id,
                activity_type,
                start_tick,
                last_updated
            FROM player_activity 
            WHERE user_id = ?
            ORDER BY start_tick DESC
            """, (user_id, ))
        row = result.fetchone()
        if row is None:
            return None
        activity_id, user_id, activity_type, start_tick, last_updated = row
        return Activity(
            activity_id=activity_id, 
            user_id=user_id,
            activity_type=ActivityType(activity_type), 
            start_tick=start_tick,
            last_updated=last_updated)

