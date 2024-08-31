class DynamicClass:
    def __init__(self):
        self.current_alt = None  # float Range: [0, 1000.0]
        self.action = None
        self.target_distance = None  # float Range: [0.0, 10000.0]
        self.action = None
        self.origin_distance = None  # float Range: [0.0, 10000.0]
        self.action = None
        self.battery = None  # float Range: [0.0, 100.0]
        self.action = None
        self.obstacle = None  # boolean Range: [False, True]
        self.action = None
        self.is_armed = None  # boolean Range: [False, True]
        self.action = None
        self.bad_connection = None  # boolean Range: [False, True]
        self.action = None
        self.onWater = None  # boolean Range: [False, True]
        self.action = None

    @property
    def arm__when(self):
       return True

    @property
    def takeoff__when(self):
       return True

    @property
    def flying__when(self):
       if self.target_distance > 5: return True
       else: return False

    @property
    def rth__when(self):
       if self.bad_connection == True: return True
       else: return False

    @property
    def glide__when(self):
       if self.bad_connection == True: return True
       else: return False

    @property
    def checkstatus__when(self):
       return True

    @property
    def safeland__when(self):
       if self.battery <= 10: return True
       else: return False

    @property
    def moveaside__when(self):
       if self.battery <= 10: return True
       else: return False

    @property
    def keepflying__when(self):
       if self.battery <= 10: return True
       else: return False

    @property
    def landingtodelever__when(self):
       if self.target_distance <= 5: return True
       else: return False

    @property
    def disarm__when(self):
       return True

    def create_update_variables(self, new_data):
        self.current_alt = new_data["current_alt"]
        self.target_distance = new_data["target_distance"]
        self.origin_distance = new_data["origin_distance"]
        self.battery = new_data["battery"]
        self.obstacle = new_data["obstacle"]
        self.is_armed = new_data["is_armed"]
        self.bad_connection = new_data["bad_connection"]
        self.onWater = new_data["onWater"]
        self.action = new_data["action"]
