# game/map_tools.py

import random
import pygame
import copy
from game.config import TILE_SIZE, door, BLUE, BLACK, VIOLET, WHITE
import game.config as config
from game.mapset import predefined_rooms, start_rooms, boss_room, Item_room, sp2_room
from game.entity import Entity
from game.itemset import item_types


special_coords = {}

_TILE_FONT = None
def _get_tile_font():
    global _TILE_FONT
    if _TILE_FONT is None:
        # 타일 크기의 ~60%로 글자 크기
        _TILE_FONT = pygame.font.SysFont(None, int(TILE_SIZE * 0.6))
    return _TILE_FONT

def _blit_center_text(surface, text, x, y, color):
    font = _get_tile_font()
    ts = font.render(text, True, color)
    tr = ts.get_rect(center=(x + TILE_SIZE // 2, y + TILE_SIZE // 2))
    surface.blit(ts, tr)

def add_doors_to_room(room, connections):
    """
    방 중앙 벽에 문(door)을 추가한 뒤, 실제 연결 여부에 따라
    연결이 없는 쪽은 벽(1)으로 되돌립니다.
    """
    room[0][4] = door
    room[8][4] = door
    room[4][0] = door
    room[4][8] = door
    if not connections.get("up"):
        room[0][4] = 1
    if not connections.get("down"):
        room[8][4] = 1
    if not connections.get("left"):
        room[4][0] = 1
    if not connections.get("right"):
        room[4][8] = 1
    return room

def generate_grid_map(n, start, boss, branch_chance=(0.2 + 0.025*(config.itdiff() - 1))):
    """
    n x n 그리드에 start, boss를 1로 설정 후,
    1) 메인 경로 생성(carve_main_path)
    2) 메인 경로 및 분기 노드 기반으로 브런치 확장
       * 분기 경로는 다른 경로와 접촉하지 않도록
    반환: grid, main_path
    """
    sx, sy = start
    bx, by = boss
    grid = [[0] * n for _ in range(n)]

    # 시작방 초기 마킹 (보스방은 메인 경로 생성 후 마킹)
    grid[sy][sx] = 1

    # 1) 메인 경로 생성
    def carve_main_path():
        cx, cy = sx, sy
        path = [(cx, cy)]
        while (cx, cy) != (bx, by):
            dx, dy = bx - cx, by - cy
            moves = []
            if dx != 0:
                moves.append((cx + (1 if dx > 0 else -1), cy))
            if dy != 0:
                moves.append((cx, cy + (1 if dy > 0 else -1)))
            next_x, next_y = random.choice(moves)
            if 0 <= next_x < n and 0 <= next_y < n and grid[next_y][next_x] == 0:
                cx, cy = next_x, next_y
                grid[cy][cx] = 1
                path.append((cx, cy))
        return path

    main_path = carve_main_path()
    # 분기 노드 리스트 초기화
    sources = [pos for pos in main_path if pos != (bx, by)]


    # 2) 분기 경로 확장
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    i = 0
    while i < len(sources):
        px, py = sources[i]
        i += 1
        if random.random() < branch_chance:
            length = random.randint(config.itdiff(), config.itdiff() + 2)
            cx, cy = px, py
            for _ in range(length):
                random.shuffle(dirs)
                for dx, dy in dirs:
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < n and 0 <= ny < n and grid[ny][nx] == 0:
                        # 인접 4방향 다른 경로 충돌 검사
                        ok = True
                        for ddx, ddy in dirs:
                            ax, ay = nx + ddx, ny + ddy
                            if (ax, ay) != (cx, cy) and 0 <= ax < n and 0 <= ay < n and grid[ay][ax] == 1:
                                ok = False
                                break
                        if not ok:
                            continue
                        grid[ny][nx] = 1
                        sources.append((nx, ny))
                        cx, cy = nx, ny
                        break
    return grid, main_path


def generate_map_with_predefined_rooms(width, height):
    global special_coords
    """
    Isaac 스타일 그리드 생성 + 메인 경로 분기에서 특수방 노드 생성
    """
    # 시작/보스 좌표
    sx, sy = width // 2, height // 2
    borders = [
        (x, y)
        for x in range(width)
        for y in range(height)
        if (x == 0 or x == width - 1 or y == 0 or y == height - 1)
        and (x, y) != (sx, sy)
    ]
    bx, by = random.choice(borders)

    # 그리드 및 메인 경로
    grid, main_path = generate_grid_map(width, (sx, sy), (bx, by))

    # 3) 메인 경로 브런치에서 특수방 좌표 생성
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    # 시작/보스 제외한 전체 grid=1 영역 중 후보 선택
    candidates = [(x, y)
                  for y in range(height)
                  for x in range(width)
                  if grid[y][x] == 1 and (x, y) not in [(sx, sy), (bx, by)]]

    random.shuffle(candidates)
    
    # 아이템방과 sp2방 순서대로 생성
    for name, layout_dict in [('item', Item_room), ('sp2', sp2_room)]:
        placed = False
        attempt = 0
        while not placed and attempt < 100:
            attempt += 1
            random.shuffle(candidates)
            for px, py in candidates:
                random.shuffle(dirs)
                for dx, dy in dirs:
                    nx, ny = px + dx, py + dy
                    if 0 <= nx < width and 0 <= ny < height and grid[ny][nx] == 0:
                        # 인접 충돌 방지
                        ok = True
                        for ddx, ddy in dirs:
                            ax, ay = nx + ddx, ny + ddy
                            if (ax, ay) != (px, py) and 0 <= ax < width and 0 <= ay < height and grid[ay][ax] == 1:
                                ok = False
                                break
                        if not ok:
                            continue
                        grid[ny][nx] = 1
                        special_coords[name] = (nx, ny)
                        placed = True
                        print(f"[아이템방 좌표]: {special_coords.get('item')}")
                        break
                if placed:
                    break
        if not placed:
            print(f"[경고] 특수방 '{name}' 생성 실패")

    # 4) 방 연결 정보 생성
    room_connections = {}
    for y in range(height):
        for x in range(width):
            if grid[y][x] == 1:
                conns = {"up": False, "down": False, "left": False, "right": False}
                if y > 0 and grid[y - 1][x] == 1: conns["up"] = True
                if y < height - 1 and grid[y + 1][x] == 1: conns["down"] = True
                if x > 0 and grid[y][x - 1] == 1: conns["left"] = True
                if x < width - 1 and grid[y][x + 1] == 1: conns["right"] = True
                room_connections[(x, y)] = conns

    # 5) 레이아웃 배치
    map_data = {}
    for (x, y), conns in room_connections.items():
        if (x, y) == (sx, sy):
            base = random.choice(list(start_rooms.values()))
        elif (x, y) == (bx, by):
            base = random.choice(list(boss_room.values()))
        elif (x, y) == special_coords.get('item'):
            base = random.choice(list(Item_room.values()))
        elif (x, y) == special_coords.get('sp2'):
            base = random.choice(list(sp2_room.values()))
        else:
            base = random.choice(list(predefined_rooms.values()))
        room = copy.deepcopy(base)
        room = add_doors_to_room(room, conns)
        map_data[(x, y)] = room

    return map_data, room_connections, (sx, sy), (bx, by), special_coords


def check_player_at_door(player, direction, tilemap, room_conns):
    """
    플레이어가 방 경계의 문 위치에 있는지 확인합니다.
    """
    if direction == "up" and player.y <= 0 and room_conns.get("up") and tilemap[0][4] == door:
        return True
    if direction == "down" and player.y >= TILE_SIZE*8 and room_conns.get("down") and tilemap[8][4] == door:
        return True
    if direction == "left" and player.x <= 0 and room_conns.get("left") and tilemap[4][0] == door:
        return True
    if direction == "right" and player.x >= TILE_SIZE*8 and room_conns.get("right") and tilemap[4][8] == door:
        return True
    return False

from game.collision import check_player_at_door

def generate_enemies_for_room(tilemap, room_x, room_y, start_x, start_y, diff):
    """
    1) 시작 방이면 빈 리스트 반환
    2) tilemap을 순회하면서 tile == 4인 칸만 '가능 위치'에 추가
    3) rate 확률로 스폰
    """
    # 시작 방이면 적 생성 안 함
    if (room_x, room_y) == (start_x, start_y):
        print(f"[generate_enemies] 시작 방 ({room_x},{room_y}) -> 생성 안 함")
        return []

    enemies = []
    possible_positions = []

    # 1) 빈 칸(tile==4) 세기
    for r in range(len(tilemap)):
        for c in range(len(tilemap[r])):
            if tilemap[r][c] == 4:
                possible_positions.append((c, r))

    print(f"[generate_enemies] 방 ({room_x},{room_y})에서 '4' 타일 개수:", len(possible_positions))

    # 2) 확률 계산
    rate = 0.1 + 0.05 * (diff - 1)
    print(f"[generate_enemies] 난이도 diff={diff}, 확률 rate={rate:.3f}")

    # 3) 실제 스폰 시도
    for (c, r) in possible_positions:
        if random.random() < rate:
            et = random.choice(list(config.enemy_types(diff).keys()))
            e = Entity(c * TILE_SIZE, r * TILE_SIZE, et, entity_type=et)
            enemies.append(e)
            print(f"  → 스폰: 타입 {et} 위치 ({c},{r})")

    print(f"[generate_enemies] 최종 생성된 적 개수:", len(enemies))
    return enemies

def generate_boss_for_room(tilemap, diff):
    """
    현재 보스룸의 타일맵을 기반으로 보스를 생성합니다.
    Returns:
        list with one boss Entity
    """
    bosses = [] 
    for row in range(len(tilemap)):
        for col in range(len(tilemap[row])):
            if tilemap[row][col] == 5:
                bt = random.choice(list(config.boss_types(diff).keys()))
                b = Entity(col*TILE_SIZE, row*TILE_SIZE, bt, entity_type=bt)
                bosses.append(b)
                return bosses
    return bosses

# ===== [교체] 타일 렌더 함수 =====
def draw_tilemap(tilemap):
    """
    타일맵(9x9)을 화면에 그립니다.
    - 통과(0): 중앙에 '0' (옅은 회색)
    - 불통과(1,2): 흰 배경 + 검은 외곽선 + 중앙에 'X','Y'
    - 문(door): 중앙에 '='
    - (옵션) 아이템/다음스테이지 표시 유지
    """
    screen = pygame.display.get_surface()
    for r, row in enumerate(tilemap):
        for c, tile in enumerate(row):
            x, y = c * TILE_SIZE, r * TILE_SIZE
            rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)

            # 공통: 흰 배경으로 깔기
            pygame.draw.rect(screen, WHITE, rect)

            if tile == 0 or tile == 4 or tile == 5 or tile == 7:
                # 이동 가능: 중앙에 '0'(옅게)
                _blit_center_text(screen, "0", x, y, (170, 170, 170))

            elif tile == 1:
                # 벽1: 외곽선 + 'e^X'
                pygame.draw.rect(screen, BLUE, rect, 2)
                _blit_center_text(screen, "e^x", x, y, BLUE)

            elif tile == 2:
                # 벽2: 외곽선 + 'x'
                pygame.draw.rect(screen, BLACK, rect, 2)
                _blit_center_text(screen, "x", x, y, BLACK)

            elif tile == door:
                # 문: '='
                _blit_center_text(screen, "=", x, y, VIOLET)

            # ---- 선택: 기존 특수타일 가독성 유지 ----
            elif getattr(config, "next_stage", None) is not None and tile == config.next_stage:
                _blit_center_text(screen, "=>", x, y, (0, 150, 0))
            else:
                # 기타 미정 의 타일은 빈 흰칸(필요시 추가 매핑)
                pass

def generate_items_for_room(tilemap, exclude_symbols=None):
    items = []
    possible = []

    # 먹은 아이템 집합화(옵션)
    if exclude_symbols is None:
        exclude = set()
    else:
        exclude = set(exclude_symbols)

    # 아이템 스폰 가능한 타일(= config.item) 수집
    for r in range(len(tilemap)):
        for c in range(len(tilemap[r])):
            if tilemap[r][c] == config.item:
                possible.append((c, r))

    if not possible:
        return items  # 후보 타일이 없으면 생성 안 함

    # 생성 가능한 아이템 심볼 풀(먹은 아이템 제외)
    candidates = [k for k in item_types.keys() if k not in exclude]
    if not candidates:
        print("[아이템 생성] 제외로 인해 생성 가능한 아이템 없음")
        return items

    # 타일/아이템 선택 및 엔티티 생성
    cx, cy = random.choice(possible)
    it_key = random.choice(candidates)

    ent = Entity(cx * TILE_SIZE, cy * TILE_SIZE, it_key, entity_type="item")
    # itemset의 texture 값을 엔티티에 주입 (경로 문자열)
    #ent.texture = item_types[it_key].get("texture") # <- 임시로 삭제?

    items.append(ent)

    # 로그
    print('item 생성!')
    print(f"[아이템 생성 후보 수]: {len(possible)}")
    print(f"[선택된 타일 좌표]: {cx}, {cy}")
    print(f"[선택된 아이템 키]: {it_key}")

    return items

def move_to_next_room(direction, player,
                      current_x, current_y,
                      map_data, room_connections,
                      explored_rooms, start_x, start_y,
                      boss_x, boss_y):
    """
    direction: "up", "down", "left", "right"
    player: Entity
    current_x, current_y: 현재 방 좌표
    map_data: {(x,y) -> 9x9 타일맵}
    room_connections: {(x,y) -> {"up":bool, …}}
    explored_rooms: {(x,y) -> bool}
    start_x, start_y: 시작 방 좌표
    boss_x, boss_y: 보스 방 좌표

    반환값: (new_x, new_y, new_tilemap, new_enemies)
    """
    tilemap      = map_data[(current_x, current_y)]
    conns        = room_connections[(current_x, current_y)]

    # 1) 문 통과 여부 체크
    if not check_player_at_door(player, direction, tilemap, conns):
        return current_x, current_y, tilemap, []

    # 2) 연결 정보가 False면 이동 불가
    if not conns.get(direction):
        return current_x, current_y, tilemap, []

    # 3) 실제 좌표(방 번호) 변경 및 플레이어 재배치
    if direction == "up":
        new_x, new_y = current_x, current_y - 1
        player.x, player.y = TILE_SIZE * 4, TILE_SIZE * 8
    elif direction == "down":
        new_x, new_y = current_x, current_y + 1
        player.x, player.y = TILE_SIZE * 4, TILE_SIZE
    elif direction == "left":
        new_x, new_y = current_x - 1, current_y
        player.x, player.y = TILE_SIZE * 8, TILE_SIZE * 4
    else:  # "right"
        new_x, new_y = current_x + 1, current_y
        player.x, player.y = TILE_SIZE, TILE_SIZE * 4

    # 4) 새로운 방 불러오기
    new_tilemap = map_data[(new_x, new_y)]
    new_conns   = room_connections[(new_x, new_y)]
    new_tilemap = add_doors_to_room(new_tilemap, new_conns)

    # 5) 적/보스 생성 여부 판단
    if not explored_rooms.get((new_x, new_y), False):
        if (new_x, new_y) == (boss_x, boss_y):
            new_enemies = generate_boss_for_room(new_tilemap, config.itdiff())
        else:
            new_enemies = generate_enemies_for_room(
                tilemap=new_tilemap,
                room_x=new_x, room_y=new_y,
                start_x=start_x, start_y=start_y, diff=config.itdiff()
            )
    else:
        new_enemies = []  # 이미 방문한 방이면 적 제거

    # 6) 탐험 플래그 갱신
    explored_rooms[(new_x, new_y)] = True

    return new_x, new_y, new_tilemap, new_enemies

