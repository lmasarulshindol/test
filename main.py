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
font = pygame.font.SysFont("meiryo", 80)
small_font = pygame.font.SysFont("meiryo", 40)

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
        self.vy = 0
        self.on_ground = False
    def update(self):
        gravity = 0.5
        # 1. on_ground判定
        enemy_rect = pygame.Rect(self.x, self.y + 1, self.width, self.height)
        on_ground_now = False
        for ground in grounds:
            if enemy_rect.colliderect(ground):
                on_ground_now = True
        for block in blocks:
            if enemy_rect.colliderect(block.rect()):
                on_ground_now = True
        self.on_ground = on_ground_now

        # 2. 重力
        if not self.on_ground:
            self.vy += gravity
        else:
            self.vy = 0

        # 3. Y方向移動・当たり判定
        self.y += self.vy
        enemy_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        on_ground_now = False
        for block in blocks:
            block_rect = block.rect()
            if enemy_rect.colliderect(block_rect):
                if self.vy > 0 and self.y + self.height - self.vy <= block_rect.top:
                    self.y = block_rect.top - self.height
                    self.vy = 0
                    on_ground_now = True
                    enemy_rect = pygame.Rect(self.x, self.y, self.width, self.height)
                elif self.vy < 0 and self.y - self.vy >= block_rect.bottom:
                    self.y = block_rect.bottom
                    self.vy = 0
                    enemy_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        for ground in grounds:
            if enemy_rect.colliderect(ground):
                if self.vy > 0 and self.y + self.height - self.vy <= ground.top:
                    self.y = ground.top - self.height
                    self.vy = 0
                    on_ground_now = True
                    enemy_rect = pygame.Rect(self.x, self.y, self.width, self.height)
                elif self.vy < 0 and self.y - self.vy >= ground.bottom:
                    self.y = ground.bottom
                    self.vy = 0
                    enemy_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.on_ground = on_ground_now

        # 4. X方向移動・当たり判定
        self.x += self.vx
        enemy_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        for block in blocks:
            block_rect = block.rect()
            if enemy_rect.colliderect(block_rect):
                if self.vx > 0:
                    self.x = block_rect.left - self.width
                    self.vx *= -1
                elif self.vx < 0:
                    self.x = block_rect.right
                    self.vx *= -1
                enemy_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        for ground in grounds:
            if enemy_rect.colliderect(ground):
                if self.vx > 0:
                    self.x = ground.left - self.width
                    self.vx *= -1
                elif self.vx < 0:
                    self.x = ground.right
                    self.vx *= -1
                enemy_rect = pygame.Rect(self.x, self.y, self.width, self.height)

        # 5. トゲとの当たり判定
        for spike in spikes:
            if enemy_rect.colliderect(spike.rect()):
                # enemiesリストから自分を消す
                if self in enemies:
                    enemies.remove(self)
                break
    def draw(self, surface):
        pygame.draw.rect(surface, (255, 0, 0), (self.x, self.y, self.width, self.height))
    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

