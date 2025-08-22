from game.config import TILE_SIZE, walkable_tiles, door
import time

def check_tile_collision(x, y, size, tilemap):
    """타일맵 경계 및 벽(walkable_tiles 외)에 부딪히는지 확인합니다."""
    corners = [(x, y), (x+size-1, y), (x, y+size-1), (x+size-1, y+size-1)]
    for cx, cy in corners:
        tx = int(cx // TILE_SIZE)
        ty = int(cy // TILE_SIZE)
        if tx < 0 or ty < 0 or ty >= len(tilemap) or tx >= len(tilemap[0]):
            return True
        if tilemap[ty][tx] not in walkable_tiles:
            return True
    return False

def check_corner_collision(entity1, entity2):
    """두 엔티티의 네 모서리 점 간 충돌 검사."""
    corners = [
        (entity1.x, entity1.y),
        (entity1.x+entity1.size-1, entity1.y),
        (entity1.x, entity1.y+entity1.size-1),
        (entity1.x+entity1.size-1, entity1.y+entity1.size-1)
    ]
    for cx, cy in corners:
        if entity2.get_rect().collidepoint(cx, cy):
            return True
    return False

def check_player_enemy_collision(player, enemies, tilemap):
    collided = False
    now = time.time()
    for enemy in enemies:
        if check_corner_collision(player, enemy):
            # 먼저 접촉시각만 기록 → 공격 판정에서 그레이스 적용됨
            try:
                enemy.last_touch_time = now
            except Exception:
                pass

            # 이후에 밀어내기
            ox = (enemy.get_rect().centerx - player.get_rect().centerx) / 2
            oy = (enemy.get_rect().centery - player.get_rect().centery) / 2
            if not check_tile_collision(enemy.x + ox, enemy.y, enemy.size, tilemap):
                enemy.x += ox * 0.15
            if not check_tile_collision(enemy.x, enemy.y + oy, enemy.size, tilemap):
                enemy.y += oy * 0.15
            collided = True
    return collided

def check_player_at_door(player, direction, tilemap, room_conns):
    """
    간단한 좌표 비교로 문 타일에 닿았는지 확인합니다.
    - 'player.x / player.y' 값만 보고, 미리 정해진 픽셀 기준으로 문 위치 판정
    - room_conns[direction]이 True인지도 함께 확인
    - tilemap[...] == door 으로 해당 타일이 실제 문인지 최종 판단
    """
    # 위쪽 문: y <= TILE_SIZE - 10, 타일 인덱스 (0,4)
    if direction == "up":
        if (player.y <= TILE_SIZE - 10             # 플레이어가 방 상단에 거의 닿았는지
                and room_conns.get("up")           # 위쪽에 연결이 열려 있는지
                and tilemap[0][4] == door):        # (0,4) 타일이 실제 문인지
            return True

    # 아래쪽 문: y >= TILE_SIZE*8 (8*75=600)
    if direction == "down":
        if (player.y >= TILE_SIZE * 8
                and room_conns.get("down")
                and tilemap[8][4] == door):
            return True

    # 왼쪽 문: x <= TILE_SIZE - 10
    if direction == "left":
        if (player.x <= TILE_SIZE - 10
                and room_conns.get("left")
                and tilemap[4][0] == door):
            return True

    # 오른쪽 문: x >= TILE_SIZE*8
    if direction == "right":
        if (player.x >= TILE_SIZE * 8
                and room_conns.get("right")
                and tilemap[4][8] == door):
            return True

    return False

def check_player_enemy_contact(player, enemy, inflate_px: int = 0) -> bool:
    """플레이어-적 히트박스 접촉 여부(필요 시 미세틈 보정)."""
    pr = player.get_rect()
    er = enemy.get_rect()
    if inflate_px:
        pr = pr.inflate(inflate_px, inflate_px)
        er = er.inflate(inflate_px, inflate_px)
    return pr.colliderect(er)