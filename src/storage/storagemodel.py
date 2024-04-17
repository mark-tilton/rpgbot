import sqlite3
import time
from math import floor
from sqlite3 import Cursor
from typing import Optional, Mapping
from storage.equipment import Equipment
from storage.activity import Activity, ActivityType, Item


class StorageTransaction:
    def __init__(self, cursor: Cursor):
        self.current_tick = floor(time.time())
        self._cursor = cursor
        self._rollback = False
    
    def cancel(self):
        self._rollback = True
    
    def start_activity(self, user_id: int, activity_type: ActivityType) -> Activity:
        self._cursor.execute("INSERT INTO player_activity VALUES(?, ?, ?, ?, ?)", 
            (None,
            user_id, 
            activity_type.value, 
            self.current_tick, 
            self.current_tick))
        if not self._cursor.lastrowid:
            raise Exception("Lost rowid for new activity")
        return Activity(
            activity_id=self._cursor.lastrowid, 
            user_id=user_id, 
            activity_type=activity_type, 
            start_tick=self.current_tick,
            last_updated=self.current_tick)

    def update_activity(self, activity: Activity):
        self._cursor.execute("""
            UPDATE player_activity
            SET last_updated = ?
            WHERE activity_id = ?
            """, (self.current_tick, activity.activity_id))
    
    def start_woodcutting(self, activity_id: int, log_type: Item):
        self._cursor.execute("INSERT INTO woodcutting_activity VALUES(?, ?)", 
            (activity_id, log_type.value))
    
    def add_item(self, user_id: int, item: Item, quantity: int):
        item_id = item.value
        result = self._cursor.execute("""
            SELECT quantity 
            FROM player_items 
            WHERE user_id = ? AND item_id = ?
            """, (user_id, item_id))
        current_quantity = result.fetchone()
        if current_quantity is None:
            self._cursor.execute("INSERT INTO player_items VALUES(?, ?, ?)", (user_id, item_id, quantity))
            return
        self._cursor.execute("""
            UPDATE player_items 
            SET quantity = ? 
            WHERE user_id = ? AND item_id = ?
            """, (
                current_quantity[0] + quantity,
                user_id, 
                item_id,
            ))
    
    def remove_item(self, user_id: int, item: Item, quantity: int) -> bool:
        item_id = item.value
        result = self._cursor.execute("""
            SELECT quantity 
            FROM player_items 
            WHERE user_id = ? AND item_id = ?
            """, (user_id, item_id))
        current_quantity = result.fetchone()
        if current_quantity is None or current_quantity[0] < quantity:
            return False
        self._cursor.execute("""
            UPDATE player_items 
            SET quantity = ? 
            WHERE user_id = ? AND item_id = ?
            """, (
                current_quantity[0] - quantity,
                user_id, 
                item_id,
            ))
        return True
    
    def set_equipment(self, user_id: int, equipment: Equipment):
        result = self._cursor.execute("""
            SELECT *
            FROM player_equipment
            WHERE user_id = ?
        """, (user_id, ))
        row = result.fetchone()
        if row is None:
            self._cursor.execute("INSERT INTO player_equipment VALUES(?, ?)", (
                user_id, 
                equipment.woodcutting_axe.value,
            ))
        self._cursor.execute("""
            UPDATE player_equipment 
            SET woodcutting_axe = ? 
            WHERE user_id = ?
            """, (
                equipment.woodcutting_axe.value,
                user_id, 
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
            CREATE TABLE IF NOT EXISTS woodcutting_activity(
                activity_id INT,
                log_type INT
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
            if self._transaction and self._transaction._rollback:
                self._connection.rollback()
            else:
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
            if quantity <= 0:
                continue
            items[Item(item_id)] = quantity
        return items
    
    def get_player_equipment(self, user_id: int) -> Equipment:
        cursor = self._connection.cursor()
        result = cursor.execute("""
            SELECT 
                woodcutting_axe
            FROM player_equipment
            WHERE user_id = ?
        """, (user_id, ))
        row = result.fetchone()
        if row is None:
            return Equipment()
        return Equipment(woodcutting_axe=Item(row[0]))

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
