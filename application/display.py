import tkinter as tk
import random
import csv
import time

GRID_W, GRID_H = 200,200
BG_COLOR = "#000000"
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
                x = float(row[1])
                y = float(row[2])
                e_type = row[3].strip().lower()  # fire / police / medical

                desc = f"{e_type.capitalize()} emergency"

                emergencies.append({
                    "time": t,
                    "type": e_type,
                    "x": x,
                    "y": y,
                })

    except FileNotFoundError:
        print(f"[WARN] CSV file '{path}' not found. No emergencies loaded.")
    except Exception as e:
        print(f"[WARN] Could not read '{path}': {e}")

    emergencies.sort(key=lambda e: e["time"])
    return emergencies

def format_sim_time(seconds):
    seconds = int(round(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    else:
        return f"{m:02d}:{s:02d}"

class EmergencyPlayer:

    def __init__(self, root, emergencies, log_func,pixel_grid, time_scale=10.0):
        self.root = root
        self.emergencies = emergencies
        self.log = log_func
        self.pg = pixel_grid
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

        while (self.next_idx < len(self.emergencies)
               and self.emergencies[self.next_idx]["time"] <= sim_time):
            e = self.emergencies[self.next_idx]
            t_str = format_sim_time(e["time"])
            line = f"[{t_str}] {e['type']}\n"
            self.log(line)

            x = e['x']
            y = e['y']
            if e['type'] == 'fire':
                color = "#FF8800"
            elif e['type'] == 'police':
                color = "#00CCFF"
            elif e['type'] == 'medical':
                color = "#FF00E1"
            else:
                color = "#808080"
            pid = self.pg.add_pixel(x, y, color)

            self.next_idx += 1

        if self.next_idx >= len(self.emergencies):
            self.log("=== Simulation finished ===\n")
            self.running = False
            return

        # keep advancing
        self.root.after(200, self._tick)

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

# UI
def build_ui(root):
    root.title("PleaseCompile - Dispatcher Simulation")
    frame = tk.Frame(root)
    frame.pack(fill='both', expand=True)

    title_label = tk.Label(frame, text="Winnipeg Dispatcher Simulation", font=("TkDefaultFont", 16, "bold"))
    title_label.pack(pady=8)

    # Legend frame for stations
    legend_frame = tk.Frame(frame)
    legend_frame.pack()
    tk.Label(legend_frame, text="Legend: ", font=("TkDefaultFont", 11, "bold")).pack(side='left')
    tk.Label(legend_frame, text="■ Fire Station", fg="#FF0000").pack(side='left', padx=8)
    tk.Label(legend_frame, text="■ Police Station", fg="#002FFF").pack(side='left', padx=8)
    tk.Label(legend_frame, text="■ Medical Station", fg="#FFE607").pack(side='left', padx=8)

    #legend for emergencies
    legend_frame2 = tk.Frame(frame)
    legend_frame2.pack()
    tk.Label(legend_frame2, text="Emergencies: ", font=("TkDefaultFont", 11, "bold")).pack(side='left')
    tk.Label(legend_frame2, text="■ Fire Emergency", fg="#FF8800").pack(side='left', padx=8)
    tk.Label(legend_frame2, text="■ Police Emergency", fg="#00CCFF").pack(side='left', padx=8)
    tk.Label(legend_frame2, text="■ Medical Emergency", fg="#FF00E1").pack(side='left', padx=8)

    # Event log
    log_frame = tk.Frame(frame)
    log_frame.pack(side='left', expand=True)

    tk.Label(log_frame, text="Emergencies Happening", font=("TkDefaultFont", 11, "bold")).pack(anchor='w')

    # Text widget + scrollbar as the log
    log_text = tk.Text(log_frame, width=45, height=30, state='disabled')
    log_scroll = tk.Scrollbar(log_frame, command=log_text.yview)
    log_text.configure(yscrollcommand=log_scroll.set)

    log_scroll.pack(side='right', fill='y')
    log_text.pack(side='left', fill='both', expand=True)

    def append_log(msg):
        log_text.configure(state='normal')
        log_text.insert(tk.END, msg)
        log_text.see(tk.END)  
        log_text.configure(state='disabled')

    # Pixel grid
    grid_frame = tk.Frame(frame)
    grid_frame.pack(side='right', padx=8, pady=8)

    pg = PixelGrid(grid_frame)
    tk.Label(grid_frame, text="Winnipeg, MB", font=("TkDefaultFont", 11, "bold")).pack()

    stations = [
        (20, 20, "#FF0000"),   # Fire Station 1
        (180, 20, "#FF0000"),  # Fire Station 2
        (50, 100, "#002FFF"),  # Police Station 1
        (150, 120, "#002FFF"), # Police Station 2
        (100, 30, "#FFE607"),  # Medical Station 1
        (100, 170, "#FFE607"), # Medical Station 2
    ]

    for x, y, color in stations:
        pg.add_pixel(x, y, color)

    emergencies = load_emergencies_from_csv("emergency_events.csv")
    append_log(f"Welcome to the Dispatcher Simulation!\n")
    player = EmergencyPlayer(root, emergencies, append_log,pg, time_scale=1000.0)

    # Start button
    start_btn = tk.Button(text="Start simulation", command=player.start)
    start_btn.pack(side= "left", padx= 300, pady=100)


    return pg, player


if __name__ == "__main__":
    root = tk.Tk()
    build_ui(root)
    root.geometry("900x640")
    root.mainloop()