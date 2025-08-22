import pygame
from game.config import *
import game.config as config
from game.map_tools import special_coords

def draw_minimap(explored_rooms, current_x, current_y, width, height, texts, room_connections, boss_X, boss_y):
    global diff
    minimap_size = (TILE_SIZE/50)*125
    minimap_x = SCREEN_WIDTH - minimap_size - 10
    minimap_y = SCREEN_HEIGHT - minimap_size - 10
    font = pygame.font.SysFont(None, 24)
    
    screen = pygame.display.get_surface()
    pygame.draw.rect(screen, BLACK, (minimap_x, minimap_y - 85, 200, 90))
    
    text = f"enemies : {texts}"
    text2 = f"x : {current_x}, y : {current_y}"
    text3 = f"stage : {config.itdiff()}"
    ts   = font.render(text,  True, WHITE)
    ts2  = font.render(text2, True, WHITE)
    ts3 = font.render(text3, True, WHITE)

    screen.blit(ts3,  (minimap_x, minimap_y - 80))
    screen.blit(ts,  (minimap_x, minimap_y - 60))
    screen.blit(ts2, (minimap_x, minimap_y - 40))
    
    room_w = minimap_size / width
    room_h = minimap_size / height

    # 배경
    pygame.draw.rect(screen, BLACK, (minimap_x, minimap_y, minimap_size, minimap_size))

    # 탐험된 방
    for (x,y), seen in explored_rooms.items():
        if seen:
            if (x,y) == (boss_X, boss_y):
                color = VIOLET
            elif (x,y) == (special_coords["item"]):
                color = YELLOW
            elif (x,y) == (special_coords["sp2"]):
                color = BLUE
            else:
                color = WHITE
            pygame.draw.rect(screen, color,
                             (minimap_x + x*room_w,
                              minimap_y + y*room_h,
                              room_w, room_h))
    
    # 연결된 미탐험 방 (회색)
    for x in range(width):
        for y in range(height):
            if explored_rooms.get((x, y), False):
                continue
            # 연결된 탐험된 방이 있는지 확인
            neighbors = [ (x, y-1), (x, y+1), (x-1, y), (x+1, y) ]
            for nx, ny in neighbors:
                if 0 <= nx < width and 0 <= ny < height:
                    if explored_rooms.get((nx, ny), False) and room_connections.get((nx, ny)):
                        if room_connections[(nx, ny)].get("up")   and ny > y: break
                        if room_connections[(nx, ny)].get("down") and ny < y: break
                        if room_connections[(nx, ny)].get("left") and nx > x: break
                        if room_connections[(nx, ny)].get("right") and nx < x: break
            else:
                continue  # break 안 됐으면 연결 없음
            # 연결 있으면 회색 표시
            pygame.draw.rect(screen, (100, 100, 100),
                            (minimap_x + x*room_w,
                            minimap_y + y*room_h,
                            room_w, room_h))

    # 현재 방 강조
    pygame.draw.rect(screen, RED,
                     (minimap_x + current_x*room_w,
                      minimap_y + current_y*room_h,
                      room_w, room_h), 2)
