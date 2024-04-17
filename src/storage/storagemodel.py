import sqlite3
from sqlite3 import Cursor
from typing import Optional, Mapping
from storage.activity import Activity, ActivityReward, ActivityType, Item


class StorageTransaction:
    def __init__(self, cursor: Cursor):
        self.cursor = cursor
    
    def get_current_activity(self, user_id: int) -> Optional[Activity]:
        result = self.cursor.execute("""
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

    def start_activity(self, user_id: int, activity_type: ActivityType, start_tick: int) -> Activity:
        self.cursor.execute("INSERT INTO player_activity VALUES(?, ?, ?, ?, ?)", 
            (None,
            user_id, 
            activity_type.value, 
            start_tick, 
            start_tick))
        if not self.cursor.lastrowid:
            raise Exception("Lost rowid for new activity")
        return Activity(
            activity_id=self.cursor.lastrowid, 
            user_id=user_id, 
            activity_type=activity_type, 
            start_tick=start_tick,
            last_updated=start_tick)
    
    def update_activity(self, activity: Activity, current_tick: int):
        self.cursor.execute("""
            UPDATE player_activity
            SET last_updated = ?
            WHERE activity_id = ?
            """, (current_tick, activity.activity_id))

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
    
    def get_player_items(self, user_id: int) -> Mapping[Item, int]:
        res = self.cursor.execute("""
            SELECT 
                item_id,
                quantity 
            FROM player_items
            WHERE user_id = ?
        """, (user_id, ))
        items: Mapping[Item, int] = {}
        for item_id, quantity in res.fetchall():
            items[Item(item_id)] = quantity
        return items


class StorageModel:
    def __init__(self):
        self.connection = sqlite3.connect("game_data.db")
        cursor = self.connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_activity(
                activity_id INTEGER PRIMARY KEY ASC,
                user_id INTEGER, 
                activity_type INTEGER, 
                start_tick INTEGER,
                last_updated INTEGER
            )
            """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_items(
                user_id INTEGER, 
                item_id INTEGER, 
                quantity INTEGER
            )
            """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_equipment(
                user_id INTEGER,
                woodcutting_axe INTEGER
            )
            """)
        self.connection.commit()
    
    def __enter__(self) -> StorageTransaction:
        return StorageTransaction(self.connection.cursor())

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.connection.commit()

