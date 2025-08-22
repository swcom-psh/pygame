# game/loot.py
import random
from game.config import TILE_SIZE
import game.config as config
from game.itemset import coin_types

def generate_coin_drop(x_px: float, y_px: float, size_px: float) -> list[dict]:
    diff = config.itdiff()
    drop_rate = 1 #0.30 + 0.05 * max(0, diff - 1) # <- 디버그용 100퍼 ㅇㅇ
    if random.random() > drop_rate:
        return []

    cnt = random.randint(1, 1 + diff // 2)
    # 필요시 가중치/복수 키로 확장. 지금은 "+1" 단일 키.
    coin_key = "+1"

    px = x_px + size_px * 0.5
    py = y_px + size_px * 0.5

    return [{"key": coin_key, "pos": (px, py)} for _ in range(cnt)]
