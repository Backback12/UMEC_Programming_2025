import tensorflow as tf
from tensorflow.keras import layers, models
import pandas as pd
from collections import defaultdict, namedtuple # from demo



FILE_PATH = './emergency_events.csv'


# Unit  = namedtuple('Unit', ['station_id','stype','unit_id','home_x','home_y','speed'])


# Assumptions
# Not going back to station
class Unit:
    def __init__(self, station_id, stype, unit_id, home_x, home_y, speed):
        self.station_id = station_id
        self.stype = stype
        self.unit_id = unit_id
        self.home_x = home_x
        self.home_y = home_y
        self.speed = speed
        
        self.x = self.home_x
        self.y = self.home_y

class Emergency:
    def __init__(self, x, y, etype, prio):
        self.x = x
        self.y = y
        self.etype = etype
        self.prio = prio

def import_data(file_path):
    data = pd.read_csv(file_path)   # import data
    data = data.sort_values(by=['t'])   # sort by time




def get_time_to_emergency(unit, emergency):
    pass


def build_initial_stations():
    stations = []
    #(id, type, x, y, num_units)
    stations.append(('F1','fire', 20,20, 2))
    stations.append(('F2','fire',180,20, 2))
    stations.append(('P1','police', 50,100, 2))
    stations.append(('P2','police',150,120, 2))
    stations.append(('H1','medical', 100,30, 2))
    stations.append(('H2','medical', 100,170,2))
    return stations

def create_units_from_stations(stations, default_speed=1.0):
    units = []
    uid = 0
    for sid, stype, sx, sy, num in stations:
        for k in range(num):
            # units.append(Unit(sid, stype, uid, sx, sy, default_speed))
            
            units.append(Unit(sid, stype, uid, sx, sy, default_speed))
            uid += 1
    return units

def main():
    stations = build_initial_stations()
    units = create_units_from_stations(stations, default_speed=1.0)  # 1 unit/sec