# Spike（トゲ）クラス追加
class Spike:
    def __init__(self, x, y, width=40, height=20):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    def draw(self, surface):
        pygame.draw.polygon(surface, (200,200,200), [
            (self.x, self.y+self.height),
            (self.x+self.width//2, self.y),
            (self.x+self.width, self.y+self.height)
        ])
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
        self.invincible_timer = 0
    def update(self, keys):
        speed = 5
        gravity = 0.5
        jump_power = 12
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
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
        # 1. まず on_ground を判定
        player_rect = pygame.Rect(self.x, self.y + 1, self.width, self.height)  # 1ピクセル下で判定
        on_ground_now = False
        for ground in grounds:
            if player_rect.colliderect(ground):
                on_ground_now = True
        for block in blocks:
            if player_rect.colliderect(block.rect()):
                on_ground_now = True
        self.on_ground = on_ground_now

        # 2. 重力やジャンプの処理
        if not self.on_ground:
            self.vy += gravity
        else:
            self.vy = 0
            # ジャンプ入力があればここでジャンプ
            if (keys[pygame.K_SPACE] or keys[pygame.K_w]):
                self.vy = -jump_power
                self.on_ground = False

        # 3. Y方向の移動・当たり判定
        self.y += self.vy
        player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        on_ground_now = False
        # ブロックとのY方向当たり判定
        for block in blocks:
            block_rect = block.rect()
            if player_rect.colliderect(block_rect):
                if self.vy > 0 and self.y + self.height - self.vy <= block_rect.top:
                    self.y = block_rect.top - self.height
                    self.vy = 0
                    on_ground_now = True
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
                    on_ground_now = True
                    player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
                elif self.vy < 0 and self.y - self.vy >= ground.bottom:
                    self.y = ground.bottom
                    self.vy = 0
                    player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.on_ground = on_ground_now
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
                if self.invincible_timer == 0:
                    self.take_damage()
        # トゲとの当たり判定
        for spike in spikes:
            if player_rect.colliderect(spike.rect()):
                if self.invincible_timer == 0:
                    self.take_damage()
        # コイン取得
        for coin in coins:
            if not coin.collected and player_rect.colliderect(coin.rect()):
                coin.collected = True
        if self.y > HEIGHT:
            global game_state, dead_menu_idx
            game_state = STATE_DEAD
            dead_menu_idx = 0
    def take_damage(self):
        if self.powered_up:
            self.powered_up = False
            self.width = 20
            self.height = 20
            self.invincible_timer = 60  # 無敵時間
        else:
            self.respawn()
    def respawn(self):
        self.x = WIDTH//2 - 10
        self.y = HEIGHT - 200
        self.vx = 0
        self.vy = 0
        self.width = 20
        self.height = 20
        self.powered_up = False
        self.invincible_timer = 60
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
# ポーズ状態を追加
STATE_PAUSE = 4
STATE_DEAD = 5

game_state = STATE_TITLE
player = Player(0, 0)

# BGM状態
bgm_on = True

enemies = []
goals = []
spikes = []

# ポーズメニュー選択肢
pause_menu_items = ['ゲームに戻る', '設定画面へ', 'タイトル画面へ']
pause_menu_idx = 0

# 死亡メニュー項目
dead_menu_items = ['リトライ', 'タイトルへ']
dead_menu_idx = 0

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
    # トゲ
    for spike in spikes:
        spike.draw(screen)
    # ゴール
    for goal in goals:
        pygame.draw.rect(screen, (0,255,0), pygame.Rect(goal['x'], goal['y'], 40, 40))
        txt = small_font.render('GOAL', True, (0,0,0))
        screen.blit(txt, (goal['x'], goal['y']-20))
    # プレイヤー
    player.draw(screen)
    # --- デバッグ表示 ---
    debug_text = small_font.render(f'on_ground: {player.on_ground}', True, (255,0,0))
    screen.blit(debug_text, (10, 10))
    pygame.display.flip()

def draw_clear_screen():
    screen.fill((0,0,0))
    clear_text = font.render('CLEAR!!', True, (255,255,0))
    screen.blit(clear_text, (WIDTH//2 - clear_text.get_width()//2, HEIGHT//2 - 40))
    info_text = small_font.render('Enterキーでタイトルへ', True, (255,255,255))
    screen.blit(info_text, (WIDTH//2 - info_text.get_width()//2, HEIGHT//2 + 40))
    pygame.display.flip()

def draw_pause_menu():
    screen.fill((30, 30, 30))
    title = font.render('ポーズ', True, (255,255,255))
    screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//3))
    global pause_menu_rects
    pause_menu_rects = []
    for i, item in enumerate(pause_menu_items):
        color = (255,255,0) if i == pause_menu_idx else (255,255,255)
        txt = small_font.render(item, True, color)
        x = WIDTH//2 - txt.get_width()//2
        y = HEIGHT//2 + i*50
        screen.blit(txt, (x, y))
        pause_menu_rects.append(pygame.Rect(x, y, txt.get_width(), txt.get_height()))
    pygame.display.flip()

def draw_dead_menu():
    screen.fill((30, 0, 0))
    title = font.render('GAME OVER', True, (255, 0, 0))
    screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//3))
    global dead_menu_rects
    dead_menu_rects = []
    for i, item in enumerate(dead_menu_items):
        color = (255,255,0) if i == dead_menu_idx else (255,255,255)
        txt = small_font.render(item, True, color)
        x = WIDTH//2 - txt.get_width()//2
        y = HEIGHT//2 + i*50
        screen.blit(txt, (x, y))
        dead_menu_rects.append(pygame.Rect(x, y, txt.get_width(), txt.get_height()))
    pygame.display.flip()

def main():
    global game_state, bgm_on, selected_stage_idx, current_stage_file, stage_files, enemies, goals, spikes, pause_menu_idx, dead_menu_idx
    clock = pygame.time.Clock()
    while True:
        if game_state == STATE_TITLE:
            draw_title_screen()
        elif game_state == STATE_PLAY:
            keys = pygame.key.get_pressed()
            for enemy in enemies:
                enemy.update()
            dummy_keys = pygame.key.get_pressed()
            player.update(dummy_keys)
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
        elif game_state == STATE_PAUSE:
            draw_pause_menu()
        elif game_state == STATE_DEAD:
            draw_dead_menu()
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
            elif game_state == STATE_PLAY:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        game_state = STATE_PAUSE
                        pause_menu_idx = 0
            elif game_state == STATE_PAUSE:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        pause_menu_idx = (pause_menu_idx - 1) % len(pause_menu_items)
                    elif event.key == pygame.K_DOWN:
                        pause_menu_idx = (pause_menu_idx + 1) % len(pause_menu_items)
                    elif event.key == pygame.K_RETURN:
                        if pause_menu_idx == 0:
                            game_state = STATE_PLAY
                        elif pause_menu_idx == 1:
                            game_state = STATE_OPTION
                        elif pause_menu_idx == 2:
                            game_state = STATE_TITLE
                    elif event.key == pygame.K_ESCAPE:
                        game_state = STATE_PLAY
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    for i, rect in enumerate(pause_menu_rects):
                        if rect.collidepoint(mx, my):
                            pause_menu_idx = i
                            # クリックで即決定
                            if pause_menu_idx == 0:
                                game_state = STATE_PLAY
                            elif pause_menu_idx == 1:
                                game_state = STATE_OPTION
                            elif pause_menu_idx == 2:
                                game_state = STATE_TITLE
                            break
            elif game_state == STATE_DEAD:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        dead_menu_idx = (dead_menu_idx - 1) % len(dead_menu_items)
                    elif event.key == pygame.K_DOWN:
                        dead_menu_idx = (dead_menu_idx + 1) % len(dead_menu_items)
                    elif event.key == pygame.K_RETURN:
                        if dead_menu_idx == 0:
                            # リトライ
                            load_stage(current_stage_file)
                            game_state = STATE_PLAY
                        elif dead_menu_idx == 1:
                            game_state = STATE_TITLE
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    for i, rect in enumerate(dead_menu_rects):
                        if rect.collidepoint(mx, my):
                            dead_menu_idx = i
                            if dead_menu_idx == 0:
                                load_stage(current_stage_file)
                                game_state = STATE_PLAY
                            elif dead_menu_idx == 1:
                                game_state = STATE_TITLE
                            break
            if game_state == STATE_OPTION and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # ポーズから来た場合はポーズに戻る、そうでなければタイトルへ
                    game_state = STATE_PAUSE if 'pause_menu_idx' in globals() and game_state != STATE_TITLE else STATE_TITLE
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
    global grounds, blocks, coins, enemies, goals, spikes
    with open(filename, encoding='utf-8') as f:
        data = json.load(f)
    grounds = [pygame.Rect(g['x'], g['y'], g['width'], g['height']) for g in data.get('ground',[])]
    blocks = [Block(b['x'], b['y'], b.get('width',40), b.get('height',40), b.get('type','normal')) for b in data.get('blocks',[])]
    coins = [Coin(c['x'], c['y']) for c in data.get('coins',[])]
    enemies = [Enemy(e['x'], e['y']) for e in data.get('enemies',[])]
    goals = data.get('goals',[])
    spikes = [Spike(s['x'], s['y'], s.get('width',40), s.get('height',20)) for s in data.get('spikes',[])]
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
        player.vy = 0
        dummy_keys = pygame.key.get_pressed()
        player.update(dummy_keys)
    else:
        player.x = WIDTH//2 - 10
        player.y = HEIGHT - 200

if __name__ == '__main__':
    main() 