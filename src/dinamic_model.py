class DynamicClass:
    def __init__(self):
        self.altitude = None  # float Range: [0, 1000.0]
        self.target_distance = None  # float Range: [0.0, 10000.0]
        self.origin_distance = None  # float Range: [0.0, 10000.0]
        self.battery = None  # float Range: [0.0, 100.0]
        self.obstacle = None  # boolean Range: [False, True]
        self.armed = None  # boolean Range: [False, True]
        self.bad_connection = None  # boolean Range: [False, True]
        self.onWater = None  # boolean Range: [False, True]

    def Start_when(self):
       return True

    def Takeoff_when(self):
       return True

    def Flying_when(self):
       if self.target_distance > 5: return True
       else: return False

    def RTH_when(self):
       if self.bad_connection == True: return True
       else: return False

    def Glide_when(self):
       if self.bad_connection == True: return True
       else: return False

    def CheckStatus_when(self):
       return True

    def SafeLand_when(self):
       if self.battery <= 10: return True
       else: return False

    def MoveAside_when(self):
       if self.battery <= 10: return True
       else: return False

    def Keepflying_when(self):
       if self.battery <= 10: return True
       else: return False

    def LandingToDelever_when(self):
       if self.target_distance <= 5: return True
       else: return False

    def Shutdown_when(self):
       return True

    def create_update_variables(self, new_data):
        self.altitude = new_data["altitude"]
        self.target_distance = new_data["target_distance"]
        self.origin_distance = new_data["origin_distance"]
        self.battery = new_data["battery"]
        self.obstacle = new_data["obstacle"]
        self.armed = new_data["armed"]
        self.bad_connection = new_data["bad_connection"]
        self.onWater = new_data["onWater"]
