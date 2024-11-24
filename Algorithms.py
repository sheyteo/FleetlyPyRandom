from typing import List, Tuple

from api import Scenario

class Algorithm:
    def __init__(self):
        pass

    def solve(self, scenario: Scenario) -> List[dir]:
        pass


class RandomAlgorithm(Algorithm):
    def solve(self, scenario: Scenario) -> List[dir]:
        vehicles = scenario.getVehicles()
        customers = scenario.getCustomers()
        aList = []
        for vehicle in vehicles:
            if vehicle["customerId"] is None:
                for customer in customers:
                    if customer["id"] in scenario.cid_set:
                        aList.append({"id": vehicle["id"],
                                      "customerId": customer["id"]})
                        scenario.cid_set.remove(customer["id"])
                        print("ASSINING VEHICLE", vehicle["id"], "to", customer["id"])
                        break
        return aList