import pygame
import sys
import time
from game.config import SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, MAP_WIDTH, MAP_HEIGHT, TILE_SIZE
import game.config as config
import game.debug as debug
import game.minimap as minimap
from game.map_tools import (
    generate_map_with_predefined_rooms,
    draw_tilemap,
    move_to_next_room,
    generate_enemies_for_room,
    generate_boss_for_room,
    generate_items_for_room,
    
    
)
from game.entity import Entity, draw_attack_area
from game.collision import check_tile_collision, check_player_enemy_collision

stage = 1           
boss_active = False 
next_stage_active = False       
next_stage_timer = None         
game_over = False
items = []
room_items = {}
room_first_visit = {}
collected_items = set() #획득한 아이템
player_coins = 0
room_coins = {}  # {(x,y): [coin_entities...]}


def apply_item_effect(player, item_data):
    if item_data.get("max_hp") is not None:
        player.max_hp += item_data["max_hp"]
    if item_data.get("hp") is not None:
        player.hp = min(player.hp + item_data["hp"], player.max_hp)
        player.hp = min(player.hp, player.max_hp)
    if item_data.get("speed") is not None:
        player.speed += item_data["speed"]
    if item_data.get("attack_speed") is not None:
        player.attack_speed *= item_data["attack_speed"]
    if item_data.get("attack_range") is not None:
        player.attack_range += item_data["attack_range"]
    if item_data.get("damage") is not None:
        player.damage += item_data["damage"]
    if item_data.get("max_damage") is not None:
        player.max_damage += item_data["max_damage"]
    if item_data.get("min_damage") is not None:
        player.min_damage += item_data["min_damage"]
    if item_data.get("size") is not None:
        player.size += item_data["size"]
    if item_data.get("sqauare_min_max_damage") is not None:
        player.max_damage = player.max_damage*player.max_damage
        player.min_damage = player.min_damage*player.min_damage
        player.damage     = player.damage*player.damage
            
def check_collision(player, item):
    item_x = item.x + TILE_SIZE * 0.5 - item.size * 0.5
    item_y = item.y + TILE_SIZE * 0.5 - item.size * 0.5

    return (
        player.x < item_x + item.size and
        player.x + player.size > item_x and
        player.y < item_y + item.size and
        player.y + player.size > item_y
    )

