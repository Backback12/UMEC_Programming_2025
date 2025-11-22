import tkinter as tk
import random
import csv 
import time

GRID_W, GRID_H = 200, 200
BG_COLOR = "#ffffff"
ZOOM = 3 

def parse_time_to_seconds(s):
    s = s.strip()
    if not s:
        return 0.0
    try:
        return float(s)
    except ValueError:
        pass

    parts = s.split(":")
    parts = [p.strip() for p in parts]
    if len(parts) == 2:
        m, sec = parts
        return int(m) * 60 + float(sec)
    elif len(parts) == 3:
        h, m, sec = parts
        return int(h) * 3600 + int(m) * 60 + float(sec)
    return 0.0

def load_emergencies_from_csv(path):
    emergencies = []
    try:
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 4:
                    continue

                try:
                    t = float(row[0])      
                except ValueError:
                    continue

                e_type = row[3].strip().lower()  # fire / police / medical

                desc = f"{e_type.capitalize()} emergency"

                emergencies.append({
                    "time": t,
                    "type": e_type,
                })
    except FileNotFoundError:
        print(f"[WARN] CSV file '{path}' not found. No emergencies loaded.")
    except Exception as e:
        print(f"[WARN] Could not read '{path}': {e}")

    emergencies.sort(key=lambda e: e["time"])
    return emergencies

class EmergencyPlayer:

    def __init__(self, root, emergencies, log_func, time_scale=10.0):
        self.root = root
        self.emergencies = emergencies
        self.log = log_func
        self.time_scale = float(time_scale)

        self.running = False
        self.start_real_time = None
        self.next_idx = 0

    def start(self):
        if not self.emergencies:
            self.log("No emergencies loaded. Nothing to simulate.\n")
            return

        # reset and start
        self.running = True
        self.start_real_time = time.time()
        self.next_idx = 0
        self.log("=== Simulation started ===\n")
        self.root.after(100, self._tick)

    def _tick(self):
        if not self.running:
            return

        # elapsed simulation time
        elapsed_real = time.time() - self.start_real_time
        sim_time = elapsed_real * self.time_scale

        # reveal all emergencies that are due
        while (self.next_idx < len(self.emergencies)
               and self.emergencies[self.next_idx]["time"] <= sim_time):
            e = self.emergencies[self.next_idx]
            t_str = format_sim_time(e["time"])
            line = f"[{t_str}] {e['type']}: {e['description']}\n"
            self.log(line)
            self.next_idx += 1

        # check if we are done
        if self.next_idx >= len(self.emergencies):
            self.log("=== Simulation finished ===\n")
            self.running = False
            return

        # keep advancing
        self.root.after(200, self._tick)

