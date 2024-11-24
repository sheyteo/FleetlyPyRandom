import math
import random

import requests
from hungarian_algorithm import algorithm


def create_scenario(number_of_vehicles, number_of_customers):

    base_url = "http://localhost:8080"
    endpoint = f"{base_url}/scenario/create"
    params = {
        "numberOfVehicles": number_of_vehicles,
        "numberOfCustomers": number_of_customers
    }

    try:
        response = requests.post(endpoint, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
        return response.json()["id"]
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def initialize_scenario(db_scenario_id=None):
    base_url = "http://localhost:8090"  # Updated base URL
    endpoint = f"{base_url}/Scenarios/initialize_scenario"
    payload = {}  # Required payload
    params = {"db_scenario_id": db_scenario_id} if db_scenario_id else {}

    try:
        response = requests.post(endpoint, json=payload, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def launch_scenario(scenario_id, speed):
    base_url = "http://localhost:8090"  # Updated base URL
    endpoint = f"{base_url}/Runner/launch_scenario/{scenario_id}"
    params = {"speed": speed}

    try:
        response = requests.post(endpoint, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def update_scenario(scenario_id, vehicles=None):
    base_url = "http://localhost:8090"  # Base URL
    endpoint = f"{base_url}/Scenarios/update_scenario/{scenario_id}"
    payload = {"vehicles": vehicles if vehicles else []}

    try:
        response = requests.put(endpoint, json=payload)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def get_scenario(scenario_id):
    base_url = "http://localhost:8090"  # Base URL
    endpoint = f"{base_url}/Scenarios/get_scenario/{scenario_id}"

    try:
        response = requests.get(endpoint)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
        return response.json()  # Return the JSON response if successful
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

class Scenario:
    def __init__(self, scenario_id=None, numberOfVehicles=5,
                 numberOfCustomers=10, speed=1):
        self.env_speed = speed
        self.numberOfVehicles = numberOfVehicles
        self.numberOfCustomers = numberOfCustomers

        if scenario_id is None:
            self.scenario_id = create_scenario(numberOfVehicles, numberOfCustomers)
        else:
            self.scenario_id = scenario_id

        initialize_scenario(self.scenario_id)
        launch_scenario(self.scenario_id, speed)
        self.state = None
        self.timeDict = {}
        self.cid_set = set()

        self.updateState()

        for customer in self.getCustomers():
            self.cid_set.add(customer["id"])


    def updateState(self):
       self.state = get_scenario(self.scenario_id)


    def getVehicles(self):
        return self.state["vehicles"]

    def getCustomers(self):
        return self.state["customers"]


    def assignVehicles(self):
        vehicles = self.getVehicles()
        customers = self.getCustomers()
        aList = []
        for vehicle in vehicles:
            if vehicle["customerId"] is None:
                for customer in customers:
                    if customer["id"] in self.cid_set:
                        aList.append({"id": vehicle["id"],
                           "customerId": customer["id"]})
                        self.cid_set.remove(customer["id"])
                        print("ASSINING VEHICLE", vehicle["id"],"to", customer["id"])
                        break

        return update_scenario(self.scenario_id, aList)
    '''
    def assignVehicles(self):
        vehicles = self.getVehicles()
        customers = self.getCustomers()
        aList = []

        vecCount = self.numberOfVehicles

        cusCount = 0
        for customer in customers:
            if customer["id"] in self.cid_set:
                cusCount += 1

        size = max(vecCount,cusCount)

        matrix = {}


        isVec = False

        if vecCount > cusCount:
            currentCusCount = vecCount -cusCount
            for vehicle in vehicles:
                tempArr = {}
                for customer in customers:
                    if customer["id"] in self.cid_set:
                        tempArr[customer["id"]] = self.costFunction(vehicle, customer)

                for i in range(currentCusCount):
                    tempArr[str(random.random())] = 0

                matrix[vehicle["id"]] = tempArr
            isVec = True
        else:
            currentVecCount = cusCount-vecCount
            for customer in customers:
                tempArr = {}
                if customer["id"] in self.cid_set:
                    for vehicle in vehicles:
                        tempArr[vehicle["id"]] = self.costFunction(vehicle, customer)
                    matrix[customer["id"]] = tempArr

                for i in range(currentVecCount):
                    tempArr[str(random.random())] = 0

        aList = algorithm.find_matching(matrix,"min","list")
        self.assignCustomers(aList,isVec)


    def haversine_distance(self, lat1, long1, lat2, long2):
        # Convert degrees to radians
        R = 6371  # Earth's radius in kilometers
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(long2 - long1)

        # Haversine formula
        a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c


    def costFunction(self,vehicle,customer):#
        if vehicle is None or customer is None:
            return 0

        x_dest = -1
        y_dest = -1

        for _customer in self.getCustomers():
            if(_customer["id"] is vehicle["customerId"]):
                x_dest = _customer["destinationX"]
                y_dest = _customer["destinationY"]


        if vehicle["customerId"] is not None and x_dest != -1:
            return (vehicle["remainingTravelTime"] * vehicle["vehicleSpeed"] +
                    self.haversine_distance(x_dest, y_dest, customer["coordX"], customer["coordY"]))

        return self.haversine_distance(vehicle["coordX"],vehicle["coordY"],customer["coordX"],customer["coordY"])

    def assignCustomers(self, aList, isVec):
        retList = []

        idx0 = 0
        idx1 = 1
        if isVec:
            idx0 = 1
            idx1 = 0

        for tpl in aList:
            if tpl[0][idx1] is None or tpl[0][idx0] is None:
                continue

            for vehicle in self.getVehicles():
                if vehicle["customerId"] is None and vehicle["id"] == tpl[0][idx1]:
                    retList.append({"id": vehicle["id"],
                                      "customerId": tpl[0][idx0]})
                    self.cid_set.remove(tpl[0][idx0])
                    print("ASSINING VEHICLE", vehicle["id"], "to", tpl[0][idx0])
        return update_scenario(self.scenario_id, retList)
    '''
    def getRouteTime(self, key,time):
        if key in self.timeDict:
            self.timeDict[key] = max(self.timeDict[key], time-0.001)
            if time == self.timeDict[key]:
                print("Override, possible Error")
            return self.timeDict[key]
        print(key+" is finished in "+str(time))
        self.timeDict[key] = time
        return time



# Example usage
if __name__ == "__main__": # Replace with the actual base URL
    number_of_vehicles = 5
    number_of_customers = 10

    scenarioId = create_scenario(number_of_vehicles, number_of_customers)
    initialize_scenario(scenarioId)
    launch_scenario(scenarioId, 1)

    resp2 = update_scenario(scenarioId)
      #                      [{"id": resp1["scenario"]["vehicles"][0]["id"],
    #                       "customerId": resp1["scenario"]["customers"][0]["id"]}])

    print(get_scenario(scenarioId))

