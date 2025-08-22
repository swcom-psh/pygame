import pygame

# 화면 크기
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 720

# 색상
WHITE  = (255, 255, 255)
BLACK  = (  0,   0,   0)
BLUE   = (  0,   0, 255)
RED    = (255,   0,   0)
GREEN  = (  0, 255,   0)
YELLOW = (255, 255,   0)
VIOLET = (238, 130, 238)

#충졸 판정 관련
CONTACT_MARGIN_PX = 16       # 중심거리 마진(px)
CONTACT_GRACE_SEC = 0.05     # 밀려난 뒤에도 접촉으로 간주하는 시간(s)

# 타일 크기
TILE_SIZE = 75

# 불·가능 타일 정의
item = 7
next_stage = 6
door               = 3
walkable_tiles     = {0,3,4,5,6,7}
non_walkable_tiles = {1,2}


# 화면(surface)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# 난이도(diff) 관리
diff = 1
def diffs(x):
    global diff
    diff += x
def reset_diff():
    global diff
    diff = 1
def itdiff():
    return int(diff)

MAP_WIDTH = 9
MAP_HEIGHT = 9

# 점수 처리
scores = 0
def score(x):
    global scores
    scores += x
def reset_score():
    global scores
    scores = 0
def getscore():
    return scores

# (원본에 있던) 적·보스 속성 함수
def enemy_types(diff):
    return {
        "a": {"hp":2+(diff-1)*3, "speed":(TILE_SIZE/50)+diff*(TILE_SIZE/50)*0.1, "color":RED, "attack_speed":1+diff*0.05, "damage":2+(diff-1)*3, "size":TILE_SIZE*0.5, "attack_type" : "-"},
        "b": {"hp":3+(diff-1)*3, "speed":(TILE_SIZE/50)+diff*(TILE_SIZE/50)*0.1, "color":GREEN, "attack_speed":1.5+diff*0.05, "damage":3+(diff-1)*3, "size":TILE_SIZE*0.6, "attack_type" : "-"},
        "c": {"hp":4+(diff-1)*3,"speed":(TILE_SIZE/50)*0.8+diff*(TILE_SIZE/50)*0.08,"color":BLUE,"attack_speed":2+diff*0.05,"damage":4+(diff-1)*3,"size":TILE_SIZE*0.75, "attack_type" : "-"},
        "a'": {"hp":2+(diff-1)*3, "speed":(TILE_SIZE/50)+diff*(TILE_SIZE/50)*0.1, "color":RED, "attack_speed":1+diff*0.05, "damage":2+(diff-1)*3, "size":TILE_SIZE*0.5, "attack_type" : "+"},
        "b'": {"hp":3+(diff-1)*3, "speed":(TILE_SIZE/50)+diff*(TILE_SIZE/50)*0.1, "color":GREEN, "attack_speed":1.5+diff*0.05, "damage":3+(diff-1)*3, "size":TILE_SIZE*0.6, "attack_type" : "+"},
        "c'": {"hp":4+(diff-1)*3,"speed":(TILE_SIZE/50)*0.8+diff*(TILE_SIZE/50)*0.08,"color":BLUE,"attack_speed":2+diff*0.05,"damage":4+(diff-1)*3,"size":TILE_SIZE*0.75, "attack_type" : "+"},
    }

def boss_types(diff):
    return {
        "B_a": {"hp":15+(diff-1)*5,"speed":(TILE_SIZE/50)+diff*(TILE_SIZE/50)*0.12,"color":VIOLET,"attack_speed":1+diff*0.05,"damage":15+(diff-1)*5,"size":TILE_SIZE*0.7, "attack_type" : "-"},
        "B_b": {"hp":20+(diff-1)*5,"speed":(TILE_SIZE/50)+diff*(TILE_SIZE/50)*0.1,"color":VIOLET,"attack_speed":1.5+diff*0.05,"damage":20+(diff-1)*5,"size":TILE_SIZE*0.8, "attack_type" : "-"},
        "B_c": {"hp":25+(diff-1)*5 ,"speed":(TILE_SIZE/50)+diff*(TILE_SIZE/50)*0.08,"color":VIOLET,"attack_speed":2+diff*0.05,"damage":25+(diff-1)*5,"size":TILE_SIZE*0.95, "attack_type" : "-"},
        "B_a": {"hp":15+(diff-1)*5,"speed":(TILE_SIZE/50)+diff*(TILE_SIZE/50)*0.12,"color":VIOLET,"attack_speed":1+diff*0.05,"damage":15+(diff-1)*5,"size":TILE_SIZE*0.7, "attack_type" : "+"},
        "B_b": {"hp":20+(diff-1)*5,"speed":(TILE_SIZE/50)+diff*(TILE_SIZE/50)*0.1,"color":VIOLET,"attack_speed":1.5+diff*0.05,"damage":20+(diff-1)*5,"size":TILE_SIZE*0.8, "attack_type" : "+"},
        "B_c": {"hp":25+(diff-1)*5 ,"speed":(TILE_SIZE/50)+diff*(TILE_SIZE/50)*0.08,"color":VIOLET,"attack_speed":2+diff*0.05,"damage":25+(diff-1)*5,"size":TILE_SIZE*0.95, "attack_type" : "+"},
    }
