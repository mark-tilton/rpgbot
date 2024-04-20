import random
from game.quests import QUESTS, ROOT_QUESTS, Quest
from game.items import ITEMS

INDENT_SIZE = 2
def display_quest_chain(quest: Quest, chance: float = 100, indent: int = 0):
    indent_str = " " * indent
    reqs_str = ", ".join([str(ITEMS[req.item_id].name.title()) for req in quest.requirements])
    if len(quest.requirements) > 0:
        reqs_str = f"({reqs_str}) "
    chance_str = ""
    if chance < 100:
        chance_str = f"{chance}%: "
    print(f"{indent_str}- {chance_str}{reqs_str}{quest.prompt}")
    for next_step in quest.next_steps:
        next_quest = QUESTS[next_step.quest_id]
        display_quest_chain(next_quest, next_step.chance, indent + INDENT_SIZE)
    
for quest, frequency in ROOT_QUESTS:
    display_quest_chain(quest)

for item in ITEMS:
    print(f"{item.item_id}: {item.name.title()}, {item.plural.title()}")
    
# Frequency test
test_frequency = 10 # minutes
tick_rate = 5 # seconds

frequency_seconds = test_frequency * 60
frequency_ticks = frequency_seconds / tick_rate
threshold = 1 / frequency_ticks
print(threshold)

samples = 10_000_000
hits = 0
int_threshold = int(threshold)
hits += int_threshold * samples
remainder = threshold - int_threshold
if remainder > 0:
    for i in range(samples):
        val = random.random()
        if val < remainder:
            hits += 1

actual_frequency = samples / hits * tick_rate / 60
print(actual_frequency)