def main():
    global boss_active, stage, MAP_WIDTH, MAP_HEIGHT
    # 초기화
    pygame.init()
    pygame.display.set_caption('로그라이크 맵')
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    # 맵 생성
    map_data, room_connections, (start_x, start_y), (boss_x, boss_y), special_coords = generate_map_with_predefined_rooms(MAP_WIDTH, MAP_HEIGHT)
    debug.print_map_data(map_data, MAP_WIDTH, MAP_HEIGHT)
    debug.print_room_connections(room_connections, MAP_WIDTH, MAP_HEIGHT)

    # 플레이어 및 적/보스 초기 설정
    player = Entity(TILE_SIZE*4.5, TILE_SIZE*4.5, '@', entity_type="player")
    current_x, current_y = start_x, start_y
    tilemap = map_data[(current_x, current_y)]
    enemies = generate_enemies_for_room(tilemap, current_x, current_y, start_x, start_y, config.itdiff())
    boss = []
    explored_rooms = {(x, y): False for x in range(MAP_WIDTH) for y in range(MAP_HEIGHT)}
    explored_rooms[(start_x, start_y)] = True

    # 메인 루프
    while True:
        global next_stage_active
        global game_over
        global items
        global room_items
        global room_first_visit
        global player_coins
        global room_coins
        screen.fill(BLACK)
        

        # 이벤트 처리
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            elif ev.type == pygame.KEYDOWN:
                # 좌/우: 공격 부호 전환
                if ev.key == pygame.K_LSHIFT:
                    player.attack_index = (player.attack_index + 1) % len(player.attack_types)
                    player.attack_type  = player.attack_types[player.attack_index]
                elif ev.key == pygame.K_RSHIFT:
                    player.attack_index = (player.attack_index - 1) % len(player.attack_types)
                    player.attack_type  = player.attack_types[player.attack_index]  
                # 상/하: 데미지 증감 (클램프)
                elif ev.key == pygame.K_e:
                    player.damage = min(player.max_damage, player.damage + 1)
                elif ev.key == pygame.K_q:
                    player.damage = max(player.min_damage, player.damage - 1)

        # 키 상태
        keys = pygame.key.get_pressed()

        # 방 이동 처리 (적이 모두 사라졌을 때만)
        if len(enemies) == 0 and len(boss) == 0:
            if keys[pygame.K_UP]:
                nx, ny, new_tilemap, new_enemies = move_to_next_room(
                    "up", player,
                    current_x, current_y,
                    map_data, room_connections,
                    explored_rooms,
                    start_x, start_y,
                    boss_x, boss_y
                )
                if (nx, ny) != (current_x, current_y):
                    current_x, current_y = nx, ny
                    tilemap  = new_tilemap
                    enemies  = new_enemies
                    if (current_x, current_y) not in room_first_visit:
                        room_first_visit[(current_x, current_y)] = True
                    if room_first_visit.get((current_x, current_y), False):
                        if any(7 in row for row in tilemap):
                            if not room_items.get((current_y, current_y)):
                                generated = generate_items_for_room(tilemap, exclude_symbols = collected_items)
                                if generated:
                                    room_items[(current_x, current_y)] = generated
                                    items = generated
                                    room_first_visit[(current_x, current_y)] = False
                                    print("아이템 생성!")
                        if not boss and any(5 in row for row in tilemap):
                            print("[1회 방문] 보스 생성 시작")
                            boss = generate_boss_for_room(tilemap, config.itdiff())
                            boss_active = True
                            enemies = []
                            room_first_visit[(current_x, current_y)] = False

            elif keys[pygame.K_DOWN]:
                nx, ny, new_tilemap, new_enemies = move_to_next_room(
                    "down", player,
                    current_x, current_y,
                    map_data, room_connections,
                    explored_rooms,
                    start_x, start_y,
                    boss_x, boss_y
                )
                if (nx, ny) != (current_x, current_y):
                    current_x, current_y = nx, ny
                    tilemap  = new_tilemap
                    enemies  = new_enemies
                    if (current_x, current_y) not in room_first_visit:
                        room_first_visit[(current_x, current_y)] = True
                    if room_first_visit.get((current_x, current_y), False):
                        if any(7 in row for row in tilemap):
                            if not room_items.get((current_y, current_y)):
                                generated = generate_items_for_room(tilemap, exclude_symbols = collected_items)
                                if generated:
                                    room_items[(current_x, current_y)] = generated
                                    items = generated
                                    room_first_visit[(current_x, current_y)] = False
                                    print("아이템 생성!")
                        if not boss and any(5 in row for row in tilemap):
                            print("[1회 방문] 보스 생성 시작")
                            boss = generate_boss_for_room(tilemap, config.itdiff())
                            boss_active = True
                            enemies = []
                            room_first_visit[(current_x, current_y)] = False
                    
            elif keys[pygame.K_LEFT]:
                nx, ny, new_tilemap, new_enemies = move_to_next_room(
                    "left", player,
                    current_x, current_y,
                    map_data, room_connections,
                    explored_rooms,
                    start_x, start_y,
                    boss_x, boss_y
                )
                if (nx, ny) != (current_x, current_y):
                    current_x, current_y = nx, ny
                    tilemap  = new_tilemap
                    enemies  = new_enemies
                    if (current_x, current_y) not in room_first_visit:
                        room_first_visit[(current_x, current_y)] = True
                    if room_first_visit.get((current_x, current_y), False):
                        if any(7 in row for row in tilemap):
                            if not room_items.get((current_y, current_y)):
                                generated = generate_items_for_room(tilemap, exclude_symbols = collected_items)
                                if generated:
                                    room_items[(current_x, current_y)] = generated
                                    items = generated
                                    room_first_visit[(current_x, current_y)] = False
                                    print("아이템 생성!")
                        if not boss and any(5 in row for row in tilemap):
                            print("[1회 방문] 보스 생성 시작")
                            boss = generate_boss_for_room(tilemap, config.itdiff())
                            boss_active = True
                            enemies = []
                            room_first_visit[(current_x, current_y)] = False

            elif keys[pygame.K_RIGHT]:
                nx, ny, new_tilemap, new_enemies = move_to_next_room(
                    "right", player,
                    current_x, current_y,
                    map_data, room_connections,
                    explored_rooms,
                    start_x, start_y,
                    boss_x, boss_y
                )
                if (nx, ny) != (current_x, current_y):
                    current_x, current_y = nx, ny
                    tilemap  = new_tilemap
                    enemies  = new_enemies
                    if (current_x, current_y) not in room_first_visit:
                        room_first_visit[(current_x, current_y)] = True
                    if room_first_visit.get((current_x, current_y), False):
                        if any(7 in row for row in tilemap):
                            if not room_items.get((current_y, current_y)):
                                generated = generate_items_for_room(tilemap, exclude_symbols = collected_items)
                                if generated:
                                    room_items[(current_x, current_y)] = generated
                                    items = generated
                                    room_first_visit[(current_x, current_y)] = False
                                    print("아이템 생성!")
                        if not boss and any(5 in row for row in tilemap):
                            print("[1회 방문] 보스 생성 시작")
                            boss = generate_boss_for_room(tilemap, config.itdiff())
                            boss_active = True
                            enemies = []
                            room_first_visit[(current_x, current_y)] = False

            elif keys[pygame.K_b]  :
                print("b 누름")
                current_x, current_y = boss_x, boss_y
                tilemap = map_data[(boss_x, boss_y)]
                explored_rooms[(boss_x, boss_y)] = True           
                draw_tilemap(tilemap)

                if (current_x, current_y) not in room_first_visit:
                    room_first_visit[(current_x, current_y)] = True
                    if room_first_visit.get((current_x, current_y), False):
                        if any(7 in row for row in tilemap):
                            if not room_items.get((current_y, current_y)):
                                generated = generate_items_for_room(tilemap)
                                if generated:
                                    room_items[(current_x, current_y)] = generated
                                    items = generated
                                    room_first_visit[(current_x, current_y)] = False
                                    print("아이템 생성!")
                        if not boss and any(5 in row for row in tilemap):
                            print("[1회 방문] 보스 생성 시작")
                            boss = generate_boss_for_room(tilemap, config.itdiff())
                            boss_active = True
                            enemies = []
                            room_first_visit[(current_x, current_y)] = False

            elif keys[pygame.K_i]  :
                print("i 누름")
                item_x, item_y = special_coords.get("item", (None, None))
                current_x, current_y = item_x, item_y
                tilemap = map_data[(item_x, item_y)]
                explored_rooms[(item_x, item_y)] = True           
                draw_tilemap(tilemap)
                if (current_x, current_y) not in room_first_visit:
                    room_first_visit[(current_x, current_y)] = True
                    if room_first_visit.get((current_x, current_y), False):
                        if any(7 in row for row in tilemap):
                            if not room_items.get((current_y, current_y)):
                                generated = generate_items_for_room(tilemap)
                                if generated:
                                    room_items[(current_x, current_y)] = generated
                                    items = generated
                                    room_first_visit[(current_x, current_y)] = False
                                    print("아이템 생성!")
                        if not boss and any(5 in row for row in tilemap):
                            print("[1회 방문] 보스 생성 시작")
                            boss = generate_boss_for_room(tilemap, config.itdiff())
                            boss_active = True
                            enemies = []
                            room_first_visit[(current_x, current_y)] = False

        new_x, new_y = player.x, player.y
        if keys[pygame.K_LEFT]:
            new_x -= player.speed
            player.last_direction = "left"
        if keys[pygame.K_RIGHT]:
            new_x += player.speed
            player.last_direction = "right"
        if keys[pygame.K_UP]:
            new_y -= player.speed
            player.last_direction = "up"
        if keys[pygame.K_DOWN]:
            new_y += player.speed
            player.last_direction = "down"

        # 충돌 검사 + 적 충돌 시스템 더해야 함 적,벽 / 
        if not check_tile_collision(new_x, player.y, player.size, tilemap) and            not check_player_enemy_collision(player, enemies + boss, tilemap):
            player.x = new_x
        if not check_tile_collision(player.x, new_y, player.size, tilemap) and            not check_player_enemy_collision(player, enemies + boss, tilemap):
            player.y = new_y
        
        # 공격 처리
        if keys[pygame.K_SPACE]:
            drops = player.attack_enemies(enemies, boss)
            if drops:
                room_coins.setdefault((current_x, current_y), []).extend(drops)
        
        # 적 행동
        for enemy in enemies:
            enemy.move_towards(player.x, player.y, tilemap, enemies=enemies)
            check_player_enemy_collision(player, [enemy], tilemap) 
            enemy.attack(player)
            enemy.draw()

        # 보스 행동
        for b in boss:
            b.move_towards(player.x, player.y, tilemap, enemies=enemies)
            check_player_enemy_collision(player, [b], tilemap)
            b.attack(player)
            b.draw()
        
         # ─── 보스 처치 완료 판정 ───
        if boss_active and len(boss) == 0 and not next_stage_active:
            print("보스 리스트 길이:", len(boss))
            print("boss_active:", boss_active, "next_stage_active:", next_stage_active)
            boss_active = False
            next_stage_active = True
            # 보스방 중앙에 다음 스테이지 타일 설치
            center = len(tilemap) // 2
            map_data[boss_x, boss_y][center][center] = 6  # config.next_stage 값(6)
            next_stage_timer = None
            # 탐험 상태 업데이트
            explored_rooms[(current_x, current_y)] = True

            screen.fill(BLACK)
        
        if next_stage_active == True:
            # 플레이어 중심 좌표로 타일 위치 계산
            px = int((player.x + player.size/2) // TILE_SIZE)
            py = int((player.y + player.size/2) // TILE_SIZE)
            if 0 <= px < len(tilemap[0]) and 0 <= py < len(tilemap):
                if tilemap[py][px] == config.next_stage:
                    if next_stage_timer is None:
                        next_stage_timer = time.time()
                    elif time.time() - next_stage_timer >= 2:
                        # 2초 이상 머물렀으면 스테이지 전환
                        stage += 1
                        config.diffs(1)
                        # 맵 크기 증가
                        MAP_HEIGHT = MAP_HEIGHT + 2
                        MAP_WIDTH = MAP_WIDTH + 2
                        # 새로운 맵 생성
                        map_data, room_connections, (start_x, start_y), (boss_x, boss_y), special_coords = \
                            generate_map_with_predefined_rooms(MAP_WIDTH, MAP_HEIGHT)
                        debug.print_map_data(map_data, MAP_WIDTH, MAP_HEIGHT)
                        debug.print_room_connections(room_connections, MAP_WIDTH, MAP_HEIGHT)
                        # 플레이어/적/보스 초기화 (원래 보스 kill 이후 로직)
                        current_x, current_y = start_x, start_y
                        tilemap = map_data[(current_x, current_y)]
                        player.x, player.y = TILE_SIZE*4, TILE_SIZE*4
                        enemies = generate_enemies_for_room(tilemap, current_x, current_y, start_x, start_y, config.itdiff())
                        boss = []
                        enemies = []
                        items = []
                        room_items = {}
                        room_first_visit = {}
                        player_coins = 0
                        room_coins.clear()
                        explored_rooms = { (x, y): False for x in range(MAP_WIDTH) for y in range(MAP_HEIGHT) }
                        explored_rooms[(current_x, current_y)] = True
                        next_stage_active = False
                        next_stage_timer = None

                else:
                    # 타일에서 벗어나면 타이머 리셋
                    next_stage_timer = None
        if (current_x, current_y) == (start_x, start_y) and tilemap[4][4] != 0:
            tilemap[4][4] = 0
            print("시작방!")

        if player.hp <= 0:
            game_over = True

        # 맵(타일)을 먼저 그린다
        draw_tilemap(tilemap)

        # 적·보스 그리기 (적이 맵 위에 올려지도록)
        for enemy in enemies:
            enemy.draw()
        for b in boss:
            b.draw()

        # 플레이어를 그린다 (플레이어가 적보다 위에 보이길 원하면 이 위치를 바꿔도 됩니다)
        player.draw()
        
        if keys[pygame.K_SPACE]:
            draw_attack_area(player)
            

        current_items = room_items.get((current_x, current_y), [])
        for item in current_items[:]:  # 복사본 반복
            if  (player, item):
                from game.itemset import item_types
                item_data = item_types.get(item.symbol, {})
                apply_item_effect(player, item_data)
                current_items.remove(item)
                break  # 1개만 처리   
        
        for item in room_items.get((current_x, current_y), []):
            item.draw()

        if game_over:
            screen.fill(BLACK)
            # 게임 오버 텍스트 출력
            font = pygame.font.SysFont(None, 48)
            msg = font.render("GAME OVER - Press R to Restart", True, (255, 255, 255))
            screen.blit(msg, (SCREEN_WIDTH//2 - msg.get_width()//2, SCREEN_HEIGHT//2))
            player.hp = 0
            enemies = []
            boss = []
            # R 키 입력 시 초기화
            if keys[pygame.K_r]:
                stage = 1
                config.reset_diff()
                MAP_WIDTH = 9
                MAP_HEIGHT = 9
                map_data, room_connections, (start_x, start_y), (boss_x, boss_y), special_coords = generate_map_with_predefined_rooms(MAP_WIDTH, MAP_HEIGHT)
                current_x, current_y = start_x, start_y
                tilemap = map_data[(current_x, current_y)]
                player = Entity(TILE_SIZE*4.5, TILE_SIZE*4.5, '@', entity_type="player")
                enemies = generate_enemies_for_room(tilemap, current_x, current_y, start_x, start_y, config.itdiff())
                boss = []
                items = []
                room_items = {}
                room_first_visit = {}
                collected_items.clear()
                explored_rooms = {(x, y): False for x in range(MAP_WIDTH) for y in range(MAP_HEIGHT)}
                explored_rooms[(start_x, start_y)] = True
                game_over = False
                next_stage_active = False
                next_stage_timer = None
                
        current_coin_list = room_coins.get((current_x, current_y), [])
        
        #코인 획득 로직
        for c in current_coin_list[:]:
            if (player.x < c.x + c.size and
                player.x + player.size > c.x and
                player.y < c.y + c.size and
                player.y + player.size > c.y):
                player_coins += getattr(c, "coin_value", 1)
                current_coin_list.remove(c)
        for c in current_coin_list:
            c.draw()
            
        # 미니맵 등 UI 요소를 마지막에 그린다
        minimap.draw_minimap(explored_rooms, current_x, current_y,
                             MAP_WIDTH, MAP_HEIGHT, len(enemies), room_connections, boss_x, boss_y)
        
                # ─── 플레이어 체력 UI 출력 ───
        font = pygame.font.SysFont(None, 24)
        hp_text = font.render(f"HP: {player.hp} / {player.max_hp}", True, (255, 255, 255))
        # 체력바 위치 및 크기
        bar_x = SCREEN_WIDTH - 240
        bar_y = 50
        bar_width = 200
        bar_height = 20
        hp_ratio = max(0, player.hp / player.max_hp)
        
        pygame.draw.rect(screen, BLACK, (bar_x - 10, bar_y - 30, bar_width + 20, bar_height + 40))

        # 체력바 배경 + 전경
        pygame.draw.rect(screen, (80, 80, 80), (bar_x, bar_y, bar_width, bar_height))       # 배경
        pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, bar_width * hp_ratio, bar_height))  # 빨간 체력바
        
        # 공격 유형 + 수치
        font = pygame.font.SysFont(None, 24)
        atk_text = font.render(f"ATK: {player.attack_type} {player.damage} / max : {player.max_damage} min : {player.min_damage}", True, (255,255,255))
        screen.blit(atk_text, (bar_x + 5, bar_y + 5 + bar_height))
        
        # HUD에 코인 표시(HP 아래 등)
        font = pygame.font.SysFont(None, 24)
        coin_text = font.render(f"COIN: {player_coins}", True, (255,255,255))
        screen.blit(coin_text, (SCREEN_WIDTH - 220, 100))

        # 수치 텍스트
        screen.blit(hp_text, (bar_x + 60, bar_y - 25))


        # 화면 업데이트
        pygame.display.flip()
        # ───────────────────────────────────
        
        clock.tick(60)

if __name__ == '__main__':
    main()