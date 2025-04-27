import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os

CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600
GRID_SIZE = 20

BLOCK_TYPES = [
    ('ノーマル', 'normal'),
    ('アイテム', 'item'),
    ('コイン', 'coin'),
    ('壊れる', 'break'),
    ('敵出現', 'enemy'),
]
OBJ_TYPES = [
    ('地面', 'ground'),
    ('ブロック', 'block'),
    ('コイン', 'coinobj'),
    ('敵', 'enemyobj'),
    ('ゴール', 'goal'),
    ('スタート位置', 'player_start'),
]

class StageEditor:
    def __init__(self, root):
        self.root = root
        self.root.title('ステージエディタ')
        self.mode = tk.StringVar(value='ground')
        self.block_type = tk.StringVar(value='normal')
        self.data = {'ground': [], 'blocks': [], 'coins': [], 'enemies': [], 'goals': [], 'player_start': None}
        self.selected = None
        self.selected_type = None
        self.drag_offset = (0, 0)
        self.filename = None

        # UI
        frame = tk.Frame(root)
        frame.pack(side=tk.TOP, fill=tk.X)
        for label, mode in OBJ_TYPES:
            b = tk.Radiobutton(frame, text=label, variable=self.mode, value=mode)
            b.pack(side=tk.LEFT)
        block_frame = tk.Frame(root)
        block_frame.pack(side=tk.TOP, fill=tk.X)
        tk.Label(block_frame, text='ブロック種別:').pack(side=tk.LEFT)
        for label, btype in BLOCK_TYPES:
            b = tk.Radiobutton(block_frame, text=label, variable=self.block_type, value=btype)
            b.pack(side=tk.LEFT)
        tk.Button(frame, text='新規', command=self.new_stage).pack(side=tk.LEFT)
        tk.Button(frame, text='開く', command=self.open_stage).pack(side=tk.LEFT)
        tk.Button(frame, text='保存', command=self.save_stage).pack(side=tk.LEFT)

        self.canvas = tk.Canvas(root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg='#aeefff')
        self.canvas.pack()
        self.canvas.bind('<Button-1>', self.on_click)
        self.canvas.bind('<Button-3>', self.on_right_click)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)
        self.draw()

    def grid_snap(self, x, y):
        return (x // GRID_SIZE) * GRID_SIZE, (y // GRID_SIZE) * GRID_SIZE

    def find_object(self, x, y):
        # 優先順位: goal, enemy, coin, block, ground
        for g in self.data['goals']:
            if g['x'] <= x <= g['x']+GRID_SIZE*2 and g['y'] <= y <= g['y']+GRID_SIZE*2:
                return g, 'goal'
        for e in self.data['enemies']:
            if e['x'] <= x <= e['x']+GRID_SIZE*2 and e['y'] <= y <= e['y']+GRID_SIZE*2:
                return e, 'enemyobj'
        for c in self.data['coins']:
            cx, cy = c['x'], c['y']
            if (cx-x)**2 + (cy-y)**2 < (GRID_SIZE)**2:
                return c, 'coinobj'
        for b in self.data['blocks']:
            bx, by = b['x'], b['y']
            if bx <= x <= bx+GRID_SIZE*2 and by <= y <= by+GRID_SIZE*2:
                return b, 'block'
        for g in self.data['ground']:
            if g['x'] <= x <= g['x']+g['width'] and g['y'] <= y <= g['y']+g['height']:
                return g, 'ground'
        return None, None

    def rect_of(self, obj, objtype):
        if objtype == 'ground':
            return (obj['x'], obj['y'], obj['x']+obj['width'], obj['y']+obj['height'])
        elif objtype in ['block', 'enemyobj', 'goal']:
            return (obj['x'], obj['y'], obj['x']+GRID_SIZE*2, obj['y']+GRID_SIZE*2)
        elif objtype == 'coinobj':
            return (obj['x']-GRID_SIZE//2, obj['y']-GRID_SIZE//2, obj['x']+GRID_SIZE//2, obj['y']+GRID_SIZE//2)
        return (0,0,0,0)

    def is_overlap(self, rect1, rect2):
        l1, t1, r1, b1 = rect1
        l2, t2, r2, b2 = rect2
        return not (r1 <= l2 or r2 <= l1 or b1 <= t2 or b2 <= t1)

    def get_all_objects(self):
        objs = []
        for g in self.data['ground']:
            objs.append((g, 'ground'))
        for b in self.data['blocks']:
            objs.append((b, 'block'))
        for c in self.data['coins']:
            objs.append((c, 'coinobj'))
        for e in self.data['enemies']:
            objs.append((e, 'enemyobj'))
        for g in self.data['goals']:
            objs.append((g, 'goal'))
        return objs

    def check_overlaps(self):
        objs = self.get_all_objects()
        overlaps = set()
        for i in range(len(objs)):
            for j in range(i+1, len(objs)):
                r1 = self.rect_of(objs[i][0], objs[i][1])
                r2 = self.rect_of(objs[j][0], objs[j][1])
                if self.is_overlap(r1, r2):
                    overlaps.add(id(objs[i][0]))
                    overlaps.add(id(objs[j][0]))
        return overlaps

    def on_click(self, event):
        x, y = self.grid_snap(event.x, event.y)
        m = self.mode.get()
        # まず既存オブジェクトの選択を優先
        obj, objtype = self.find_object(event.x, event.y)
        if obj:
            self.selected = obj
            self.selected_type = objtype
            rx, ry, _, _ = self.rect_of(obj, objtype)
            self.drag_offset = (event.x - rx, event.y - ry)
            self.draw()
            return
        # 空きなら新規配置
        if m == 'ground':
            self.data['ground'].append({'x': x, 'y': y, 'width': GRID_SIZE*4, 'height': GRID_SIZE})
            self.selected = self.data['ground'][-1]
            self.selected_type = 'ground'
            self.drag_offset = (event.x - x, event.y - y)
        elif m == 'block':
            self.data['blocks'].append({'x': x, 'y': y, 'type': self.block_type.get()})
            self.selected = self.data['blocks'][-1]
            self.selected_type = 'block'
            self.drag_offset = (event.x - x, event.y - y)
        elif m == 'coinobj':
            self.data['coins'].append({'x': x+GRID_SIZE//2, 'y': y+GRID_SIZE//2})
            self.selected = self.data['coins'][-1]
            self.selected_type = 'coinobj'
            self.drag_offset = (event.x - (x+GRID_SIZE//2), event.y - (y+GRID_SIZE//2))
        elif m == 'enemyobj':
            self.data['enemies'].append({'x': x, 'y': y})
            self.selected = self.data['enemies'][-1]
            self.selected_type = 'enemyobj'
            self.drag_offset = (event.x - x, event.y - y)
        elif m == 'goal':
            self.data['goals'].append({'x': x, 'y': y})
            self.selected = self.data['goals'][-1]
            self.selected_type = 'goal'
            self.drag_offset = (event.x - x, event.y - y)
        elif m == 'player_start':
            self.data['player_start'] = {'x': x, 'y': y}
            self.selected = self.data['player_start']
            self.selected_type = 'player_start'
            self.drag_offset = (event.x - x, event.y - y)
        self.draw()

    def on_drag(self, event):
        if self.selected:
            x, y = event.x - self.drag_offset[0], event.y - self.drag_offset[1]
            x, y = self.grid_snap(x, y)
            if self.selected_type == 'ground':
                self.selected['x'] = x
                self.selected['y'] = y
            elif self.selected_type in ['block', 'enemyobj', 'goal']:
                self.selected['x'] = x
                self.selected['y'] = y
            elif self.selected_type == 'coinobj':
                self.selected['x'] = x+GRID_SIZE//2
                self.selected['y'] = y+GRID_SIZE//2
            elif self.selected_type == 'player_start':
                self.selected['x'] = x
                self.selected['y'] = y
            self.draw()

    def on_release(self, event):
        self.selected = None
        self.selected_type = None
        self.draw()

    def on_right_click(self, event):
        x, y = event.x, event.y
        obj, objtype = self.find_object(x, y)
        if obj and objtype:
            if objtype == 'ground':
                self.data['ground'].remove(obj)
            elif objtype == 'block':
                self.data['blocks'].remove(obj)
            elif objtype == 'coinobj':
                self.data['coins'].remove(obj)
            elif objtype == 'enemyobj':
                self.data['enemies'].remove(obj)
            elif objtype == 'goal':
                self.data['goals'].remove(obj)
            elif objtype == 'player_start':
                self.data['player_start'] = None
            self.draw()

    def draw(self):
        self.canvas.delete('all')
        overlaps = self.check_overlaps()
        # grid
        for x in range(0, CANVAS_WIDTH, GRID_SIZE):
            self.canvas.create_line(x, 0, x, CANVAS_HEIGHT, fill='#d0f0ff')
        for y in range(0, CANVAS_HEIGHT, GRID_SIZE):
            self.canvas.create_line(0, y, CANVAS_WIDTH, y, fill='#d0f0ff')
        # ground
        for g in self.data['ground']:
            color = '#ff4444' if id(g) in overlaps else '#228B22'
            self.canvas.create_rectangle(g['x'], g['y'], g['x']+g['width'], g['y']+g['height'], fill=color)
        # blocks
        for b in self.data['blocks']:
            color = {
                'normal': '#b8860b',
                'item': '#ffcc00',
                'coin': '#ffee88',
                'break': '#888888',
                'enemy': '#ff8888',
            }.get(b['type'], '#b8860b')
            if id(b) in overlaps:
                color = '#ff4444'
            self.canvas.create_rectangle(b['x'], b['y'], b['x']+GRID_SIZE*2, b['y']+GRID_SIZE*2, fill=color)
            self.canvas.create_text(b['x']+GRID_SIZE, b['y']+GRID_SIZE, text=b['type'], font=('Arial',8))
        # coins
        for c in self.data['coins']:
            color = '#ff4444' if id(c) in overlaps else '#ffd700'
            self.canvas.create_oval(c['x']-GRID_SIZE//2, c['y']-GRID_SIZE//2, c['x']+GRID_SIZE//2, c['y']+GRID_SIZE//2, fill=color)
        # enemies
        for e in self.data['enemies']:
            color = '#ff4444' if id(e) in overlaps else '#ff0000'
            self.canvas.create_rectangle(e['x'], e['y'], e['x']+GRID_SIZE*2, e['y']+GRID_SIZE*2, fill=color)
            self.canvas.create_text(e['x']+GRID_SIZE, e['y']+GRID_SIZE, text='enemy', font=('Arial',8))
        # goals
        for g in self.data['goals']:
            color = '#ff4444' if id(g) in overlaps else '#00ff00'
            self.canvas.create_rectangle(g['x'], g['y'], g['x']+GRID_SIZE*2, g['y']+GRID_SIZE*2, fill=color)
            self.canvas.create_text(g['x']+GRID_SIZE, g['y']+GRID_SIZE, text='goal', font=('Arial',8))
        # player start
        if self.data['player_start']:
            color = '#ff4444' if id(self.data['player_start']) in overlaps else '#0000ff'
            self.canvas.create_rectangle(self.data['player_start']['x']-GRID_SIZE//2, self.data['player_start']['y']-GRID_SIZE//2, self.data['player_start']['x']+GRID_SIZE//2, self.data['player_start']['y']+GRID_SIZE//2, fill=color)
            self.canvas.create_text(self.data['player_start']['x']+GRID_SIZE, self.data['player_start']['y']+GRID_SIZE, text='player start', font=('Arial',8))

    def new_stage(self):
        self.data = {'ground': [], 'blocks': [], 'coins': [], 'enemies': [], 'goals': [], 'player_start': None}
        self.filename = None
        self.draw()

    def open_stage(self):
        fname = filedialog.askopenfilename(defaultextension='.json', filetypes=[('JSON','*.json')], initialdir='assets/stages')
        if fname:
            with open(fname, encoding='utf-8') as f:
                self.data = json.load(f)
            # バックワード互換
            if 'enemies' not in self.data:
                self.data['enemies'] = []
            if 'goals' not in self.data:
                self.data['goals'] = []
            self.filename = fname
            self.draw()

    def save_stage(self):
        overlaps = self.check_overlaps()
        if overlaps:
            messagebox.showerror('エラー', 'オブジェクトが重なっています。重なりを解消してください。')
            return
        if not self.filename:
            fname = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON','*.json')], initialdir='assets/stages')
            if not fname:
                return
            self.filename = fname
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        messagebox.showinfo('保存', '保存しました')

if __name__ == '__main__':
    root = tk.Tk()
    app = StageEditor(root)
    root.mainloop() 