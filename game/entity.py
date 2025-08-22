# game/entity.py

import pygame
import os
import math
import time
from game.config import*
from game.collision import check_corner_collision, check_tile_collision
import game.config as config
from game.loot import generate_coin_drop
from game.itemset import coin_types, item_types

ITEM_TEXTURES = {}

def _get_item_texture(path: str, scale_px: int | None = None) -> pygame.Surface | None:
    """경로 기반 텍스처 로드/스케일/캐시. 실패 시 None."""
    if not path:
        return None
    if scale_px is None:
        scale_px = int(TILE_SIZE * 0.6)

    # 상대경로 지원: 프로젝트 루트(…/game/..) 기준으로 정규화
    if os.path.isabs(path):
        abs_path = path
    else:
        root = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
        abs_path = os.path.normpath(os.path.join(root, path))

    key = (abs_path, scale_px)
    tex = ITEM_TEXTURES.get(key)
    if tex is not None:
        return tex

    if not os.path.exists(abs_path):
        return None

    try:
        img = pygame.image.load(abs_path).convert_alpha()
        tex = pygame.transform.smoothscale(img, (scale_px, scale_px))
        ITEM_TEXTURES[key] = tex
        return tex
    except Exception:
        return None

class Entity:
    def __init__(self, x, y, symbol, entity_type="player"):
        self.x = x
        self.y = y
        self.symbol = symbol
        self.entity_type = entity_type
        if entity_type == "player":
            self.max_hp           = 100
            self.hp               = self.max_hp
            self.speed            = (TILE_SIZE/50)*2 + (TILE_SIZE/50)*0.25*config.itdiff()
            self.color            = RED
            self.attack_speed     = 0.75 - 0.025*config.itdiff()
            self.damage           = 2
            self.attack_types     = ["+", "-"]
            self.attack_index     = 0
            self.attack_type      = self.attack_types[self.attack_index]
            self.min_damage       = 1
            self.max_damage       = 3
            self.attack_range     = 1
            self.size             = TILE_SIZE * 0.25
            self.last_damage_time = 0
            self.last_attack_time = 0
            self.last_direction   = "down"
        elif entity_type.startswith("B_"):
            attrs = boss_types(config.itdiff()).get(entity_type, boss_types(config.itdiff())["B_a"])
            self.hp               = attrs["hp"]
            self.speed            = attrs["speed"]
            self.color            = attrs["color"]
            self.attack_speed     = attrs["attack_speed"]
            self.damage           = attrs["damage"]
            self.size             = attrs["size"]
            self.attack_type      = attrs["attack_type"]
            self.last_attack_time = 0
        elif entity_type == "item":
            self.entity_type = 'item'
            self.size = TILE_SIZE * 0.5
            self.color = BLACK
            info = item_types.get(symbol, {})
            tex_path = info.get("texture")
            self.texture = pygame.image.load(tex_path).convert_alpha() if tex_path else None
        elif entity_type == "coin":
            self.entity_type = "coin"
            self.size = TILE_SIZE*0.5
            self.color = YELLOW
            info = coin_types.get(symbol, {})
            self.coin_value = info.get("value", 1)  # 기본 1
            tex_path = info.get("texture")
            self.texture = pygame.image.load(tex_path).convert_alpha() if tex_path else None
        else:
            attrs = enemy_types(config.itdiff()).get(entity_type, enemy_types(config.itdiff())["a"])
            self.hp               = attrs["hp"]
            self.speed            = attrs["speed"]
            self.color            = attrs["color"]
            self.attack_speed     = attrs["attack_speed"]
            self.damage           = attrs["damage"]
            self.size             = attrs["size"]
            self.last_attack_time = 0
            self.attack_type      = attrs["attack_type"]

    def draw(self):
        screen = pygame.display.get_surface()
        rect = pygame.Rect(int(self.x), int(self.y), int(self.size), int(self.size))

        # 아이템: 기존 스타일 유지 (필요 없다면 이 블록 삭제)
        if getattr(self, "entity_type", "") == "item":
            tex = self.texture
            if tex:
                if tex.get_size() != rect.size:
                    tex = pygame.transform.scale(tex, rect.size)
                screen.blit(tex, (rect.x + self.size*0.5, rect.y + self.size*0.5))
            else:
                # 폴백(텍스처 로드 실패 시): 작은 사각형
                BLACK = (0, 0, 0)
                cx = self.x + TILE_SIZE * 0.5 - rect.size * 0.5
                cy = self.y + TILE_SIZE * 0.5 - rect.size * 0.5
                pygame.draw.rect(screen, BLACK, (cx, cy, self.size, self.size))
            return
        elif getattr(self, "entity_type", "") == "coin":
            tex = self.texture
            if tex:
                if tex.get_size() != rect.size:
                    tex = pygame.transform.scale(tex, rect.size)
                screen.blit(tex, rect)
            return
                
        # 플레이어: 채움 유지
        if getattr(self, "entity_type", "") == "player":
            pygame.draw.rect(screen, self.color, rect)
            return

        # 적/보스: 채우기 없이 테두리
        pygame.draw.rect(screen, self.color, rect, 2)

        # 중앙 텍스트: attack_type + damage(damge)
        pre = getattr(self, "attack_type", None)
        amt = getattr(self, "hp", None)
        if pre and (amt is not None):
            try:
                amt_i = int(amt)
            except (TypeError, ValueError):
                amt_i = amt
            label = f"{pre} {amt_i}"

            font = pygame.font.SysFont(None, int(self.size * 0.6), bold=True)
            text = font.render(label, True, self.color)
            text_rect = text.get_rect(center=rect.center)
            screen.blit(text, text_rect)
    
    def draw_attack_range(self):
        # (선택) 공격 범위 원을 그립니다. 디버그용으로만 사용하세요.
        center = (int(self.x + self.size/2), int(self.y + self.size/2))
        pygame.draw.circle(pygame.display.get_surface(), (255, 255, 0),
                           center, TILE_SIZE, 1)


    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.size, self.size)

    def move_towards(self, target_x, target_y, tilemap, stop_distance=10, enemies=None):
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)
        if dist <= stop_distance:
            return
            # 정규화
        dx_norm, dy_norm = dx / dist, dy / dist

        # X축 이동 시 맵 충돌 검사
        new_x = self.x + dx_norm * self.speed
        if not check_tile_collision(new_x, self.y, self.size, tilemap):
            self.x = new_x

        # Y축 이동 시 맵 충돌 검사
        new_y = self.y + dy_norm * self.speed
        if not check_tile_collision(self.x, new_y, self.size, tilemap):
            self.y = new_y

        # 다른 적들과의 충돌 방지 (살짝 밀어내기)
        if enemies:
            for other in enemies:
                if other is not self and check_corner_collision(self, other):
                    ox = (self.get_rect().centerx - other.get_rect().centerx) / 2
                    oy = (self.get_rect().centery - other.get_rect().centery) / 2
                    self.x += ox * 0.1
                    self.y += oy * 0.1

    def attack(self, player):
        now = time.time()
        if now - self.last_attack_time < self.attack_speed:
            return

        # 중심거리 + 마진
        cx, cy = self.x + self.size/2, self.y + self.size/2
        px, py = player.x + player.size/2, player.y + player.size/2
        center_dist = math.hypot(cx - px, cy - py)
        contact_threshold = (self.size + player.size)/2 + config.CONTACT_MARGIN_PX
        near_contact = center_dist <= contact_threshold

        # 직전 프레임의 접촉 그레이스
        grace = (now - getattr(self, "last_touch_time", 0)) <= config.CONTACT_GRACE_SEC

        if (near_contact or grace) and (now - player.last_damage_time) >= 1:
            dmg = max(1,int(abs(self.hp)))
            player.hp -= dmg
            player.last_damage_time = now

        # 쿨타임 갱신(명중 여부와 무관하게 시도 간격 제한)
        self.last_attack_time = now


