import pygame
import sys
import os
import json

# 初期化
pygame.init()

# 画面サイズ
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Super Python Bros')

# フォント
font = pygame.font.SysFont(None, 80)
small_font = pygame.font.SysFont(None, 40)

# 色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 200, 0)

# 画像とBGMのパス
PLAYER_IMG_PATH = os.path.join('assets', 'images', 'player.png')
BGM_PATH = os.path.join('assets', 'sounds', 'bgm.mp3')

# キャラクター画像の読み込み
try:
    player_img = pygame.image.load(PLAYER_IMG_PATH)
    player_img = pygame.transform.scale(player_img, (100, 100))
except Exception:
    player_img = None

# BGMの再生
try:
    pygame.mixer.music.load(BGM_PATH)
    pygame.mixer.music.play(-1)
except Exception:
    pass

# Coinクラス
class Coin:
    def __init__(self, x, y, radius=10):
        self.x = x
        self.y = y
        self.radius = radius
        self.collected = False
    def draw(self, surface):
        if not self.collected:
            pygame.draw.circle(surface, (255, 215, 0), (self.x, self.y), self.radius)
    def rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius*2, self.radius*2)

# Blockクラス修正
class Block:
    def __init__(self, x, y, width=40, height=40, type="normal"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.type = type
    def draw(self, surface):
        color = (150, 75, 0) if self.type == "item" else (200, 200, 0) if self.type == "coin" else (150, 75, 0)
        pygame.draw.rect(surface, color, (self.x, self.y, self.width, self.height))
    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

# 敵キャラクタークラス
class Enemy:
    def __init__(self, x, y, width=20, height=20):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.vx = 2
    def update(self):
        self.x += self.vx
        if self.x < 0 or self.x + self.width > WIDTH:
            self.vx *= -1
    def draw(self, surface):
        pygame.draw.rect(surface, (255, 0, 0), (self.x, self.y, self.width, self.height))
    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

# ステージファイル一覧取得
STAGE_DIR = os.path.join('assets', 'stages')
def get_stage_files():
    return [f for f in os.listdir(STAGE_DIR) if f.endswith('.json')]

selected_stage_idx = 0
stage_files = get_stage_files()
current_stage_file = os.path.join(STAGE_DIR, stage_files[selected_stage_idx]) if stage_files else None

# プレイヤークラス
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.width = 20
        self.height = 20
        self.on_ground = False
        self.img = player_img
        self.is_crouching = False
        self.powered_up = False
    def update(self, keys):
        speed = 5
        gravity = 0.5
        jump_power = 12
        # パワーアップ切り替え（デモ用：PキーでON/OFF）
        if keys[pygame.K_p]:
            if not self.powered_up:
                self.width = 40
                self.height = 20
                self.powered_up = True
        else:
            if self.powered_up:
                self.width = 20
                self.height = 20
                self.powered_up = False
        # 左右移動
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vx = -speed
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx = speed
        else:
            self.vx = 0
        # ジャンプ
        if (keys[pygame.K_SPACE] or keys[pygame.K_w]) and self.on_ground:
            self.vy = -jump_power
            self.on_ground = False
        # しゃがみ
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            if not self.is_crouching:
                self.y += self.height // 2
                self.height = self.height // 2
                self.is_crouching = True
        else:
            if self.is_crouching:
                self.y -= self.height
                self.height = 20 if not self.powered_up else 20
                self.is_crouching = False
        # 重力
        self.vy += gravity
        # --- Y方向の移動と当たり判定 ---
        self.y += self.vy
        self.on_ground = False
        player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        # ブロックとのY方向当たり判定
        for block in blocks:
            block_rect = block.rect()
            if player_rect.colliderect(block_rect):
                if self.vy > 0 and self.y + self.height - self.vy <= block_rect.top:
                    self.y = block_rect.top - self.height
                    self.vy = 0
                    self.on_ground = True
                    player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
                elif self.vy < 0 and self.y - self.vy >= block_rect.bottom:
                    self.y = block_rect.bottom
                    self.vy = 0
                    player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        # 地面とのY方向当たり判定
        for ground in grounds:
            if player_rect.colliderect(ground):
                if self.vy > 0 and self.y + self.height - self.vy <= ground.top:
                    self.y = ground.top - self.height
                    self.vy = 0
                    self.on_ground = True
                    player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
                elif self.vy < 0 and self.y - self.vy >= ground.bottom:
                    self.y = ground.bottom
                    self.vy = 0
                    player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        # --- X方向の移動と当たり判定 ---
        self.x += self.vx
        player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        for block in blocks:
            block_rect = block.rect()
            if player_rect.colliderect(block_rect):
                if self.vx > 0:
                    self.x = block_rect.left - self.width
                elif self.vx < 0:
                    self.x = block_rect.right
                player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        for ground in grounds:
            if player_rect.colliderect(ground):
                if self.vx > 0:
                    self.x = ground.left - self.width
                elif self.vx < 0:
                    self.x = ground.right
                player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        # 敵との当たり判定
        for enemy in enemies:
            if player_rect.colliderect(enemy.rect()):
                self.respawn()
        # コイン取得
        for coin in coins:
            if not coin.collected and player_rect.colliderect(coin.rect()):
                coin.collected = True
    def respawn(self):
        self.x = WIDTH//2 - 10
        self.y = HEIGHT - 200
        self.vx = 0
        self.vy = 0
        self.width = 20
        self.height = 20
        self.powered_up = False
    def draw(self, surface):
        if self.img:
            img = pygame.transform.scale(self.img, (self.width, self.height))
            surface.blit(img, (self.x, self.y))
        else:
            pygame.draw.rect(surface, WHITE, (self.x, self.y, self.width, self.height))

# ゲーム状態
STATE_TITLE = 0
STATE_PLAY = 1
STATE_OPTION = 2
STATE_CLEAR = 3

game_state = STATE_TITLE
player = Player(0, 0)

# BGM状態
bgm_on = True

enemies = []
goals = []

def draw_title_screen():
    screen.fill(BLACK)
    title_text = font.render('Super Python Bros', True, WHITE)
    press_text = small_font.render('Enterキーでスタート', True, WHITE)
    stage_text = small_font.render('ステージ選択: ', True, WHITE)
    screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, HEIGHT//3))
    screen.blit(press_text, (WIDTH//2 - press_text.get_width()//2, HEIGHT//2))
    screen.blit(stage_text, (WIDTH//2 - stage_text.get_width()//2, HEIGHT//2 + 50))
    # ステージファイルリスト表示
    for i, fname in enumerate(stage_files):
        color = (255,255,0) if i == selected_stage_idx else WHITE
        txt = small_font.render(fname, True, color)
        screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 + 90 + i*30))
    if player_img:
        screen.blit(player_img, (WIDTH//2 - player_img.get_width()//2, HEIGHT//2 + 100 + len(stage_files)*30))
    pygame.display.flip()

def draw_option_screen():
    screen.fill((30, 30, 60))
    option_title = font.render('設定', True, WHITE)
    bgm_status = 'ON' if bgm_on else 'OFF'
    bgm_text = small_font.render(f'BGM: {bgm_status}（Bキーで切替）', True, WHITE)
    back_text = small_font.render('ESCキーで戻る', True, WHITE)
    screen.blit(option_title, (WIDTH//2 - option_title.get_width()//2, HEIGHT//3))
    screen.blit(bgm_text, (WIDTH//2 - bgm_text.get_width()//2, HEIGHT//2))
    screen.blit(back_text, (WIDTH//2 - back_text.get_width()//2, HEIGHT//2 + 50))
    pygame.display.flip()

def draw_play_screen():
    screen.fill((100, 180, 255))  # 空色
    # 地面
    for ground in grounds:
        pygame.draw.rect(screen, GREEN, ground)
    # ブロック
    for block in blocks:
        block.draw(screen)
    # 敵
    for enemy in enemies:
        enemy.draw(screen)
    # コイン
    for coin in coins:
        coin.draw(screen)
    # ゴール
    for goal in goals:
        pygame.draw.rect(screen, (0,255,0), pygame.Rect(goal['x'], goal['y'], 40, 40))
        txt = small_font.render('GOAL', True, (0,0,0))
        screen.blit(txt, (goal['x'], goal['y']-20))
    # プレイヤー
    player.draw(screen)
    pygame.display.flip()

def draw_clear_screen():
    screen.fill((0,0,0))
    clear_text = font.render('CLEAR!!', True, (255,255,0))
    screen.blit(clear_text, (WIDTH//2 - clear_text.get_width()//2, HEIGHT//2 - 40))
    info_text = small_font.render('Enterキーでタイトルへ', True, (255,255,255))
    screen.blit(info_text, (WIDTH//2 - info_text.get_width()//2, HEIGHT//2 + 40))
    pygame.display.flip()

def main():
    global game_state, bgm_on, selected_stage_idx, current_stage_file, stage_files, enemies, goals
    clock = pygame.time.Clock()
    while True:
        if game_state == STATE_TITLE:
            draw_title_screen()
        elif game_state == STATE_PLAY:
            keys = pygame.key.get_pressed()
            for enemy in enemies:
                enemy.update()
            player.update(keys)
            # ゴール判定
            player_rect = pygame.Rect(player.x, player.y, player.width, player.height)
            for goal in goals:
                goal_rect = pygame.Rect(goal['x'], goal['y'], 40, 40)
                if player_rect.colliderect(goal_rect):
                    game_state = STATE_CLEAR
            draw_play_screen()
        elif game_state == STATE_OPTION:
            draw_option_screen()
        elif game_state == STATE_CLEAR:
            draw_clear_screen()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if game_state == STATE_TITLE:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if stage_files:
                            current_stage_file = os.path.join(STAGE_DIR, stage_files[selected_stage_idx])
                            load_stage(current_stage_file)
                            game_state = STATE_PLAY
                    elif event.key == pygame.K_UP:
                        selected_stage_idx = (selected_stage_idx - 1) % len(stage_files)
                    elif event.key == pygame.K_DOWN:
                        selected_stage_idx = (selected_stage_idx + 1) % len(stage_files)
                    stage_files = get_stage_files()
            if game_state == STATE_OPTION and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game_state = STATE_TITLE
                if event.key == pygame.K_b:
                    bgm_on = not bgm_on
                    if bgm_on:
                        try:
                            pygame.mixer.music.play(-1)
                        except Exception:
                            pass
                    else:
                        pygame.mixer.music.stop()
            if game_state == STATE_CLEAR and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    game_state = STATE_TITLE
        clock.tick(60)

def load_stage(filename):
    global grounds, blocks, coins, enemies, goals
    with open(filename, encoding='utf-8') as f:
        data = json.load(f)
    grounds = [pygame.Rect(g['x'], g['y'], g['width'], g['height']) for g in data.get('ground',[])]
    blocks = [Block(b['x'], b['y'], b.get('width',40), b.get('height',40), b.get('type','normal')) for b in data.get('blocks',[])]
    coins = [Coin(c['x'], c['y']) for c in data.get('coins',[])]
    enemies = [Enemy(e['x'], e['y']) for e in data.get('enemies',[])]
    goals = data.get('goals',[])
    # プレイヤースタート位置
    if 'player_start' in data and data['player_start']:
        player.x = data['player_start']['x']
        player.y = data['player_start']['y']
        # 地面やブロックの上に自動で乗せる
        player_rect = pygame.Rect(player.x, player.y, player.width, player.height)
        min_dy = None
        for ground in grounds:
            if player_rect.colliderect(ground):
                dy = ground.top - (player.y + player.height)
                if min_dy is None or abs(dy) < abs(min_dy):
                    min_dy = dy
        for block in blocks:
            block_rect = block.rect()
            if player_rect.colliderect(block_rect):
                dy = block_rect.top - (player.y + player.height)
                if min_dy is None or abs(dy) < abs(min_dy):
                    min_dy = dy
        if min_dy is not None:
            player.y += min_dy
    else:
        player.x = WIDTH//2 - 10
        player.y = HEIGHT - 200

if __name__ == '__main__':
    main() 