class DynamicClass:
    def __init__(self):
        self.altitude = None  # float Range: [0, 1000.0]
        self.action = None
        self.target_distance = None  # float Range: [0.0, 10000.0]
        self.action = None
        self.origin_distance = None  # float Range: [0.0, 10000.0]
        self.action = None
        self.battery = None  # float Range: [0.0, 100.0]
        self.action = None
        self.obstacle = None  # boolean Range: [False, True]
        self.action = None
        self.armed = None  # boolean Range: [False, True]
        self.action = None
        self.bad_connection = None  # boolean Range: [False, True]
        self.action = None
        self.onWater = None  # boolean Range: [False, True]
        self.action = None

    def Start__when(self):
       return True

    def Takeoff__when(self):
       return True

    def Flying__when(self):
       if self.target_distance > 5: return True
       else: return False

    def RTH__when(self):
       if self.bad_connection == True: return True
       else: return False

    def Glide__when(self):
       if self.bad_connection == True: return True
       else: return False

    def CheckStatus__when(self):
       return True

    def SafeLand__when(self):
       if self.battery <= 10: return True
       else: return False

    def MoveAside__when(self):
       if self.battery <= 10: return True
       else: return False

    def Keepflying__when(self):
       if self.battery <= 10: return True
       else: return False

    def LandingToDelever__when(self):
       if self.target_distance <= 5: return True
       else: return False

    def Shutdown__when(self):
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
        self.action = new_data["action"]
