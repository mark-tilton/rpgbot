import sqlite3
from sqlite3 import Cursor
from typing import Optional, Mapping
from storage.datatypes import Activity, ActivityReward, ActivityType, Item

class StorageModel:
    def __init__(self):
        self.connection = sqlite3.connect("game_data.db")
        cursor = self.connection.cursor()
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
                user_id, 
                item_id, 
                quantity
            )
            """)
        self.connection.commit()
    
    def get_current_activity(self, user_id: int) -> Optional[Activity]:
        cursor = self.connection.cursor()
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

    def start_activity(self, user_id: int, activity_type: ActivityType, start_tick: int) -> Activity:
        cursor = self.connection.cursor()
        cursor.execute("INSERT INTO player_activity VALUES(?, ?, ?, ?, ?)", 
            (None,
            user_id, 
            activity_type.value, 
            start_tick, 
            start_tick))
        self.connection.commit()
        if not cursor.lastrowid:
            raise Exception("Lost rowid for new activity")
        return Activity(
            activity_id=cursor.lastrowid, 
            user_id=user_id, 
            activity_type=activity_type, 
            start_tick=start_tick,
            last_updated=start_tick)
    
    def update_activity(self, activity: Activity, reward: Optional[ActivityReward], current_tick: int):
        cursor = self.connection.cursor()
        if reward is not None:
            self._apply_reward(cursor, activity, reward)
        cursor.execute("""
            UPDATE player_activity
            SET last_updated = ?
            WHERE activity_id = ?
            """, (current_tick, activity.activity_id))
        self.connection.commit()

    def _apply_reward(self, cursor: Cursor, activity: Activity, reward: ActivityReward):
        user_id = activity.user_id
        for item, quantity in reward.items.items():
            item_id = item.value
            res = cursor.execute("""
                SELECT quantity 
                FROM player_items 
                WHERE user_id = ? AND item_id = ?
                """, (user_id, item_id))
            current_quantity = res.fetchone()
            if current_quantity is None:
                cursor.execute("INSERT INTO player_items VALUES(?, ?, ?)", (user_id, item_id, quantity))
                continue
            cursor.execute("""
                UPDATE player_items 
                SET quantity = ? 
                WHERE user_id = ? AND item_id = ?
                """, (
                    current_quantity[0] + quantity,
                    user_id, 
                    item_id,
                ))
    
    def get_player_items(self, user_id: int) -> Mapping[Item, int]:
        cursor = self.connection.cursor()
        res = cursor.execute("""
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


def main():
    model = StorageModel()
    model.start_activity(0, ActivityType.COMBAT, 0)
    model.start_activity(0, ActivityType.COMBAT, 3)
    model.start_activity(0, ActivityType.COMBAT, 6)
    activity = model.get_current_activity(0)
    print(activity)

if __name__ == "__main__":
    main()