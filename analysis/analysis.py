import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
from mpl_toolkits.mplot3d import Axes3D
import numpy as np


# FILE_PATH = './emergency_events.csv'
FILE_PATH = 'C:/Users/cepag/Documents/School/Competitions/UMEC_Programming_2025/analysis/emergency_events.csv'



RADIUS = 5
PRIO_FACTOR = 0.05
ALPHA = 0.2

def plot2d():
    fig, ax = plt.subplots(figsize=(6, 6))

    data = pd.read_csv(FILE_PATH)   # import data
    # data = data.sort_values(by=['t'])   # sort by time

    for index, row in data.iterrows():
        etype = row['etype']
        x = row['x']
        y = row['y']
        prio = row['priority_s']
        
        if etype == 'fire':
            col = 'red'
        elif etype == 'police':
            col = 'blue'
        else:
            col = 'yellow'
        
        circle = patches.Circle((x, y), radius=RADIUS + PRIO_FACTOR * prio, alpha=ALPHA, facecolor=col, edgecolor=None, linewidth=2)
        ax.add_patch(circle)


    ax.set_xlim(0, 200)
    ax.set_ylim(0, 200)

    ax.set_title('Emergencies Heatmap')
    ax.legend()

    plt.show()

def plot3d(ttype):
    data = pd.read_csv(FILE_PATH)   # import data
    sigma = 10

    x = np.linspace(0, 200, 200)
    y = np.linspace(0, 200, 200)
    X, Y = np.meshgrid(x, y)

    Z = np.zeros_like(X)

    
    col = 'Blues'
    for index, row in data.iterrows():
        etype = row['etype']
        x = row['x']
        y = row['y']
        prio = row['priority_s']
        
        if etype != ttype.lower():
            continue
        
        if etype == 'fire': 
            col = 'Reds'
        elif etype == 'police':
            col = 'Blues'
        else:
            col = 'Oranges'
        # circle = patches.Circle((x, y), radius=RADIUS + PRIO_FACTOR * prio, alpha=ALPHA, facecolor=col, edgecolor=None, linewidth=2)
        # ax.add_patch(circle)
        Z += np.exp(-((X - x)**2 + (Y - y)**2) / (2 * sigma**2))#gaussian distribution

    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')

    ax.plot_surface(X, Y, Z, cmap=col, rstride=1, cstride=1, linewidth=0, antialiased=True)

    ax.set_title(f"City {ttype} Emergency Distribution")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")

    plt.show()

plot3d('Fire')
plot3d('Police')
plot3d('Medical')
# plot2d()