# ── [수정] 플레이어의 공격: 부호 연산만 적용, 제거 조건은 hp == 0 ──
    def attack_enemies(self, enemies, bosses=None):
        now = time.time()
        if now - self.last_attack_time < self.attack_speed:
            return []

        attack_range = self.attack_range * TILE_SIZE
        attack_width = TILE_SIZE*1.1  # 기존보다 살짝 넓힘
        px = self.x + self.size / 2
        py = self.y + self.size / 2

        targets = []
        coin_drop = []
        if enemies:
            targets.extend(enemies)
        if bosses:
            targets.extend(bosses)

        for target in targets:
            ex = target.x + target.size / 2
            ey = target.y + target.size / 2

            in_range = False
            if self.last_direction == "up":
                if (abs(ex - px) <= attack_width / 2 and
                    py - attack_range <= ey < py):
                    in_range = True
            elif self.last_direction == "down":
                if (abs(ex - px) <= attack_width / 2 and
                    py < ey <= py + attack_range):
                    in_range = True
            elif self.last_direction == "left":
                if (abs(ey - py) <= attack_width / 2 and
                    px - attack_range <= ex < px):
                    in_range = True
            elif self.last_direction == "right":
                if (abs(ey - py) <= attack_width / 2 and
                    px < ex <= px + attack_range):
                    in_range = True

            if not in_range:
                continue

            current_attack_type = self.attack_types[self.attack_index]

            # 공격 타입별 처리
            if ((current_attack_type == '+' and target.attack_type == "-")
                or (current_attack_type == "-" and target.attack_type == "+")):
                target.hp -= self.damage
                if target.hp < 0:
                    target.hp = abs(target.hp)  # 음수면 절대값으로 변환
                    if target.attack_type == "+":
                        target.attack_type = "-"
                    elif target.attack_type == "-":
                        target.attack_type = "+"
            else:
                target.hp += self.damage

            print(f"[공격] {target.symbol} hp={target.hp} "
                f"(ptype={current_attack_type}, pdmg={self.damage})")

            # ── 코인 드랍: '사망' 판정 시 1회 ──
            # 이 게임 규칙은 hp == 0 이 사망
            if getattr(target, "entity_type", "") != "player" and target.hp == 0:
                # 지역 import로 순환참조 회피
                for drop in generate_coin_drop(target.x, target.y, target.size):
                    cx, cy = drop["pos"]
                    coin_key = drop["key"]
                    coin = Entity(cx - TILE_SIZE * 0.5, cy - TILE_SIZE * 0.5,
                                  coin_key, entity_type="coin")
                    coin_drop.append(coin)
                
            self.last_attack_time = now  # 맞췄을 때만 쿨타임 초기화

        # hp == 0 만 제거
        if enemies:
            enemies[:] = [e for e in enemies if e.hp != 0]
        if bosses:
            bosses[:] = [b for b in bosses if b.hp != 0]

        return coin_drop


def draw_attack_area(self):
    """플레이어의 전방 공격 범위를 시각적으로 사각형으로 표시합니다."""
    if self.entity_type != "player":
        return

    attack_range = self.attack_range * TILE_SIZE
    attack_width = TILE_SIZE * 1.1
    px = self.x + self.size / 2
    py = self.y + self.size / 2

    screen = pygame.display.get_surface()
    label = f"{self.attack_range}"
    font = pygame.font.SysFont(None, int(TILE_SIZE*0.65), bold=False)
    text = font.render(label, True, YELLOW)
    
    if self.last_direction == "up":
        rect = pygame.Rect(
            px - attack_width/2,
            py - attack_range,
            attack_width,
            attack_range
        )
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)
    elif self.last_direction == "down":
        rect = pygame.Rect(
            px - attack_width/2,
            py,
            attack_width,
            attack_range
        )
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)
    elif self.last_direction == "left":
        rect = pygame.Rect(
            px - attack_range,
            py - attack_width/2,
            attack_range,
            attack_width
        )
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)
    elif self.last_direction == "right":
        rect = pygame.Rect(
            px,
            py - attack_width/2,
            attack_range,
            attack_width
        )
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)
    else:
        return

    pygame.draw.rect(screen, YELLOW, rect, 2)
