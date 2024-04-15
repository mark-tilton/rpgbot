from dataclasses import dataclass
import sqlite3
from sqlite3 import Cursor, Connection
import time
from typing import List, Optional
from datatypes import Activity, ActivityReward, ActivityType

@dataclass
class Player:
    id: int
    name: str

class StorageModel:
    def __init__(self):
        self.connection = sqlite3.connect("game_data.db")

    def init_tables(self):
        cursor = self.connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_activity(
                user_id INT, 
                activity_id INT, 
                start_tick INT,
                channel_id INT, 
                message_id INT
            )
            """)
        cursor.execute("CREATE TABLE IF NOT EXISTS player_skills(user_id, combat_xp, woodcutting_xp, mining_xp)")
        cursor.execute("CREATE TABLE IF NOT EXISTS player_items(user_id, item_id, quantity)")
        self.connection.commit()
    
    def get_current_activity(self, user_id: int) -> Optional[Activity]:
        cursor = self.connection.cursor()
        result = cursor.execute("SELECT * FROM player_activity WHERE user_id = ?", (user_id, ))
        row = result.fetchone()
        if row is None:
            return None
        activity_id, start_tick, channel_id, message_id = row[1:]
        return Activity(ActivityType(activity_id), start_tick, channel_id, message_id)

    def stop_activity(self, user_id: int):
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM player_activity WHERE user_id = ?", (user_id, ))

    def start_activity(self, user_id: int, activity: Activity):
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM player_activity WHERE user_id = ?", (user_id, ))
        cursor.execute("INSERT INTO player_activity VALUES(?, ?, ?, ?, ?)", 
                       (user_id, 
                       activity.activity_type.value, 
                       activity.start_tick, 
                       activity.channel_id, 
                       activity.message_id))
        self.connection.commit()

    def apply_reward(self, user_id: int, reward: ActivityReward):
        cursor = self.connection.cursor()
        for item, quantity in reward.items.items():
            item_id = item.value
            res = cursor.execute("SELECT quantity FROM player_items WHERE user_id = ? AND item_id = ?", (user_id, item_id))
            current_quantity = (res.fetchone() or (0, ))[0]
            cursor.execute("DELETE FROM player_items WHERE user_id = ? AND item_id = ?", (user_id, item_id))
            cursor.execute("INSERT INTO player_items VALUES(?, ?, ?)", (user_id, item_id, current_quantity + quantity))
        self.connection.commit()


def main():
    model = StorageModel()
    model.init_tables()
    activity = model.get_current_activity(0)
    print(activity)

if __name__ == "__main__":
    main()