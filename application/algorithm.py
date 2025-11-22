import pandas as pd
import math



FILE_PATH = './emergency_events.csv'
OUTPUT_PATH = './output.csv'

DEFAULT_SPEED = 1   # 1 unit/s
VERBOSE = False




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

        
        self.is_busy = False    # checks if the unit is currently busy traversing
        self.done_busy_time = 0 # shows at what time the unit will be done


        self.target = None  # TARGET EMERGENCY


        # name - F1-0, F1-1
        # used in database
        self.name = str(self.station_id) + "-" + str(self.unit_id)
        

class Emergency:
    def __init__(self, id, x, y, etype, prio, expire_time):
        self.id = id
        self.x = x
        self.y = y
        self.etype = etype
        self.prio = prio
        self.expire_time = expire_time
        self.is_active = True
        
        
        if self.etype == 'fire':
            self.applicable_units = ['fire']
        elif self.etype == 'police':
            self.applicable_units = ['police', 'medical']
        elif self.etype == 'medical':
            self.applicable_units = ['medical', 'fire']
        else:
            self.applicable_units = []




def import_data(file_path):
    data = pd.read_csv(file_path)   # import data
    data = data.sort_values(by=['t'])   # sort by time
    return data


def get_time_to_emergency(unit, emergency):
    return  math.sqrt( math.pow(emergency.y - unit.y, 2) + math.pow(emergency.x - unit.x, 2)) / unit.speed   # v = d / t -> t = d / v


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
    points = 0

    # import data
    data = import_data(FILE_PATH)

    # INITIALIZE STATIONS
    stations = build_initial_stations()
    # INITIALIZE UNITS
    units = create_units_from_stations(stations, DEFAULT_SPEED)
    emergency_stack = []



    # Add units positions to data
    for unit in units:
        
        data[unit.name + "-x"] = None    # create unit x position col
        data[unit.name + "-y"] = None    # create unit y position col
    data['points'] = None
    data['done'] = ''




    last_time = 0

    # for time tick in emergency data:
    for index, row in data.iterrows():
        curr_time = row['t']

        if VERBOSE: print(f"\nNEW TIME TICK = {curr_time}")
        

        
        # ------------------------------------------------------------
        # update all other units
        # ------------------------------------------------------------
        
        for unit in units:

            if unit.is_busy:    # if unit is moving

                if VERBOSE: print(f"Unit done busy time = {unit.done_busy_time}")

                if unit.done_busy_time < curr_time:
                    if VERBOSE: print(f"AAAAA - UNIT AT TARGET! {unit.name}")
                    # unit is at target, should be free again to go to next emergency!
                    unit.x = unit.target.x
                    unit.y = unit.target.y
                    unit.is_busy = False
                    unit.done_busy_time = 0

                    # completed event
                    unit.target.is_active = False # set emergency to non-active
                    data.at[index, 'done'] += str(unit.target.id) + " "
                    if unit.target in emergency_stack:
                        emergency_stack.remove(unit.target)

                    
                    remaining_time = curr_time - unit.target.expire_time    # calculate points
                    points += 1 * int(remaining_time / 60)      # 1 point for every minute remaining
                else:
                    if VERBOSE: print("BBBB")
                    # unit is still moving towards target. Calculate new current distance
                    ratio = (curr_time-last_time) / (get_time_to_emergency(unit, unit.target))
                    if VERBOSE: print(f"curr={curr_time} last={last_time} ratio={ratio} gtoe={get_time_to_emergency(unit, unit.target)}")
                    unit.x = unit.x * ratio 
                    unit.y = unit.y * ratio
            

            # save unit positions to output data
            data.at[index, unit.name + "-x"] = unit.x
            data.at[index, unit.name + "-y"] = unit.y
            
                    

        # ------------------------------------------------------------
        # update all emergencies on stack
        # ------------------------------------------------------------
        
        things_to_pop = []   
        for emerg in emergency_stack:
            if emerg.expire_time < curr_time:
                # emergency has expired. RIP.
                emerg.is_active = False
                points -= 2
                # index = emergency_stack.index(emerg)
                # emergency_stack.pop(0)  # pop first in stack
                things_to_pop.append(emerg)
                data.at[index, 'done'] += str(emerg.id) + " "

        for emr in things_to_pop:   # remove emergencies after iterating
            emergency_stack.remove(emr)

        # ------------------------------------------------------------
        # NEW EMERGENCY
        # ------------------------------------------------------------
        # NEW EMERGENCY. basic Greedy algo
        # find closest unit to emergency
        

        emergency = Emergency(id=row['id'],
                            x=row['x'], 
                            y=row['y'], 
                            etype=row['etype'], 
                            prio=row['priority_s'],
                            expire_time=curr_time + row['priority_s'])

        emergency_stack.append(emergency)
        if VERBOSE: print(f"New emergency! At {curr_time}") 
        
        # Find closest applicable unit to emergency
        best_unit = None
        lowest_cost = float('inf')
        for unit in units:
            
            if unit.is_busy:    # unit is currently busy going to another emergency.    - COULD BE OPTIMIZED INCASE UNIT IS STILL CLOSEST?? ***********************************************************
                continue


            if unit.stype in emergency.applicable_units:    # unit is applicable to go
                # compare each applicable unit and send the lowest cost
                curr_cost = get_time_to_emergency(unit, emergency)
                
                if curr_cost > emergency.expire_time:
                    # Unit cannot make it to the emergency in time
                    continue

                if curr_cost < lowest_cost:
                    # unit can make it to the emergency in time
                    lowest_cost = curr_cost
                    best_unit = unit


        if best_unit:
            # set best unit to head to emergency
            best_unit.is_busy = True
            best_unit.done_busy_time = curr_time + get_time_to_emergency(best_unit, emergency)
            best_unit.target = emergency



        # loop updates
        data.at[index, 'points'] = points
        last_time = curr_time

    # return data

    print(f"Simulation complete! Saved position log to {OUTPUT_PATH}")
    data.to_csv(OUTPUT_PATH)



if __name__ == "__main__":
    main()
