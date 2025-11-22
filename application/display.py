import tkinter as tk
import random

GRID_W, GRID_H = 200, 200
BG_COLOR = "#ffffff"
ZOOM = 3 

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
    controls = tk.Frame(frame)
    controls.pack(side='left', fill='y', padx=8, pady=8)
 
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

    # Controls
    tk.Label(controls, text="Add pixel").pack()
    add_x = tk.Entry(controls, width=6); add_x.insert(0, "10")
    add_y = tk.Entry(controls, width=6); add_y.insert(0, "10")
    add_color = tk.Entry(controls, width=8); add_color.insert(0, "#ff0000")
    add_x.pack(pady=2); add_y.pack(pady=2); add_color.pack(pady=2)

    def on_add():
        try:
            x = int(add_x.get()); y = int(add_y.get()); c = add_color.get()
            pid = pg.add_pixel(x, y, c)
            refresh_list()
        except Exception:
            pass
    tk.Button(controls, text="Add pixel", command=on_add).pack(pady=4)

    tk.Label(controls, text="Pixels (id: x,y)").pack(pady=(10,0))
    listbox = tk.Listbox(controls, width=18, height=10)
    listbox.pack()

    def refresh_list():
        listbox.delete(0, tk.END)
        for pid, p in sorted(pg.pixels.items()):
            listbox.insert(tk.END, f"{pid}: {int(round(p['x']))},{int(round(p['y']))}")
    refresh_list()

    # Move controls
    tk.Label(controls, text="Move selected").pack(pady=(10,0))
    tx_e = tk.Entry(controls, width=6); tx_e.insert(0, "180")
    ty_e = tk.Entry(controls, width=6); ty_e.insert(0, "180")
    steps_e = tk.Entry(controls, width=6); steps_e.insert(0, "80")
    tx_e.pack(pady=2); ty_e.pack(pady=2); steps_e.pack(pady=2)

    def on_move():
        sel = listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        item = listbox.get(idx)
        pid = int(item.split(":")[0])
        try:
            tx = int(tx_e.get()); ty = int(ty_e.get()); steps = int(steps_e.get())
            pg.move_pixel(pid, tx, ty, steps=steps)
        except Exception:
            pass
    tk.Button(controls, text="Move", command=on_move).pack(pady=4)

    def on_remove():
        sel = listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        pid = int(listbox.get(idx).split(":")[0])
        pg.remove_pixel(pid)
        refresh_list()
    tk.Button(controls, text="Remove selected", command=on_remove).pack(pady=4)

    def on_clear():
        pg.clear_all()
        refresh_list()
    tk.Button(controls, text="Clear all", command=on_clear).pack(pady=6)

    # update list periodically (to show moving coords)
    def periodic_refresh():
        refresh_list()
        root.after(200, periodic_refresh)
    periodic_refresh()

    return pg

if __name__ == "__main__":
    root = tk.Tk()
    build_ui(root)
    root.geometry("900x640")
    root.mainloop()