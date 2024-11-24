import time
import pygame
import math
from api import Scenario


class MapViewer:
    def __init__(self,id=None, numberOfVehicles=10, numberOfCustomers=20, speed=0.2):
        # Initialize Pygame
        pygame.init()

        # Define map boundaries
        self.latMax = 48.165312
        self.latMin = 48.113
        self.longMax = 11.6467088
        self.longMin = 11.50302

        # Screen dimensions
        self.screen_height = 700
        self.screen_width = 1100
        self.map_height = 463
        self.map_width = 850

        # Load the map image
        self.map_image = pygame.image.load("MAPS.png")
        self.font = pygame.font.Font("ff.otf", 13)
        self.lfont = pygame.font.Font("ff.otf", 20)

        # Create the Pygame screen
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Map Viewer")

        # Initialize the scenario
        self.obj = Scenario(id, numberOfVehicles, numberOfCustomers, speed)
        print("Playing on " + self.obj.scenario_id)

        self.text = self.font.render(str(self.obj.scenario_id), False, (255, 255, 255))  # White text

        # Application loop variables
        self.running = True
        self.last_update_time = 0

    def latlong_to_pixels(self, lat, long):
        x = int((long - self.longMin) / (self.longMax - self.longMin) * self.map_width)
        y = int((self.latMax - lat) / (self.latMax - self.latMin) * self.map_height)  # Invert Y axis
        return x, y

    def interpolate_points(self, point1, point2, t):
        lat1, long1 = point1
        lat2, long2 = point2
        lat = lat1 + t * (lat2 - lat1)
        long = long1 + t * (long2 - long1)
        return lat, long

    def draw_dashed_line(self, surface, color, start_pos, end_pos, dash_length=10, space_length=5, width=1):
        x1, y1 = start_pos
        x2, y2 = end_pos

        # Calculate the total distance and direction of the line
        dx, dy = x2 - x1, y2 - y1
        distance = math.sqrt(dx ** 2 + dy ** 2)
        angle = math.atan2(dy, dx)

        # Position along the line
        current_distance = 0

        while current_distance < distance:
            # Calculate start and end points of the dash
            start_x = x1 + math.cos(angle) * current_distance
            start_y = y1 + math.sin(angle) * current_distance
            end_distance = min(current_distance + dash_length, distance)
            end_x = x1 + math.cos(angle) * end_distance
            end_y = y1 + math.sin(angle) * end_distance

            # Draw the dash segment
            pygame.draw.line(surface, color, (start_x, start_y), (end_x, end_y), width)

            # Move to the next segment
            current_distance += dash_length + space_length

    def draw_customers(self, customers, color=(255, 0, 0), radius=5):
        for customer in customers:
            if not customer["awaitingService"]:
                continue
            lat = customer["coordX"]
            long = customer["coordY"]
            x, y = self.latlong_to_pixels(lat, long)
            pygame.draw.circle(self.screen, color, (x, y), radius)

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

    def totaltime(self, point1, point2, speed_kmp):
        lat1, long1 = point1
        lat2, long2 = point2
        distance = self.haversine_distance(lat1, long1, lat2, long2)  # Distance in kilometers
        speed_kps = speed_kmp / 3600  # Speed in kilometers per second
        return distance / speed_kps

    def draw_vehicles(self, vehicles, customers):
        for vehicle in vehicles:
            if vehicle["customerId"] is None:
                x, y = self.latlong_to_pixels(vehicle["coordX"], vehicle["coordY"])
                pygame.draw.circle(self.screen, (0, 1, 0), (x, y), 7)
            else:
                for customer in customers:
                    if(vehicle["customerId"] != customer["id"]):
                        continue
                    # customer is in car
                    if (vehicle["coordX"] == customer["coordX"] and vehicle["coordY"] == customer["coordY"]):
                        startp = (vehicle["coordX"], vehicle["coordY"])
                        endp = (customer["destinationX"], customer["destinationY"])

                        key = vehicle["id"] + customer["id"]

                        ttime = self.obj.getRouteTime(key, vehicle["remainingTravelTime"])
                        point = self.interpolate_points(startp, endp, 1 - (vehicle["remainingTravelTime"] / ttime))

                        x, y = self.latlong_to_pixels(point[0], point[1])
                        x1, y1 = self.latlong_to_pixels(endp[0], endp[1])
                        self.draw_dashed_line(self.screen, (0, 1, 0), (x, y), (x1, y1))
                        pygame.draw.circle(self.screen, (0, 1, 0), (x, y), 7)
                    else:
                        startp = (vehicle["coordX"], vehicle["coordY"])
                        endp = (customer["coordX"], customer["coordY"])
                        cendp = (customer["destinationX"], customer["destinationY"])

                        key = vehicle["id"] + customer["id"]

                        ttime = self.obj.getRouteTime(key, vehicle["remainingTravelTime"])
                        point = self.interpolate_points(startp, endp, 1 - (vehicle["remainingTravelTime"] / ttime))

                        x, y = self.latlong_to_pixels(point[0], point[1])
                        x1, y1 = self.latlong_to_pixels(endp[0], endp[1])
                        x2, y2 = self.latlong_to_pixels(cendp[0], cendp[1])
                        self.draw_dashed_line(self.screen, (0, 1, 0), (x, y), (x1, y1))
                        self.draw_dashed_line(self.screen, (0, 1, 0), (x1, y1), (x2, y2))
                        pygame.draw.circle(self.screen, (0, 1, 0), (x, y), 7)
                    break

    def draw(self, scenario):
        self.draw_customers(scenario.getCustomers())
        self.draw_vehicles(scenario.getVehicles(), scenario.getCustomers())

    def update(self):
        current_time = time.time() * 1000  # Get the current time in milliseconds
        if current_time - self.last_update_time > 500:
            self.obj.updateState()
            self.obj.assignVehicles()
            self.last_update_time = current_time

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    result = self.obj.assignVehicles()
                    print(result)

    def display_info(self):
        ftxt = self.lfont.render("Started at : " + self.obj.state["startTime"],
                                 False, pygame.Color("white"))
        self.screen.blit(ftxt, (self.map_width-40, self.map_height + 40))

        count = 0
        idleCount = 0
        inUse = 0

        for vehicle in self.obj.getVehicles():
            count += vehicle["distanceTravelled"]
            if(vehicle["customerId"] is None):
                idleCount += 1
            else:
                inUse += 1

        distanceStats = self.lfont.render("Total TravelDistance : "+str(int(count)),
                                          False, (255, 255, 255))

        idle = self.lfont.render("Idle: " + str(idleCount) + "  /  " + str(self.obj.numberOfVehicles),
                                 False, pygame.Color("green"))

        used = self.lfont.render("In Use: " + str(inUse) + "  /  " + str(self.obj.numberOfVehicles),
                                 False, pygame.Color("red"))

        # Calculate the available space area
        text_x = self.map_width + 10
        text_y = 20

        # Blit the text in the available space
        self.screen.blit(self.text, (text_x, text_y))
        self.screen.blit(distanceStats, (10, self.map_height + 5))
        self.screen.blit(idle, (10, self.map_height + 25))
        self.screen.blit(used, (10, self.map_height + 45))

    def main_loop(self):
        while self.running:
            self.update()
            self.handle_events()

            self.screen.fill((0, 0, 0))

            # Draw the map
            self.screen.blit(self.map_image, (0, 0))

            self.draw(self.obj)
            self.display_info()

            # Update the display
            pygame.display.flip()

        pygame.quit()


# Run the MapViewer application
if __name__ == "__main__":
    viewer = MapViewer(None,50,200,0.1)
    viewer.main_loop()