def format_sim_time(seconds):
    seconds = int(round(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    else:
        return f"{m:02d}:{s:02d}"

class PixelGrid:
    def __init__(self, master, width=GRID_W, height=GRID_H, zoom=ZOOM, bg=BG_COLOR):
        self.master = master
        self.W = width
        self.H = height
        self.zoom = zoom
        self.bg = bg

        self.pixel_img = tk.PhotoImage(width=self.W, height=self.H)
        self.pixel_img.put(self.bg, to=(0, 0, self.W - 1, self.H - 1))
        self.scaled_img = self.pixel_img.zoom(self.zoom, self.zoom)

        self.label = tk.Label(master, image=self.scaled_img)
        self.label.image = self.scaled_img
        self.label.pack(padx=6, pady=6)

        self.pixels = {}          
        self.next_id = 1

        self.animations = {}       
        self.anim_running = False
        self.anim_delay = 16     

    # low-level drawing
    def redraw_all(self):
        self.pixel_img.put(self.bg, to=(0, 0, self.W - 1, self.H - 1))
        for pid, p in self.pixels.items():
            ix = int(round(p['x']))
            iy = int(round(p['y']))
            if 0 <= ix < self.W and 0 <= iy < self.H:
                self.pixel_img.put(p['color'], to=(ix, iy))
        self.scaled_img = self.pixel_img.zoom(self.zoom, self.zoom)
        self.label.configure(image=self.scaled_img)
        self.label.image = self.scaled_img

    # pixel management
    def add_pixel(self, x, y, color="#ff0000"):
        pid = self.next_id
        self.next_id += 1
        self.pixels[pid] = {'x': float(x), 'y': float(y), 'color': color}
        self.redraw_all()
        return pid

    def remove_pixel(self, pid):
        if pid in self.pixels:
            self.pixels.pop(pid)
            self.animations.pop(pid, None)
            self.redraw_all()
    
    # 6 stations to create 
    # 12 units to dispatch 

    def set_pixel_pos(self, pid, x, y):
        if pid in self.pixels:
            self.pixels[pid]['x'] = float(x)
            self.pixels[pid]['y'] = float(y)
            self.redraw_all()

    def clear_all(self):
        self.pixels.clear()
        self.animations.clear()
        self.redraw_all()

    # animation control - moves pixel smoothly over steps frames
    def move_pixel(self, pid, tx, ty, steps=60, delay_ms=None):
        if pid not in self.pixels:
            return
        if delay_ms is None:
            delay_ms = self.anim_delay
        p = self.pixels[pid]
        sx, sy = p['x'], p['y']
        if steps <= 0:
            self.set_pixel_pos(pid, tx, ty)
            return
        anim = {
            'sx': sx, 'sy': sy, 'tx': float(tx), 'ty': float(ty),
            'steps': int(steps), 'i': 0
        }
        self.animations[pid] = anim
        self.anim_delay = delay_ms
        if not self.anim_running:
            self.anim_running = True
            self.master.after(delay_ms, self._animation_step)

    def _animation_step(self):
        if not self.animations:
            self.anim_running = False
            return
        to_remove = []
        for pid, anim in list(self.animations.items()):
            i = anim['i']
            steps = anim['steps']
            if i >= steps:
                # finalize
                self.pixels[pid]['x'] = anim['tx']
                self.pixels[pid]['y'] = anim['ty']
                to_remove.append(pid)
                continue
            t = (i + 1) / steps
            nx = anim['sx'] + (anim['tx'] - anim['sx']) * t
            ny = anim['sy'] + (anim['ty'] - anim['sy']) * t
            self.pixels[pid]['x'] = nx
            self.pixels[pid]['y'] = ny
            anim['i'] += 1
        for pid in to_remove:
            self.animations.pop(pid, None)
        self.redraw_all()
        if self.animations:
            self.master.after(self.anim_delay, self._animation_step)
        else:
            self.anim_running = False

#update canvas
#TODO: update emergencies (managed or unmanaged, positions), update unit positions, per time step

# MAIN UI
def build_ui(root):
    root.title("PleaseCompile - Dispatcher Simulation")
    frame = tk.Frame(root)
    frame.pack(fill='both', expand=True)

    grid_frame = tk.Frame(frame)
    grid_frame.pack(side='right', padx=8, pady=8)
    
    
    log_frame = tk.Frame(frame)
    log_frame.pack(side='left', fill='both',expand = True, padx=8, pady=8)
    tk.Label(log_frame, text="Event Log", font=("TkDefaultFont", 11, "bold")).pack(anchor='w')

    log_text = tk.Text(log_frame, width=45, height=30, state='disabled')
    log_scroll = tk.Scrollbar(log_frame, command=log_text.yview)
    log_text.configure(yscrollcommand=log_scroll.set)

    log_scroll.pack(side='right', fill='y')
    log_text.pack(side='left', fill='both', expand=True)

    def append_log(msg):
        log_text.configure(state='normal')
        log_text.insert(tk.END, msg)
        log_text.see(tk.END)   # auto-scroll
        log_text.configure(state='disabled')


    pg = PixelGrid(grid_frame)

    stations = [
        (20, 20, "#FF0000"),  # Fire Station 1
        (180, 20, "#700000"),  # Fire Station 2
        (50, 100, "#002FFF"),  # Police Station 1
        (150, 120, "#000000"),  # Police Station 2
        (100, 30, "#000000"),  # Medical Station 1
        (100, 170, "#000000"),  # Medical Station 2
    ]

    for x, y, color in stations:
        pg.add_pixel(x, y, color)

    emergencies = load_emergencies_from_csv("../emergency_events.csv")
    append_log(f"Loaded {len(emergencies)} emergencies from 'emergencies.csv'\n")

    # time_scale: change this if you want the simulation to go faster/slower
    player = EmergencyPlayer(root, emergencies, append_log, time_scale=1000.0)

    # Start button
    start_btn = tk.Button(log_frame, text="Start simulation", command=player.start)
    start_btn.pack(anchor='w', pady=(6, 0))

    return pg, player

if __name__ == "__main__":
    root = tk.Tk()
    build_ui(root)
    root.geometry("900x640")
    root.mainloop()

#MAYBE USEFUL LATER
## ADD PIXEL
# tk.Label(controls, text="Add pixel").pack()
#     add_x = tk.Entry(controls, width=6); add_x.insert(0, "10")
#     add_y = tk.Entry(controls, width=6); add_y.insert(0, "10")
#     add_color = tk.Entry(controls, width=8); add_color.insert(0, "#ff0000")
#     add_x.pack(pady=2); add_y.pack(pady=2); add_color.pack(pady=2)

#     def on_add():
#         try:
#             x = int(add_x.get()); y = int(add_y.get()); c = add_color.get()
#             pid = pg.add_pixel(x, y, c)
#             refresh_list()
#         except Exception:
#             pass
#     tk.Button(controls, text="Add pixel", command=on_add).pack(pady=4)

# def on_remove():
#         sel = listbox.curselection()
#         if not sel:
#             return
#         idx = sel[0]
#         pid = int(listbox.get(idx).split(":")[0])
#         pg.remove_pixel(pid)
#         refresh_list()
#     tk.Button(controls, text="Remove selected", command=on_remove).pack(pady=4)

# def on_clear():
#     pg.clear_all()
#     refresh_list()
# tk.Button(controls, text="Clear all", command=on_clear).pack(pady=6)
