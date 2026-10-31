import math
import random
import sys
import json
from pathlib import Path

import pygame
import pygame.gfxdraw

W, H = 1000, 660
FPS = 60
JERSEY_FONT = None

GRASS1 = (52, 148, 70)
GRASS2 = (44, 134, 62)
LINE = (235, 245, 235)
BLUE = (40, 110, 230)
BLUE_D = (20, 60, 150)
RED = (220, 50, 50)
RED_D = (130, 20, 20)
GOLD = (250, 200, 60)
WHITE = (250, 250, 250)
DARK = (14, 20, 28)
BG = (22, 30, 42)
PANEL = (32, 42, 58)
PANEL2 = (46, 60, 82)
GREY = (150, 160, 175)
GREEN = (80, 210, 120)
ORANGE = (240, 140, 60)

FIELD = pygame.Rect(90, 50, W - 180, H - 90)
GOAL = pygame.Rect(W // 2 - 75, FIELD.top - 22, 150, 22)

LEAGUE_TEAMS = [
    "Vila Nova FC", "Atletico Serrano", "Uniao Litoral", "Gremio Central",
    "EC Sul", "Real Paulistano", "Ferroviario", "Botafogo do Vale",
    "Ipiranga AC", "Nautico Leste", "Aurora Esporte", "Porto Real",
    "Estrela do Norte", "Academicos FC", "Racing Metropolitano", "Independente"
]

TEAM_COLORS = {
    "Vila Nova FC": (35, 105, 225), "Atletico Serrano": (205, 45, 48),
    "Uniao Litoral": (20, 145, 125), "Gremio Central": (35, 65, 150),
    "EC Sul": (235, 235, 235), "Real Paulistano": (185, 35, 45),
    "Ferroviario": (30, 30, 35), "Botafogo do Vale": (35, 35, 40),
    "Ipiranga AC": (235, 185, 35), "Nautico Leste": (25, 130, 195),
    "Aurora Esporte": (130, 65, 190), "Porto Real": (25, 95, 155),
    "Estrela do Norte": (235, 125, 35), "Academicos FC": (35, 145, 65),
    "Racing Metropolitano": (80, 100, 190), "Independente": (170, 55, 95)
}

NATIONS = [
    "Brasil", "Portugal", "Argentina", "Uruguai",
    "Angola", "Mocambique", "Chile", "Colombia"
]

POSITIONS = ["Atacante", "Meia", "Ponta"]
SEASON_ROUNDS = (len(LEAGUE_TEAMS) - 1) * 2


def clamp(v, a, b):
    return max(a, min(b, v))


def aacircle(s, color, pos, r):
    x, y, r = int(pos[0]), int(pos[1]), int(r)
    pygame.gfxdraw.filled_circle(s, x, y, r, color)
    pygame.gfxdraw.aacircle(s, x, y, r, color)


def shade(c, d):
    return tuple(clamp(v + d, 0, 255) for v in c)


def gradient(s, top, bottom):
    for y in range(H):
        t = y / H
        c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        pygame.draw.line(s, c, (0, y), (W, y))


# ----------------------------------------------------------------- liga
class League:
    def __init__(self, teams):
        self.teams = list(teams)
        self.strength = {t: random.randint(40, 75) for t in self.teams}
        self.table = {
            t: dict(P=0, V=0, E=0, D=0, GP=0, GC=0, PTS=0)
            for t in self.teams
        }
        self.fixtures = self.make_fixtures()
        self.round = 0
        self.last_results = []

    def make_fixtures(self):
        t = self.teams[:]
        random.shuffle(t)
        n = len(t)
        rounds = []

        for r in range(n - 1):
            pairs = []
            for i in range(n // 2):
                a, b = t[i], t[n - 1 - i]
                pairs.append((a, b) if r % 2 == 0 else (b, a))

            rounds.append(pairs)
            t = [t[0]] + [t[-1]] + t[1:-1]

        return rounds + [[(b, a) for a, b in rnd] for rnd in rounds]

    def user_fixture(self, club):
        for a, b in self.fixtures[self.round]:
            if club in (a, b):
                return a, b
        return None

    def record(self, home, away, gh, ga):
        for t, gf, gc in ((home, gh, ga), (away, ga, gh)):
            r = self.table[t]
            r["P"] += 1
            r["GP"] += gf
            r["GC"] += gc

            if gf > gc:
                r["V"] += 1
                r["PTS"] += 3
            elif gf == gc:
                r["E"] += 1
                r["PTS"] += 1
            else:
                r["D"] += 1

    def sim_goals(self, s):
        lam = 0.6 + s / 60
        g, L, p = 0, math.exp(-lam), 1.0

        while True:
            p *= random.random()
            if p < L:
                return g
            g += 1

    def play_round(self, club, user_home_goals, user_away_goals):
        self.last_results = []

        for a, b in self.fixtures[self.round]:
            if club in (a, b):
                ga, gb = user_home_goals, user_away_goals
            else:
                ga = self.sim_goals(self.strength[a] + 5)
                gb = self.sim_goals(self.strength[b])

            self.record(a, b, ga, gb)
            self.last_results.append((a, ga, gb, b))

        self.round += 1

    def standings(self):
        return sorted(
            self.teams,
            key=lambda t: (
                -self.table[t]["PTS"],
                -(self.table[t]["GP"] - self.table[t]["GC"]),
                -self.table[t]["GP"],
                t
            )
        )

    def finished(self):
        return self.round >= len(self.fixtures)


# --------------------------------------------------------------- jogador
class Player:
    def __init__(self):
        self.name = ""
        self.nation = NATIONS[0]
        self.position = POSITIONS[0]
        self.age = 17
        self.shoot = 45
        self.pass_ = 45
        self.speed = 45
        self.energy = 100
        self.money = 1000
        self.wage = 150
        self.club = ""
        self.fame = 0
        self.goals = 0
        self.season_goals = 0
        self.matches = 0
        self.ratings = []
        self.coach = 50
        self.fans = 30
        self.mates = 50
        self.season = 1

    def avg(self):
        return sum(self.ratings) / len(self.ratings) if self.ratings else 0.0

    def overall(self):
        return round((self.shoot + self.pass_ + self.speed) / 3)


# ---------------------------------------------------------------- UI
class Button:
    def __init__(self, rect, text, color=PANEL2):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.color = color
        self.enabled = True

    def draw(self, s, font, mouse, selected=False):
        hov = self.rect.collidepoint(mouse) and self.enabled
        c = self.color if self.enabled else (55, 58, 64)

        if hov:
            c = shade(c, 28)

        if selected:
            c = shade(GOLD, -60)

        pygame.draw.rect(s, DARK, self.rect.move(0, 4), border_radius=10)
        pygame.draw.rect(s, c, self.rect, border_radius=10)
        pygame.draw.rect(
            s, GOLD if (hov or selected) else shade(c, 40),
            self.rect, 2, border_radius=10
        )

        t = font.render(self.text, True, WHITE if self.enabled else GREY)
        s.blit(t, t.get_rect(center=self.rect.center))

    def hit(self, ev):
        return (
            self.enabled
            and ev.type == pygame.MOUSEBUTTONDOWN
            and ev.button == 1
            and self.rect.collidepoint(ev.pos)
        )


class Dude:
    """Jogador desenhado em estilo 2D: cabeça, tronco, braços, pernas e uniforme."""

    def __init__(self, x, y, team, number=None, role="field"):
        self.x, self.y, self.team = float(x), float(y), team
        self.r = 12
        self.bob = random.random() * 6
        self.number = number if number is not None else random.randint(2, 99)
        self.role = role
        self.facing = -math.pi / 2
        self.skin = random.choice([
            (224, 178, 139), (190, 135, 98),
            (135, 91, 65), (242, 204, 170)
        ])
        self.hair = random.choice([
            (35, 27, 22), (75, 48, 28),
            (25, 25, 28), (125, 83, 45)
        ])
        self.kit = {
            0: (35, 105, 225),
            1: (205, 45, 48),
            2: (242, 190, 35)
        }[team]
        self.kit_dark = shade(self.kit, -65)
        self.shorts = {
            0: (22, 48, 115),
            1: (245, 245, 245),
            2: (35, 35, 35)
        }[team]
        self.socks = self.kit
        self.step = random.random() * math.tau

    def draw(self, s, t, highlight=False, label=None, font=None):
        bob = math.sin(t * 0.12 + self.bob) * 1.0
        x, y = int(self.x), int(self.y + bob)
        moving_phase = t * 0.28 + self.step
        leg_swing = math.sin(moving_phase) * 3
        arm_swing = math.sin(moving_phase + math.pi) * 2

        pygame.draw.ellipse(s, (18, 48, 25), (x - 11, y + 10, 23, 8))

        pygame.draw.line(
            s, self.skin, (x - 4, y + 5),
            (x - 5 - leg_swing, y + 14), 4
        )
        pygame.draw.line(
            s, self.skin, (x + 4, y + 5),
            (x + 5 + leg_swing, y + 14), 4
        )

        pygame.draw.line(
            s, self.socks, (x - 5 - leg_swing, y + 10),
            (x - 5 - leg_swing, y + 15), 4
        )
        pygame.draw.line(
            s, self.socks, (x + 5 + leg_swing, y + 10),
            (x + 5 + leg_swing, y + 15), 4
        )

        pygame.draw.ellipse(s, (28, 28, 32), (x - 10 - leg_swing, y + 13, 8, 4))
        pygame.draw.ellipse(s, (28, 28, 32), (x + 3 + leg_swing, y + 13, 8, 4))

        pygame.draw.line(
            s, self.skin, (x - 7, y - 5),
            (x - 11 - arm_swing, y + 3), 4
        )
        pygame.draw.line(
            s, self.skin, (x + 7, y - 5),
            (x + 11 + arm_swing, y + 3), 4
        )

        body = pygame.Rect(x - 8, y - 10, 16, 18)
        pygame.draw.rect(s, self.kit_dark, body.inflate(2, 2), border_radius=5)
        pygame.draw.rect(s, self.kit, body, border_radius=4)
        pygame.draw.line(s, shade(self.kit, 45), (x - 4, y - 8), (x - 4, y + 5), 2)

        global JERSEY_FONT
        if JERSEY_FONT is None:
            JERSEY_FONT = pygame.font.SysFont("arial", 8, bold=True)

        num = JERSEY_FONT.render(str(self.number), True, WHITE)
        s.blit(num, num.get_rect(center=(x, y - 1)))

        pygame.draw.rect(s, self.skin, (x - 3, y - 14, 6, 6))
        pygame.draw.circle(s, self.skin, (x, y - 17), 7)
        pygame.draw.arc(s, self.hair, (x - 7, y - 24, 14, 10), math.pi, math.tau, 3)
        pygame.draw.circle(s, self.hair, (x - 5, y - 20), 2)

        if self.role == "keeper":
            pygame.draw.line(s, WHITE, (x - 7, y - 6), (x + 7, y - 6), 2)

        if highlight:
            pygame.draw.circle(s, GOLD, (x, y - 4), 19, 2)
            pygame.draw.circle(s, (255, 235, 130), (x, y - 4), 21, 1)

        if label and font:
            tx = font.render(label, True, WHITE)
            s.blit(tx, tx.get_rect(center=(x, y - 34)))


def draw_field(s):
    s.fill((34, 104, 50))
    n = 12
    st = FIELD.height / n

    for i in range(n):
        pygame.draw.rect(
            s, GRASS1 if i % 2 == 0 else GRASS2,
            (FIELD.left - 50, FIELD.top + i * st, FIELD.width + 100, st + 1)
        )

    pygame.draw.rect(s, LINE, FIELD, 3)
    pygame.draw.rect(s, LINE, (W // 2 - 200, FIELD.top, 400, 140), 3)
    pygame.draw.rect(s, LINE, (W // 2 - 95, FIELD.top, 190, 52), 3)
    pygame.draw.arc(
        s, LINE, (W // 2 - 70, FIELD.top + 80, 140, 120),
        math.pi + 0.65, 2 * math.pi - 0.65, 3
    )
    aacircle(s, LINE, (W // 2, FIELD.top + 100), 4)
    pygame.draw.arc(s, LINE, (W // 2 - 95, FIELD.bottom - 95, 190, 190), 0, math.pi, 3)

    for cx, cy, a0, a1 in (
        (FIELD.left, FIELD.top, -math.pi / 2, 0),
        (FIELD.right, FIELD.top, math.pi, 3 * math.pi / 2)
    ):
        pygame.draw.arc(s, LINE, (cx - 14, cy - 14, 28, 28), a0, a1, 2)

    pygame.draw.rect(s, (215, 215, 215), GOAL)

    for x in range(GOAL.left + 6, GOAL.right, 9):
        pygame.draw.line(s, (165, 165, 165), (x, GOAL.top), (x, GOAL.bottom), 1)

    for y in range(GOAL.top + 4, GOAL.bottom, 6):
        pygame.draw.line(s, (165, 165, 165), (GOAL.left, y), (GOAL.right, y), 1)

    pygame.draw.rect(s, WHITE, GOAL, 3)


# --------------------------------------------------------------- partida
class Match:
    CHANCES = 8

    def __init__(self, game, home, away):
        self.g = game
        self.p = game.player
        self.home, self.away = home, away
        self.user_home = home == self.p.club
        self.opp = away if self.user_home else home
        self.opp_str = game.league.strength[self.opp]
        self.us, self.them = 0, 0
        self.chance = 0
        self.passes = 0
        self.rating = 6.0
        self.msg, self.msg_t = "", 0
        self.wait = 0
        self.over = False
        self.t = 0
        self.log = []
        self.my_goals = 0
        self.new_chance()

    @property
    def minute(self):
        return clamp(int((self.chance - 1) * 90 / self.CHANCES) + 1, 1, 90)

    def flash(self, m):
        self.msg, self.msg_t = m, 110

    def new_chance(self):
        self.chance += 1

        if self.chance > self.CHANCES:
            self.finish()
            return

        diff = 0.8 + self.opp_str / 70
        roll = random.random()

        if roll < min(0.075, 0.035 * diff):
            self.them += 1
            self.log.append(f"{self.minute}' Gol do {self.opp}")
            self.flash(f"Gol do {self.opp}!  {self.minute}'")
        elif roll < 0.085:
            self.us += 1
            self.log.append(f"{self.minute}' Gol do {self.p.club}")
            self.flash(f"Seu time marcou! {self.minute}'")

        self.me = Dude(
            random.randint(W // 2 - 45, W // 2 + 45),
            FIELD.bottom - 250, 0, number=10
        )

        self.holder = self.me
        self.kicker = self.me

        home_positions = [
            (FIELD.bottom - 145, FIELD.left + 150),
            (FIELD.bottom - 145, FIELD.right - 150),
            (FIELD.bottom - 290, W // 2 - 115),
            (FIELD.bottom - 290, W // 2 + 115),
        ]

        self.mates = [
            Dude(x + random.randint(-10, 10), y + random.randint(-10, 10),
                 0, number=n + 7)
            for n, (y, x) in enumerate(home_positions)
        ]

        away_positions = [
            (FIELD.top + 145, FIELD.left + 150),
            (FIELD.top + 145, FIELD.right - 150),
            (FIELD.top + 290, W // 2 - 115),
            (FIELD.top + 290, W // 2 + 115),
            (FIELD.top + 225, W // 2),
        ]

        self.opps = [
            Dude(x + random.randint(-12, 12), y + random.randint(-10, 10),
                 1, number=n + 2)
            for n, (y, x) in enumerate(away_positions)
        ]

        home_color = TEAM_COLORS.get(self.p.club, BLUE)
        away_color = TEAM_COLORS.get(self.opp, RED)

        for athlete in [self.me] + self.mates:
            athlete.kit = home_color
            athlete.kit_dark = shade(home_color, -65)
            athlete.socks = home_color

        for athlete in self.opps:
            athlete.kit = away_color
            athlete.kit_dark = shade(away_color, -65)
            athlete.socks = away_color

        self.keeper = Dude(W // 2, FIELD.top + 16, 2, number=1, role="keeper")
        self.keeper.kit = (245, 205, 45)
        self.keeper.kit_dark = shade(self.keeper.kit, -65)
        self.keeper.socks = self.keeper.kit

        self.keeper_speed = 1.8 + self.opp_str / 58
        self.keeper_reaction = random.uniform(0.82, 1.18)

        self.phase = random.choice([
            "Contra-ataque", "Ataque organizado", "Pressão alta",
            "Bola recuperada", "Jogada trabalhada"
        ])

        self.pass_target = None
        self.ball = [self.holder.x, self.holder.y - 18]
        self.vel = [0.0, 0.0]
        self.moving = False
        self.aiming = False

        self.dribble_cooldown = 0
        self.dribble_escape = 0
        self.dribble_dir = (0.0, -1.0)
        self.dribble_flash = 0

        self.shot_mode = False
        self.shot_origin = tuple(self.ball)
        self.shot_aim_point = (self.ball[0], self.ball[1] - 120)
        self.shot_dragging = False

        self.shot_confirm_rect = pygame.Rect(W // 2 - 155, H - 58, 150, 42)
        self.shot_cancel_rect = pygame.Rect(W // 2 + 5, H - 58, 150, 42)

    def end_chance(self, m, dr):
        self.rating += dr
        self.flash(m)
        self.moving = False
        self.aiming = False
        self.wait = 75

    def finish(self):
        self.over = True
        p = self.p
        self.final_rating = round(clamp(self.rating, 1, 10), 1)
        p.ratings.append(self.final_rating)
        p.matches += 1
        p.energy = clamp(p.energy - 22, 0, 100)

        win, draw = self.us > self.them, self.us == self.them
        self.prize = int(
            p.wage + self.final_rating * 30 + self.my_goals * 150
            + (250 if win else 80 if draw else 0)
        )

        p.money += self.prize
        p.fame += int(self.final_rating + self.my_goals * 4)
        p.coach = clamp(p.coach + (self.final_rating - 6) * 4, 0, 100)
        p.fans = clamp(p.fans + self.my_goals * 5 + (3 if win else -2), 0, 100)
        p.mates = clamp(p.mates + self.passes - 1, 0, 100)

        gh, ga = (self.us, self.them) if self.user_home else (self.them, self.us)
        self.g.league.play_round(p.club, gh, ga)
    def update(self):
        # Pausa total durante a mira.
        if self.shot_mode:
            return

        self.t += 1

        if self.msg_t > 0:
            self.msg_t -= 1

        if self.dribble_cooldown > 0:
            self.dribble_cooldown -= 1

        if self.dribble_escape > 0:
            self.dribble_escape -= 1

        if self.dribble_flash > 0:
            self.dribble_flash -= 1

        if self.over:
            return

        if self.wait > 0:
            self.wait -= 1
            if self.wait == 0:
                self.new_chance()
            return

        if self.moving and self.vel[1] < 0:
            frames_to_goal = max(
                0,
                (self.ball[1] - FIELD.top) / max(1.0, abs(self.vel[1]))
            )
            predicted_x = (
                self.ball[0]
                + self.vel[0] * min(frames_to_goal, 18) * 0.72
            )
            tx = clamp(predicted_x, GOAL.left + 12, GOAL.right - 12)
        else:
            tx = clamp(self.ball[0], GOAL.left + 22, GOAL.right - 22)

        keeper_step = self.keeper_speed * (
            self.keeper_reaction if self.moving else 0.7
        )
        self.keeper.x += clamp(
            tx - self.keeper.x, -keeper_step, keeper_step
        )

        if not self.moving:
            keys = pygame.key.get_pressed()

            dx = (
                int(keys[pygame.K_RIGHT] or keys[pygame.K_d])
                - int(keys[pygame.K_LEFT] or keys[pygame.K_a])
            )
            dy = (
                int(keys[pygame.K_DOWN] or keys[pygame.K_s])
                - int(keys[pygame.K_UP] or keys[pygame.K_w])
            )

            if dx or dy:
                length = math.hypot(dx, dy) or 1
                run_speed = 2.1 + self.p.speed * 0.045

                self.holder.x = clamp(
                    self.holder.x + dx / length * run_speed,
                    FIELD.left + 15,
                    FIELD.right - 15
                )
                self.holder.y = clamp(
                    self.holder.y + dy / length * run_speed,
                    FIELD.top + 25,
                    FIELD.bottom - 15
                )

                self.holder.facing = math.atan2(dy, dx)
                self.ball = [
                    self.holder.x + dx / length * 3,
                    self.holder.y - 15 + dy / length * 3
                ]
                self.p.energy = max(0, self.p.energy - 0.003)

            # Companheiros abrem linhas de passe.
            for i, mate in enumerate(self.mates):
                lane = i - (len(self.mates) - 1) / 2
                row = 0

                target_x = clamp(
                    self.holder.x + lane * 118,
                    FIELD.left + 28,
                    FIELD.right - 28
                )
                target_y = clamp(
                    self.holder.y - 72 - row * 78,
                    FIELD.top + 55,
                    FIELD.bottom - 35
                )

                if (
                    abs(mate.x - self.holder.x) < 38
                    and abs(mate.y - self.holder.y) < 45
                ):
                    target_x += 55 if lane >= 0 else -55

                vx, vy = target_x - mate.x, target_y - mate.y
                dmate = math.hypot(vx, vy)

                if dmate > 7:
                    step = min(1.65, dmate * 0.035)
                    mate.x += vx / dmate * step
                    mate.y += vy / dmate * step
                    mate.facing = math.atan2(vy, vx)

            # Defesa adversária.
            spd = max(
                0.55,
                0.65 + self.opp_str / 190 - self.p.speed * 0.002
            )

            closest = min(
                self.opps,
                key=lambda d: math.hypot(
                    self.holder.x - d.x,
                    self.holder.y - d.y
                )
            )

            for i, o in enumerate(self.opps):
                if o is closest and self.dribble_escape > 0:
                    target_x = self.holder.x - self.dribble_dir[0] * 58
                    target_y = self.holder.y - self.dribble_dir[1] * 58
                elif o is closest:
                    target_x, target_y = self.holder.x, self.holder.y - 8
                else:
                    target_x = clamp(
                        self.holder.x
                        + (i - (len(self.opps) - 1) / 2) * 72,
                        FIELD.left + 25,
                        FIELD.right - 25
                    )
                    target_y = clamp(
                        self.holder.y - 35 - (i % 3) * 45,
                        FIELD.top + 45,
                        FIELD.bottom - 45
                    )

                vx, vy = target_x - o.x, target_y - o.y
                d = math.hypot(vx, vy)

                if d > 1 and (o is closest or d < 245):
                    o.x += vx / d * spd
                    o.y += vy / d * spd
                    o.facing = math.atan2(vy, vx)

                if o is closest and d < 21 and self.dribble_escape <= 0:
                    tackle_chance = clamp(
                        0.18 + self.opp_str / 220 - self.p.speed / 500,
                        0.12,
                        0.48
                    )

                    if random.random() < tackle_chance:
                        self.end_chance(
                            "Desarme! O adversario recuperou a bola.",
                            -0.45
                        )
                        return

            return

        # Defensores acompanham a bola em movimento.
        for i, defender in enumerate(self.opps):
            tx = clamp(
                self.ball[0] + (i - (len(self.opps) - 1) / 2) * 30,
                FIELD.left + 18,
                FIELD.right - 18
            )
            ty = clamp(
                self.ball[1] - 26 - (i % 3) * 28,
                FIELD.top + 30,
                FIELD.bottom - 25
            )

            vx, vy = tx - defender.x, ty - defender.y
            d = math.hypot(vx, vy)

            if d > 2:
                step = min(1.15 + self.opp_str / 150, d * 0.025)
                defender.x += vx / d * step
                defender.y += vy / d * step

        self.ball[0] += self.vel[0]
        self.ball[1] += self.vel[1]
        self.vel[0] *= 0.985
        self.vel[1] *= 0.985

        sp = math.hypot(*self.vel)
        bx, by = self.ball

        if by < FIELD.top:
            if GOAL.left < bx < GOAL.right:
                self.us += 1

                if self.kicker is self.me:
                    self.my_goals += 1
                    self.p.goals += 1
                    self.p.season_goals += 1
                    self.log.append(
                        f"{self.minute}' GOL de {self.p.name}!"
                    )
                    self.end_chance("GOOOOOL! Que golaco!", 1.6)
                else:
                    self.log.append(
                        f"{self.minute}' Gol do {self.p.club} (assist. sua)"
                    )
                    self.end_chance("GOL! Assistencia sua!", 0.9)
            else:
                self.end_chance("Pra fora! Tiro de meta.", -0.2)

            return

        if not FIELD.collidepoint(bx, by):
            self.end_chance("Bola pra fora.", -0.2)
            return

        if math.hypot(bx - self.keeper.x, by - self.keeper.y) < 21:
            if sp > 7 and random.random() < 0.18:
                self.vel[0] *= -0.35
                self.vel[1] *= -0.25
                self.flash("O goleiro espalmou!")
            else:
                self.end_chance("Defesa do goleiro!", 0.15)
            return

        for o in self.opps:
            if math.hypot(bx - o.x, by - o.y) < 18 and sp < 13:
                self.end_chance("Interceptado!", -0.4)
                return

        for m in self.mates + [self.me]:
            if m is self.kicker:
                continue

            if math.hypot(bx - m.x, by - m.y) < 22 and sp < 11:
                self.passes += 1
                self.rating += 0.3 if self.kicker is self.me else 0.15
                self.holder = m
                self.moving = False
                self.vel = [0.0, 0.0]
                self.ball = [m.x, m.y - 15]

                if m is self.me:
                    self.flash("Recebeu! Continue a jogada.")
                else:
                    self.flash("Passe certo! Seu companheiro recebeu.")

                return

        if sp < 0.35:
            self.end_chance(
                "A bola parou... o adversario recuperou.",
                -0.2
            )

    def max_power(self):
        return 13 + self.p.shoot * 0.12

    def confirm_shot(self):
        """Executa o chute usando a direção escolhida e a força ajustada."""
        dx = self.shot_aim_point[0] - self.shot_origin[0]
        dy = self.shot_aim_point[1] - self.shot_origin[1]
        dist = math.hypot(dx, dy)

        if dist < 8:
            self.flash("Escolha uma direcao para chutar.")
            return

        power = self.shot_power
        skill = self.p.shoot

        distance_factor = clamp(
            (FIELD.bottom - self.shot_origin[1]) / FIELD.height,
            0.15,
            1.0
        )

        err = (
            (1.0 - skill / 110) * 0.11
            + (1.0 - distance_factor) * 0.07
        )

        ang = math.atan2(dy, dx) + random.uniform(-err, err)

        self.kicker = self.holder
        self.vel = [
            math.cos(ang) * power,
            math.sin(ang) * power
        ]

        self.shot_mode = False
        self.shot_dragging = False
        self.aiming = False
        self.moving = True
        self.flash("CHUTE!")

    def cancel_shot(self):
        self.shot_mode = False
        self.shot_dragging = False
        self.aiming = False
        self.moving = False
        self.ball = [self.holder.x, self.holder.y - 15]
        self.flash("Finalizacao cancelada.")

    def perform_dribble(self):
        """Executa uma finta/arrancada curta para vencer a marcacao."""
        if self.over or self.moving or self.wait > 0 or self.shot_mode:
            return

        if self.dribble_cooldown > 0:
            self.flash("Espere um pouco para tentar outro drible.")
            return

        keys = pygame.key.get_pressed()

        dx = (
            int(keys[pygame.K_RIGHT] or keys[pygame.K_d])
            - int(keys[pygame.K_LEFT] or keys[pygame.K_a])
        )
        dy = (
            int(keys[pygame.K_DOWN] or keys[pygame.K_s])
            - int(keys[pygame.K_UP] or keys[pygame.K_w])
        )

        if dx or dy:
            length = math.hypot(dx, dy)
            ux, uy = dx / length, dy / length
        else:
            ux = math.cos(self.holder.facing)
            uy = math.sin(self.holder.facing)

        self.dribble_dir = (ux, uy)

        self.holder.x = clamp(
            self.holder.x + ux * 24,
            FIELD.left + 18,
            FIELD.right - 18
        )
        self.holder.y = clamp(
            self.holder.y + uy * 24,
            FIELD.top + 28,
            FIELD.bottom - 18
        )

        self.holder.facing = math.atan2(uy, ux)

        self.ball = [
            clamp(
                self.holder.x + ux * 19,
                FIELD.left + 8,
                FIELD.right - 8
            ),
            clamp(
                self.holder.y - 15 + uy * 19,
                FIELD.top + 8,
                FIELD.bottom - 8
            )
        ]

        self.dribble_escape = 48
        self.dribble_cooldown = 92
        self.dribble_flash = 36
        self.p.energy = max(0, self.p.energy - 2.0)
        self.rating = min(10, self.rating + 0.08)
        self.flash("DRIBLE! Voce ganhou espaco.")

    def handle(self, ev):
        if self.over:
            return

        # Modo de mira: J confirma, ESC cancela.
        if self.shot_mode:
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_j:
                    self.confirm_shot()
                elif ev.key == pygame.K_ESCAPE:
                    self.cancel_shot()
                elif ev.key in (pygame.K_UP, pygame.K_w):
                    self.shot_power = min(
                        self.max_power(),
                        self.shot_power + 0.7
                    )
                elif ev.key in (pygame.K_DOWN, pygame.K_s):
                    self.shot_power = max(
                        3.0,
                        self.shot_power - 0.7
                    )

            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if FIELD.collidepoint(ev.pos):
                    self.shot_aim_point = ev.pos

            return

        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_j:
                if not self.moving and self.wait <= 0:
                    self.shot_mode = True
                    self.shot_origin = tuple(self.ball)
                    self.shot_aim_point = (
                        W // 2,
                        FIELD.top - 5
                    )
                    self.shot_power = min(8.0, self.max_power())
                    self.aiming = False
                    self.flash("Escolha a direcao e pressione J para chutar.")
                return

            if ev.key in (
                pygame.K_e,
                pygame.K_LSHIFT,
                pygame.K_RSHIFT
            ):
                self.perform_dribble()
                return

        if self.moving or self.wait > 0:
            return

        # Arrastar a bola agora serve exclusivamente para passes.
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if math.hypot(
                ev.pos[0] - self.ball[0],
                ev.pos[1] - self.ball[1]
            ) < 78:
                self.aiming = True

        elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1 and self.aiming:
            self.aiming = False

            dx = self.ball[0] - ev.pos[0]
            dy = self.ball[1] - ev.pos[1]
            dist = math.hypot(dx, dy)

            if dist < 10:
                return

            power = min(dist / 9, self.max_power())
            skill = self.p.pass_

            distance_factor = clamp(
                (FIELD.bottom - self.ball[1]) / FIELD.height,
                0.15,
                1.0
            )

            err = (
                (1.0 - skill / 110) * 0.075
                + (1.0 - distance_factor) * 0.07
            )

            ang = math.atan2(dy, dx) + random.uniform(-err, err)
            self.pass_target = None

            # Procura um companheiro na direção do passe.
            ux, uy = math.cos(ang), math.sin(ang)
            candidates = []

            for teammate in self.mates + [self.me]:
                if teammate is self.holder:
                    continue

                vx = teammate.x - self.ball[0]
                vy = teammate.y - self.ball[1]
                d = math.hypot(vx, vy)

                if 48 < d < 390:
                    dot = clamp((vx * ux + vy * uy) / d, -1, 1)
                    angle = math.acos(dot)

                    if angle < 0.62:
                        candidates.append((angle + d / 1800, teammate, d))

            if candidates:
                _, target, target_dist = min(
                    candidates,
                    key=lambda item: item[0]
                )

                self.pass_target = target
                ang = math.atan2(
                    target.y - self.ball[1],
                    target.x - self.ball[0]
                )
                power = clamp(
                    target_dist / 22,
                    4.5,
                    min(11.5, self.max_power())
                )

            self.kicker = self.holder
            self.vel = [
                math.cos(ang) * power,
                math.sin(ang) * power
            ]
            self.moving = True
    def draw(self, s, f):
        draw_field(s)
        draw_t = self.t

        for o in self.opps:
            o.draw(s, draw_t)

        for m in self.mates:
            m.draw(s, draw_t)

        self.keeper.draw(s, draw_t)

        if not self.over:
            if self.me is not self.holder:
                self.me.draw(
                    s, draw_t,
                    label=self.p.name.split()[0][:10],
                    font=f["s"]
                )

            self.holder.draw(
                s, draw_t,
                highlight=not self.moving,
                label=self.p.name.split()[0][:10]
                if self.holder is self.me else None,
                font=f["s"]
            )

            bx, by = self.ball
            pygame.gfxdraw.filled_ellipse(
                s, int(bx + 3), int(by + 5), 6, 3, (0, 0, 0, 100)
            )
            aacircle(s, WHITE, (bx, by), 6)
            pygame.gfxdraw.aacircle(s, int(bx), int(by), 6, (40, 40, 40))
            aacircle(s, (40, 40, 40), (bx, by), 2)

            # Indicador visual do passe.
            if self.aiming:
                mx, my = pygame.mouse.get_pos()
                dx = bx - mx
                dy = by - my
                dist = math.hypot(dx, dy)
                frac = min(dist / 9, self.max_power()) / self.max_power()
                col = (255, int(250 - 190 * frac), 60)

                if dist > 1:
                    ux, uy = dx / dist, dy / dist

                    for i in range(14, int(60 + frac * 240), 14):
                        aacircle(s, col, (bx + ux * i, by + uy * i), 3)

                pygame.draw.aaline(s, WHITE, (bx, by), (mx, my))

                bar = pygame.Rect(bx - 32, by + 28, 64, 8)
                pygame.draw.rect(s, DARK, bar, border_radius=4)
                pygame.draw.rect(
                    s, col,
                    (bar.x, bar.y, int(64 * frac), 8),
                    border_radius=4
                )

        # Tela de mira do chute.
        if self.shot_mode:
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((5, 8, 18, 145))
            s.blit(overlay, (0, 0))

            ox, oy = self.shot_origin
            ax, ay = self.shot_aim_point
            dx, dy = ax - ox, ay - oy
            dist = math.hypot(dx, dy)

            frac = clamp(
                self.shot_power / self.max_power(),
                0.08,
                1.0
            )

            if dist > 1:
                ux, uy = dx / dist, dy / dist

                for i in range(18, int(min(dist, 300)), 18):
                    aacircle(s, GOLD, (ox + ux * i, oy + uy * i), 4)

                pygame.draw.aaline(s, WHITE, (ox, oy), (ax, ay))
                aacircle(s, GOLD, (ax, ay), 8)

            title = f["l"].render("PREPARE O CHUTE", True, GOLD)
            s.blit(title, title.get_rect(center=(W // 2, 78)))

            sub = f["s"].render(
                "Clique no campo para mirar | Setas ↑/↓: forca | J: chutar | ESC: cancelar",
                True,
                WHITE
            )
            s.blit(sub, sub.get_rect(center=(W // 2, 112)))

            panel = pygame.Rect(W // 2 - 175, H - 120, 350, 110)
            pygame.draw.rect(s, (12, 18, 28), panel, border_radius=12)
            pygame.draw.rect(s, GOLD, panel, 2, border_radius=12)

            power_label = f["m"].render(
                f"FORCA: {int(frac * 100)}%",
                True,
                WHITE
            )
            s.blit(
                power_label,
                power_label.get_rect(center=(W // 2, H - 108))
            )

            pygame.draw.rect(
                s, (55, 60, 70),
                (W // 2 - 145, H - 88, 290, 7),
                border_radius=4
            )
            pygame.draw.rect(
                s, GOLD,
                (W // 2 - 145, H - 88, int(290 * frac), 7),
                border_radius=4
            )

            instruction = f["s"].render(
                "PRESSIONE J PARA CHUTAR",
                True,
                WHITE
            )
            s.blit(
                instruction,
                instruction.get_rect(center=(W // 2, H - 55))
            )

        # Dica de controles.
        hint = f["s"].render(
            "WASD/setas: conduzir | E/SHIFT: drible | "
            "J: mirar e chutar | Arraste a bola: passe",
            True,
            WHITE
        )
        s.blit(hint, (FIELD.left + 8, FIELD.bottom + 8))

        dribble_label = (
            "DRIBLE PRONTO"
            if self.dribble_cooldown <= 0
            else f"DRIBLE: {self.dribble_cooldown // 6 + 1}s"
        )

        dribble_color = GREEN if self.dribble_cooldown <= 0 else GREY
        dtext = f["s"].render(dribble_label, True, dribble_color)
        s.blit(dtext, (FIELD.right - dtext.get_width() - 8, FIELD.bottom + 8))

        # Placar.
        sb = pygame.Rect(W // 2 - 260, 6, 520, 34)
        pygame.draw.rect(s, DARK, sb, border_radius=8)

        gh, ga = (
            (self.us, self.them)
            if self.user_home
            else (self.them, self.us)
        )

        t = f["m"].render(
            f"{self.home}  {gh} - {ga}  {self.away}",
            True,
            WHITE
        )
        s.blit(t, t.get_rect(center=sb.center))

        clock = pygame.Rect(10, 8, 70, 30)
        pygame.draw.rect(s, DARK, clock, border_radius=6)

        t = f["m"].render(f"{self.minute}'", True, GOLD)
        s.blit(t, t.get_rect(center=clock.center))

        t = f["s"].render(
            f"{self.phase}  |  Lance "
            f"{min(self.chance, self.CHANCES)}/{self.CHANCES}   "
            f"Nota {clamp(self.rating, 1, 10):.1f}   "
            f"Energia {int(self.p.energy)}%",
            True,
            WHITE
        )
        s.blit(t, (W - t.get_width() - 12, 14))

        if self.msg_t > 0 and self.msg and not self.shot_mode:
            t = f["l"].render(self.msg, True, GOLD)
            r = t.get_rect(center=(W // 2, H // 2))
            box = r.inflate(44, 22)

            ov = pygame.Surface(box.size, pygame.SRCALPHA)
            ov.fill((0, 0, 0, 175))
            s.blit(ov, box)
            s.blit(t, r)


# ------------------------------------------------------------------ jogo
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Carreira de Craque - Futebol")
        self.s = pygame.display.set_mode((W, H))
        self.clock = pygame.time.Clock()

        F = pygame.font.SysFont
        self.f = {
            "s": F("arial", 15),
            "n": F("arial", 18),
            "m": F("arial", 20, bold=True),
            "l": F("arial", 32, bold=True),
            "xl": F("arial", 70, bold=True)
        }

        self.state = "title"
        self.p = Player()
        self.player = self.p
        self.league = None
        self.match = None
        self.note = ""
        self.tab = "carreira"
        self.t = 0
        self.offers = []
        self.intro_line = 0

        cx = W // 2

        self.b_new = Button(
            (105, 405, 300, 58),
            "NOVA CARREIRA",
            (30, 120, 70)
        )
        self.b_quit = Button(
            (105, 478, 300, 50),
            "SAIR DO JOGO",
            (120, 40, 40)
        )

        self.b_nation = [
            Button((140 + i * 125, 300, 115, 42), n)
            for i, n in enumerate(NATIONS)
        ]

        self.b_pos = [
            Button((300 + i * 140, 410, 130, 42), n)
            for i, n in enumerate(POSITIONS)
        ]

        self.b_next = Button(
            (cx - 120, 540, 240, 54),
            "CONTINUAR",
            (30, 120, 70)
        )

        self.b_offer = [
            Button(
                (120 + i * 260, 430, 240, 52),
                "ACEITAR CONTRATO",
                (30, 120, 70)
            )
            for i in range(3)
        ]

        self.b_more_offers = Button(
            (W // 2 - 145, 525, 290, 46),
            "VER OUTRAS PROPOSTAS",
            (65, 85, 120)
        )

        self.tabs = {
            k: Button((20 + i * 160, 92, 150, 40), lbl)
            for i, (k, lbl) in enumerate([
                ("carreira", "CARREIRA"),
                ("tabela", "TABELA"),
                ("treino", "TREINO"),
                ("loja", "LOJA")
            ])
        }

        self.b_play = Button(
            (W - 270, 92, 250, 40),
            "JOGAR PARTIDA",
            (30, 120, 70)
        )

        self.b_train = [
            Button((60, 210 + i * 70, 400, 52), lbl)
            for i, lbl in enumerate([
                "Treinar Chute  (-15 energia)",
                "Treinar Passe  (-15 energia)",
                "Treinar Velocidade  (-15 energia)",
                "Descansar  (+35 energia)"
            ])
        ]

        self.shop = [
            ("Chuteira Pro", 900, "shoot", 5),
            ("Aulas de Visao de Jogo", 700, "pass_", 5),
            ("Personal Trainer", 800, "speed", 5),
            ("Carro Esportivo", 3000, "fans", 15),
            ("Jantar com o Tecnico", 400, "coach", 10)
        ]

        self.b_shop = [
            Button((W - 240, 190 + i * 70, 180, 50), f"${it[1]}")
            for i, it in enumerate(self.shop)
        ]

        self.b_cont = Button(
            (cx - 130, 580, 260, 54),
            "CONTINUAR",
            (30, 120, 70)
        )

    # ---------------------------------------------------------- loop
    def run(self):
        while True:
            mouse = pygame.mouse.get_pos()

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                self.handle(ev)

            self.t += 1

            if self.state == "match":
                self.match.update()

            self.draw(mouse)
            pygame.display.flip()
            self.clock.tick(FPS)

    def make_offers(self):
        clubs = random.sample(LEAGUE_TEAMS, 3)
        self.offers = []

        for c in clubs:
            self.offers.append(dict(
                club=c,
                wage=random.choice([100, 150, 200, 250]),
                bonus=random.choice([300, 500, 800])
            ))

    def start_career(self, offer):
        p = self.p
        p.club = offer["club"]
        p.wage = offer["wage"]
        p.money += offer["bonus"]

        self.league = League(LEAGUE_TEAMS)
        self.state = "hub"
        self.tab = "carreira"
        self.note = (
            f"Bem-vindo ao {p.club}! "
            f"Luvas de ${offer['bonus']} recebidas."
        )

    def train(self, attr, label):
        p = self.p

        if p.energy < 15:
            self.note = "Energia insuficiente! Descanse."
            return

        p.energy -= 15
        g = random.randint(1, 3)
        setattr(p, attr, min(99, getattr(p, attr) + g))
        self.note = f"Treino concluido: {label} +{g}"

    def next_season(self):
        p = self.p

        champ = self.league.standings()[0]
        pos = self.league.standings().index(p.club) + 1

        self.season_summary = (champ, pos, p.season_goals)

        p.season += 1
        p.age += 1
        p.season_goals = 0

        old = self.league.strength
        self.league = League(LEAGUE_TEAMS)

        self.league.strength = {
            t: clamp(old[t] + random.randint(-5, 6), 35, 90)
            for t in LEAGUE_TEAMS
        }

        self.state = "season"

    # ---------------------------------------------------------- eventos
    def handle(self, ev):
        p = self.p
        st = self.state

        if st == "title":
            if self.b_new.hit(ev):
                self.state = "name"
            elif self.b_quit.hit(ev):
                pygame.quit()
                sys.exit()

        elif st == "name":
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_RETURN and p.name.strip():
                    p.name = p.name.strip().title()
                    self.state = "profile"

                elif ev.key == pygame.K_BACKSPACE:
                    p.name = p.name[:-1]

                elif ev.unicode and ev.unicode.isprintable() and len(p.name) < 22:
                    p.name += ev.unicode

            if self.b_next.hit(ev) and p.name.strip():
                p.name = p.name.strip().title()
                self.state = "profile"

        elif st == "profile":
            for b in self.b_nation:
                if b.hit(ev):
                    p.nation = b.text

            for b in self.b_pos:
                if b.hit(ev):
                    p.position = b.text

            if self.b_next.hit(ev):
                if p.position == "Atacante":
                    p.shoot += 8
                elif p.position == "Meia":
                    p.pass_ += 8
                else:
                    p.speed += 8

                self.intro_line = 0
                self.state = "agent"

        elif st == "agent":
            if (
                self.b_next.hit(ev)
                or (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1)
            ):
                self.intro_line += 1

                if self.intro_line >= 4:
                    self.make_offers()
                    self.state = "offers"

        elif st == "offers":
            if self.b_more_offers.hit(ev):
                self.make_offers()

            for i, b in enumerate(self.b_offer):
                if b.hit(ev):
                    self.start_career(self.offers[i])

        elif st == "hub":
            for k, b in self.tabs.items():
                if b.hit(ev):
                    self.tab = k

            if self.b_play.hit(ev):
                if p.energy < 20:
                    self.note = "Voce esta exausto. Descanse antes do jogo!"
                else:
                    fixture = self.league.user_fixture(p.club)

                    if fixture is None:
                        self.note = (
                            "Temporada encerrada! "
                            "Avance para a próxima temporada."
                        )
                    else:
                        home, away = fixture
                        self.match = Match(self, home, away)
                        self.state = "match"
                        self.note = ""

            if self.tab == "treino":
                acts = [
                    ("shoot", "Chute"),
                    ("pass_", "Passe"),
                    ("speed", "Velocidade")
                ]

                for i, b in enumerate(self.b_train):
                    if b.hit(ev):
                        if i < 3:
                            self.train(*acts[i])
                        else:
                            p.energy = min(100, p.energy + 35)
                            self.note = "Voce descansou. Energia +35"

            if self.tab == "loja":
                for i, b in enumerate(self.b_shop):
                    if b.hit(ev):
                        name, price, attr, val = self.shop[i]

                        if p.money < price:
                            self.note = "Dinheiro insuficiente."
                        else:
                            p.money -= price

                            setattr(
                                p,
                                attr,
                                min(
                                    99 if attr in ("shoot", "pass_", "speed") else 100,
                                    getattr(p, attr) + val
                                )
                            )

                            self.note = f"Comprado: {name}!"

        elif st == "match":
            if self.match.over:
                if self.b_cont.hit(ev):
                    self.state = "results"
            else:
                self.match.handle(ev)

        elif st == "results":
            if self.b_cont.hit(ev):
                if self.league.finished():
                    self.next_season()
                else:
                    self.state = "hub"
                    self.tab = "tabela"

        elif st == "season":
            if self.b_cont.hit(ev):
                self.state = "hub"
                self.tab = "carreira"

    # ---------------------------------------------------------- desenho
    def text(self, txt, font, color, pos, center=False):
        t = self.f[font].render(str(txt), True, color)
        r = t.get_rect(center=pos) if center else t.get_rect(topleft=pos)
        self.s.blit(t, r)
        return r

    def panel(self, rect, title=None):
        r = pygame.Rect(rect)

        pygame.draw.rect(self.s, DARK, r.move(0, 4), border_radius=14)
        pygame.draw.rect(self.s, PANEL, r, border_radius=14)
        pygame.draw.rect(self.s, PANEL2, r, 2, border_radius=14)

        if title:
            self.text(title, "m", GOLD, (r.x + 18, r.y + 12))

        return r

    def bar(self, x, y, label, val, color, w=230):
        self.text(label, "n", GREY, (x, y))

        r = pygame.Rect(x + 130, y + 4, w, 14)
        pygame.draw.rect(self.s, DARK, r, border_radius=7)
        pygame.draw.rect(
            self.s, color,
            (r.x, r.y, int(r.w * val / 100), r.h),
            border_radius=7
        )

        self.text(int(val), "n", WHITE, (r.right + 10, y))

    def draw_table(self, rect, compact=False):
        L = self.league

        r = self.panel(
            rect,
            f"LIGA NACIONAL  -  Temporada {self.p.season}  -  "
            f"Rodada {min(L.round + 1, SEASON_ROUNDS)}/{SEASON_ROUNDS}"
        )

        cols = ["P", "V", "E", "D", "GP", "GC", "SG", "PTS"]
        x0 = r.x + 20
        y = r.y + 48

        self.text("#", "s", GREY, (x0, y))
        self.text("CLUBE", "s", GREY, (x0 + 30, y))

        cx = r.right - 30 - len(cols) * 46

        for i, c in enumerate(cols):
            self.text(c, "s", GREY, (cx + i * 46, y))

        y += 24
        available_h = max(18, r.height - 88)
        rowh = max(
            18,
            min(30 if not compact else 26, available_h // max(1, len(L.teams)))
        )

        for i, team in enumerate(L.standings()):
            row = pygame.Rect(r.x + 10, y - 4, r.w - 20, rowh - 2)

            if team == self.p.club:
                pygame.draw.rect(self.s, shade(BLUE_D, 10), row, border_radius=6)
            elif i % 2 == 0:
                pygame.draw.rect(self.s, shade(PANEL, 8), row, border_radius=6)

            marker = GREEN if i == 0 else (
                RED if i >= len(L.teams) - 2 else None
            )

            if marker:
                pygame.draw.rect(
                    self.s, marker,
                    (row.x, row.y, 4, row.h),
                    border_radius=2
                )

            d = L.table[team]

            self.text(i + 1, "n", WHITE, (x0, y))
            self.text(
                team, "n",
                GOLD if team == self.p.club else WHITE,
                (x0 + 30, y)
            )

            vals = [
                d["P"], d["V"], d["E"], d["D"],
                d["GP"], d["GC"],
                d["GP"] - d["GC"],
                d["PTS"]
            ]

            for j, v in enumerate(vals):
                self.text(
                    v,
                    "m" if j == 7 else "n",
                    WHITE,
                    (cx + j * 46, y)
                )

            y += rowh

    def draw(self, mouse):
        s = self.s
        p = self.p
        st = self.state

        if st == "title":
            # Abertura em estilo de simulador de carreira.
            gradient(s, (8, 18, 32), (5, 10, 17))

            for row in range(5):
                y = 28 + row * 27
                pygame.draw.rect(
                    s,
                    (22 + row * 2, 31 + row * 2, 46 + row * 2),
                    (0, y, W, 20)
                )

                for x in range(18, W, 34):
                    glow = 115 + int(
                        35 * math.sin(self.t * 0.035 + x * 0.018 + row)
                    )
                    pygame.draw.circle(s, (glow, glow, glow), (x, y + 9), 2)

            pygame.draw.polygon(
                s, (20, 76, 43),
                [(0, 220), (W, 220), (W, H), (0, H)]
            )

            for i in range(8):
                yy = 250 + i * 55
                pygame.draw.polygon(
                    s,
                    (24 + (i % 2) * 5, 88 + (i % 2) * 7, 48),
                    [
                        (0, yy), (W, yy - 8),
                        (W, yy + 34), (0, yy + 42)
                    ]
                )

            pygame.draw.ellipse(s, (32, 112, 62), (470, 275, 470, 300))
            pygame.draw.ellipse(s, (185, 220, 190), (470, 275, 470, 300), 2)
            pygame.draw.line(s, (185, 220, 190), (705, 275), (705, 575), 2)
            pygame.draw.circle(s, (185, 220, 190), (705, 425), 48, 2)

            panel = pygame.Rect(55, 72, 405, 485)
            pygame.draw.rect(s, (5, 12, 22), panel.move(0, 7), border_radius=18)
            pygame.draw.rect(s, (13, 25, 40), panel, border_radius=18)
            pygame.draw.rect(s, (192, 157, 66), panel, 2, border_radius=18)

            self.text("CARREIRA", "l", GOLD, (95, 115))
            self.text("DE CRAQUE", "xl", WHITE, (92, 155))
            self.text("SUA HISTORIA NO FUTEBOL", "m", (150, 190, 205), (98, 230))

            pygame.draw.line(s, (75, 96, 112), (98, 270), (415, 270), 1)

            self.text("Comece nas categorias de base,", "n", WHITE, (98, 292))
            self.text("conquiste seu espaco e vire idolo.", "n", WHITE, (98, 318))
            self.text("Cada partida pode mudar sua carreira.", "s", GREY, (98, 354))

            self.b_new.draw(s, self.f["m"], mouse)
            self.b_quit.draw(s, self.f["m"], mouse)

            bob = math.sin(self.t * 0.045) * 5
            px, py = 720, int(330 + bob)

            aacircle(s, (225, 178, 140), (px, py - 100), 22)
            pygame.draw.arc(
                s, (35, 25, 20),
                (px - 22, py - 124, 44, 30),
                math.pi, math.tau, 7
            )

            pygame.draw.polygon(
                s, (28, 88, 195),
                [
                    (px - 24, py - 76),
                    (px + 24, py - 76),
                    (px + 34, py + 5),
                    (px - 34, py + 5)
                ]
            )

            pygame.draw.line(
                s, (225, 178, 140),
                (px - 20, py - 64), (px - 48, py - 5), 11
            )
            pygame.draw.line(
                s, (225, 178, 140),
                (px + 20, py - 64), (px + 48, py - 10), 11
            )
            pygame.draw.line(
                s, (25, 35, 75),
                (px - 12, py + 3), (px - 27, py + 98), 17
            )
            pygame.draw.line(
                s, (25, 35, 75),
                (px + 12, py + 3), (px + 30, py + 98), 17
            )
            pygame.draw.line(
                s, WHITE,
                (px - 27, py + 90), (px - 43, py + 105), 9
            )
            pygame.draw.line(
                s, WHITE,
                (px + 30, py + 90), (px + 46, py + 105), 9
            )

            aacircle(s, WHITE, (px - 72, py + 105), 11)
            pygame.draw.circle(s, DARK, (px - 72, py + 105), 11, 2)

            self.text(
                "DO PRIMEIRO CONTRATO AO ESTRELATO",
                "s", WHITE, (705, 555), True
            )

        elif st == "name":
            gradient(s, (20, 40, 60), (10, 16, 24))
            self.text("CRIE SEU JOGADOR", "l", GOLD, (W // 2, 140), True)
            self.text("Qual e o seu nome?", "m", WHITE, (W // 2, 230), True)

            box = pygame.Rect(W // 2 - 220, 270, 440, 60)
            pygame.draw.rect(s, PANEL, box, border_radius=10)
            pygame.draw.rect(s, GOLD, box, 2, border_radius=10)

            cur = "|" if (self.t // 30) % 2 == 0 else ""
            self.text(p.name + cur, "l", WHITE, box.center, True)
            self.text("Digite e pressione ENTER", "s", GREY, (W // 2, 350), True)
            self.text("Dica: use um nome para começar sua carreira", "s", GREY, (W // 2, 385), True)

            self.b_next.enabled = bool(p.name.strip())
            self.b_next.draw(s, self.f["m"], mouse)

        elif st == "profile":
            gradient(s, (20, 40, 60), (10, 16, 24))
            self.text(p.name.upper(), "l", GOLD, (W // 2, 120), True)
            self.text("Nacionalidade", "m", WHITE, (W // 2, 270), True)

            for b in self.b_nation:
                b.draw(s, self.f["s"], mouse, selected=b.text == p.nation)

            self.text("Posicao", "m", WHITE, (W // 2, 380), True)

            for b in self.b_pos:
                b.draw(s, self.f["n"], mouse, selected=b.text == p.position)

            hint = {
                "Atacante": "+8 Chute",
                "Meia": "+8 Passe",
                "Ponta": "+8 Velocidade"
            }[p.position]

            self.text(
                f"Bonus da posicao: {hint}",
                "n", GREY, (W // 2, 480), True
            )
            self.text(
                f"{p.age} anos  •  {p.nation}",
                "n", GREY, (W // 2, 165), True
            )

            self.b_next.enabled = True
            self.b_next.draw(s, self.f["m"], mouse)

        elif st == "agent":
            gradient(s, (30, 30, 50), (10, 12, 20))

            lines = [
                f"Ola, {p.name.split()[0]}! Eu sou o Marcao, seu novo empresario.",
                f"Vi voce jogando na varzea. Um {p.position.lower()} de {p.age} anos com muito talento!",
                "Nao vai ser facil. Todo craque comeca de baixo... na Serie D.",
                "Consegui algumas propostas. Vamos ver?"
            ]

            self.panel((100, 160, W - 200, 300), "EMPRESARIO")

            aacircle(s, (232, 190, 150), (180, 260), 40)
            aacircle(s, (60, 40, 30), (180, 236), 26)
            aacircle(s, (232, 190, 150), (180, 262), 32)

            pygame.draw.rect(
                s, (40, 40, 60),
                (140, 300, 80, 60),
                border_radius=12
            )

            for i in range(min(self.intro_line + 1, 4)):
                self.text(
                    lines[i],
                    "n",
                    WHITE if i == self.intro_line else GREY,
                    (250, 220 + i * 50)
                )

            self.b_next.draw(s, self.f["m"], mouse)

        elif st == "offers":
            gradient(s, (20, 40, 60), (10, 16, 24))
            self.text("PROPOSTAS DE CONTRATO", "l", GOLD, (W // 2, 110), True)

            for i, o in enumerate(self.offers):
                r = self.panel((120 + i * 260, 170, 240, 320))

                aacircle(
                    s, TEAM_COLORS.get(o["club"], BLUE),
                    (r.centerx, r.y + 60), 34
                )
                aacircle(s, WHITE, (r.centerx, r.y + 60), 20)

                self.text(
                    o["club"][:2].upper(),
                    "m", DARK, (r.centerx, r.y + 60), True
                )
                self.text(o["club"], "m", WHITE, (r.centerx, r.y + 120), True)
                self.text("Liga Nacional", "s", GREY, (r.centerx, r.y + 146), True)
                self.text("Elenco profissional", "s", GREY, (r.centerx, r.y + 166), True)
                self.text(
                    f"Salario: ${o['wage']}/jogo",
                    "n", WHITE, (r.centerx, r.y + 195), True
                )
                self.text(
                    f"Luvas: ${o['bonus']}",
                    "n", GOLD, (r.centerx, r.y + 215), True
                )

                self.b_offer[i].draw(s, self.f["m"], mouse)

            self.b_more_offers.draw(s, self.f["m"], mouse)
            self.text(
                "16 clubes ficticios disponíveis na liga",
                "s", GREY, (W // 2, 590), True
            )

        elif st == "hub":
            self.draw_hub(mouse)

        elif st == "match":
            m = self.match
            m.draw(s, self.f)

            if m.over:
                ov = pygame.Surface((W, H), pygame.SRCALPHA)
                ov.fill((0, 0, 0, 200))
                s.blit(ov, (0, 0))

                res, col = (
                    ("VITORIA!", GREEN)
                    if m.us > m.them
                    else (
                        ("EMPATE", GOLD)
                        if m.us == m.them
                        else ("DERROTA", RED)
                    )
                )

                self.text("FIM DE JOGO", "m", GREY, (W // 2, 70), True)
                self.text(res, "xl", col, (W // 2, 130), True)

                gh, ga = (
                    (m.us, m.them)
                    if m.user_home
                    else (m.them, m.us)
                )

                self.text(
                    f"{m.home}  {gh} - {ga}  {m.away}",
                    "l", WHITE, (W // 2, 200), True
                )

                for i, l in enumerate(m.log[-5:]):
                    self.text(
                        l, "n", GREY,
                        (W // 2, 245 + i * 24), True
                    )

                info = [
                    f"Sua nota: {m.final_rating}",
                    f"Seus gols: {m.my_goals}   Passes: {m.passes}",
                    f"Ganhos: ${m.prize}"
                ]

                for i, l in enumerate(info):
                    self.text(
                        l, "m",
                        GOLD if i == 0 else WHITE,
                        (W // 2, 390 + i * 40),
                        True
                    )

                self.b_cont.draw(s, self.f["m"], mouse)

        elif st == "results":
            gradient(s, (20, 40, 60), (10, 16, 24))
            r = self.panel((40, 30, 400, 540), "RESULTADOS DA RODADA")

            for i, (a, ga, gb, b) in enumerate(self.league.last_results):
                y = r.y + 60 + i * 44
                me = self.p.club in (a, b)

                if me:
                    pygame.draw.rect(
                        s, shade(BLUE_D, 10),
                        (r.x + 10, y - 6, r.w - 20, 36),
                        border_radius=6
                    )

                t = self.f["n"].render(a, True, WHITE)
                s.blit(t, (r.x + 170 - t.get_width(), y))

                self.text(
                    f"{ga} - {gb}",
                    "m", GOLD, (r.centerx, y + 10), True
                )
                self.text(b, "n", WHITE, (r.x + 230, y))

            self.draw_table((460, 30, 520, 540), compact=True)
            self.b_cont.rect.topleft = (W // 2 - 130, 590)
            self.b_cont.draw(s, self.f["m"], mouse)

        elif st == "season":
            gradient(s, (50, 40, 10), (10, 12, 20))
            champ, pos, sg = self.season_summary

            self.text("FIM DE TEMPORADA", "l", GOLD, (W // 2, 140), True)
            self.text(f"Campeao: {champ}", "l", WHITE, (W // 2, 230), True)
            self.text(
                f"{p.club} terminou em {pos}o lugar",
                "m", WHITE, (W // 2, 300), True
            )
            self.text(
                f"Voce marcou {sg} gols na temporada",
                "m", WHITE, (W // 2, 340), True
            )

            if champ == p.club:
                self.text(
                    "CAMPEOES!!! A torcida te idolatra!",
                    "l", GREEN, (W // 2, 420), True
                )

            self.b_cont.rect.topleft = (W // 2 - 130, 520)
            self.b_cont.draw(s, self.f["m"], mouse)

    def draw_hub(self, mouse):
        s, p, L = self.s, self.p, self.league

        gradient(s, (22, 34, 50), (12, 16, 24))
        pygame.draw.rect(s, DARK, (0, 0, W, 78))

        aacircle(s, BLUE, (44, 39), 26)
        self.text(p.overall(), "m", WHITE, (44, 39), True)
        self.text(p.name, "l", WHITE, (82, 8))

        self.text(
            f"{p.position}  •  {p.age} anos  •  {p.nation}  •  {p.club}",
            "n", GREY, (84, 48)
        )

        self.text(f"${p.money}", "l", GOLD, (W - 250, 8))
        self.text(f"Fama {p.fame}", "n", GREY, (W - 250, 48))

        for k, b in self.tabs.items():
            b.draw(s, self.f["n"], mouse, selected=self.tab == k)

        self.b_play.enabled = p.energy >= 20
        self.b_play.draw(s, self.f["m"], mouse)

        if self.tab == "carreira":
            r = self.panel((20, 150, 470, 230), "ATRIBUTOS")

            self.bar(r.x + 20, r.y + 50, "Chute", p.shoot, ORANGE)
            self.bar(r.x + 20, r.y + 85, "Passe", p.pass_, (60, 170, 240))
            self.bar(r.x + 20, r.y + 120, "Velocidade", p.speed, GOLD)
            self.bar(r.x + 20, r.y + 165, "Energia", p.energy, GREEN)

            r = self.panel((20, 395, 470, 190), "RELACIONAMENTOS")

            self.bar(r.x + 20, r.y + 50, "Tecnico", p.coach, (200, 120, 240))
            self.bar(r.x + 20, r.y + 85, "Torcida", p.fans, (240, 90, 120))
            self.bar(r.x + 20, r.y + 120, "Elenco", p.mates, (90, 220, 200))

            r = self.panel((510, 150, 470, 200), "PROXIMO JOGO")
            fx = L.user_fixture(p.club)

            if fx:
                self.text(f"{fx[0]}", "m", WHITE, (r.centerx, r.y + 70), True)
                self.text("x", "n", GREY, (r.centerx, r.y + 100), True)
                self.text(f"{fx[1]}", "m", WHITE, (r.centerx, r.y + 130), True)

                opp = fx[1] if fx[0] == p.club else fx[0]

                self.text(
                    f"Forca do adversario: {L.strength[opp]}",
                    "s", GREY, (r.centerx, r.y + 170), True
                )

            r = self.panel((510, 365, 470, 220), "ESTATISTICAS")
            pos = L.standings().index(p.club) + 1

            for i, l in enumerate([
                f"Posicao na liga: {pos}o",
                f"Jogos: {p.matches}",
                f"Gols na carreira: {p.goals}",
                f"Gols na temporada: {p.season_goals}",
                f"Nota media: {p.avg():.1f}"
            ]):
                self.text(l, "n", WHITE, (r.x + 20, r.y + 50 + i * 30))

        elif self.tab == "tabela":
            self.draw_table((20, 150, W - 40, 440))
            self.text(
                "Verde = lider   Vermelho = zona de rebaixamento",
                "s", GREY, (30, 598)
            )

        elif self.tab == "treino":
            self.panel((20, 150, 480, 430), "TREINAMENTO")

            for b in self.b_train:
                b.draw(s, self.f["n"], mouse)

            r = self.panel((520, 150, 460, 430), "SEU JOGADOR")

            self.bar(r.x + 20, r.y + 60, "Chute", p.shoot, ORANGE, 200)
            self.bar(r.x + 20, r.y + 100, "Passe", p.pass_, (60, 170, 240), 200)
            self.bar(r.x + 20, r.y + 140, "Velocidade", p.speed, GOLD, 200)
            self.bar(r.x + 20, r.y + 200, "Energia", p.energy, GREEN, 200)

            tips = [
                "Chute: forca maxima do chute",
                "Passe: precisao dos toques",
                "Velocidade: defensores demoram",
                "a chegar em voce"
            ]

            for i, l in enumerate(tips):
                self.text(l, "s", GREY, (r.x + 20, r.y + 260 + i * 24))

        elif self.tab == "loja":
            self.panel((20, 150, W - 40, 430), "LOJA")

            for i, (name, price, attr, val) in enumerate(self.shop):
                y = 190 + i * 70

                label = {
                    "shoot": "Chute",
                    "pass_": "Passe",
                    "speed": "Velocidade",
                    "fans": "Torcida",
                    "coach": "Tecnico"
                }[attr]

                self.text(name, "m", WHITE, (50, y + 4))
                self.text(f"+{val} {label}", "n", GREY, (50, y + 28))

                self.b_shop[i].enabled = p.money >= price
                self.b_shop[i].draw(s, self.f["m"], mouse)

        if self.note:
            self.text(self.note, "m", GOLD, (W // 2, 640), True)


if __name__ == "__main__":
    Game().run()