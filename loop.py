from api import Scenario
import time  # Import time to use for tracking elapsed time
import pygame
import math


# Initialize Pygame
pygame.init()

# Define map boundaries
latMax = 48.165312
latMin = 48.113
longMax = 11.6467088
longMin = 11.50302

# Screen dimensions (match your MAP.png dimensions)
screen_height = 700  # Adjust to your map image size
screen_width = 1100  # Adjust to your map image size

map_height = 463  # Adjust to your map image size
map_width = 850  # Adjust to your map image size

# Load the map image
map_image = pygame.image.load("MAPS.png")

font = pygame.font.Font("ff.otf", 13)
lfont = pygame.font.Font("ff.otf", 20)

# Create the Pygame screen
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Map Viewer")

obj = Scenario(None, 50, 200, 0.1)
print("Playing on " + obj.scenario_id)

text = font.render(str(obj.scenario_id), False, (255, 255, 255))  # White text

# Application loop
running = True
last_update_time = 0  # Initialize the last update time

def draw_dashed_line(surface, color, start_pos, end_pos, dash_length=10, space_length=5, width=1):
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


def latlong_to_pixels(lat, long):
    x = int((long - longMin) / (longMax - longMin) * map_width)
    y = int((latMax - lat) / (latMax - latMin) * map_height)  # Invert Y axis
    return x, y


def interpolate_points(point1, point2, t):
    lat1, long1 = point1
    lat2, long2 = point2
    lat = lat1 + t * (lat2 - lat1)
    long = long1 + t * (long2 - long1)
    return lat, long


def draw_customers(screen, customers, color=(255, 0, 0), radius=5):
    for customer in customers:
        if not customer["awaitingService"]:
            continue
        lat = customer["coordX"]
        long = customer["coordY"]
        x, y = latlong_to_pixels(lat, long)
        pygame.draw.circle(screen, color, (x, y), radius)

def haversine_distance(lat1, long1, lat2, long2):
    # Convert degrees to radians
    R = 6371  # Earth's radius in kilometers
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(long2 - long1)

    # Haversine formula
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def totaltime(point1, point2, speed_kmp):
    lat1, long1 = point1
    lat2, long2 = point2
    distance = haversine_distance(lat1, long1, lat2, long2)  # Distance in kilometers
    speed_kps = speed_kmp / 3600  # Speed in kilometers per second
    return distance / speed_kps

def draw_vehicles(screen,vehicles,customers):
    for vehicle in obj.getVehicles():
        if vehicle["customerId"] is None:
            x, y = latlong_to_pixels(vehicle["coordX"], vehicle["coordY"])
            pygame.draw.circle(screen, (0,1,0), (x, y), 7)
        else:
            for customer in customers:
                if(vehicle["customerId"] != customer["id"]):
                    continue
                # custmer is in car
                if (vehicle["coordX"] == customer["coordX"]
                    and vehicle["coordY"] == customer["coordY"]):
                    startp = (vehicle["coordX"], vehicle["coordY"])
                    endp = (customer["destinationX"], customer["destinationY"])

                    key = vehicle["id"] + customer["id"]

                    ttime = obj.getRouteTime(key, vehicle["remainingTravelTime"])
                    point = interpolate_points(startp, endp, 1 - (vehicle["remainingTravelTime"] / ttime))

                    x, y = latlong_to_pixels(point[0], point[1])
                    x1, y1 = latlong_to_pixels(endp[0], endp[1])
                    draw_dashed_line(screen,(0,1,0),(x,y),(x1,y1))
                    pygame.draw.circle(screen, (0, 1, 0), (x, y), 7)
                else:
                    startp = (vehicle["coordX"], vehicle["coordY"])
                    endp = (customer["coordX"], customer["coordY"])
                    cendp = (customer["destinationX"], customer["destinationY"])

                    key = vehicle["id"]+customer["id"]

                    ttime = obj.getRouteTime(key,vehicle["remainingTravelTime"])
                    point = interpolate_points(startp, endp, 1 - (vehicle["remainingTravelTime"] / ttime))

                    x, y = latlong_to_pixels(point[0], point[1])
                    x1, y1 = latlong_to_pixels(endp[0], endp[1])
                    x2, y2 = latlong_to_pixels(cendp[0], cendp[1])
                    draw_dashed_line(screen, (0, 1, 0), (x, y), (x1,y1))
                    draw_dashed_line(screen, (0, 1, 0), (x1, y1), (x2,y2))
                    pygame.draw.circle(screen, (0, 1, 0), (x, y), 7)
                break



def draw(screen, scenario):
    draw_customers(screen, scenario.getCustomers())
    draw_vehicles(screen, scenario.getVehicles(),scenario.getCustomers())


while running:
    current_time = time.time() * 1000  # Get the current time in milliseconds

    # Only call obj.updateState if 100 milliseconds have passed
    if current_time - last_update_time > 500:
        obj.updateState()
        erg = obj.assignVehicles()
        last_update_time = current_time


    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                result = obj.assignVehicles()
                print(result)

    screen.fill((0, 0, 0))





    ftxt = lfont.render("Started at : " + obj.state["startTime"],
                        False, pygame.Color("white"))
    screen.blit(ftxt, (map_width, map_height + 40))

    #change text :
    count = 0
    idleCount = 0
    inUse = 0

    for vehicle in obj.getVehicles():
        count += vehicle["distanceTravelled"]
        if(vehicle["customerId"] is None):
            idleCount += 1
        else:
            inUse += 1



    distanceStats = lfont.render("Total TravelDistance : "+str(int(count)),
                              False, (255, 255, 255))

    idle = lfont.render("Idle: " + str(idleCount)+"  /  "+str(obj.numberOfVehicles),
                                 False, pygame.Color("green"))

    used = lfont.render("In Use: " + str(inUse) + "  /  " + str(obj.numberOfVehicles),
                        False, pygame.Color("red"))


    # Calculate the available space area
    text_x = map_width + 10  # 10 pixels to the right of the map
    text_y = 20  # Vertically centered on screen

    # Blit the text in the available space
    screen.blit(text, (text_x, text_y))
    screen.blit(distanceStats, (10, map_height + 5))
    screen.blit(idle, (10, map_height + 25))
    screen.blit(used, (10, map_height + 45))

    # Draw the map
    screen.blit(map_image, (0, 0))

    draw(screen, obj)

    # Update the display
    pygame.display.flip()

pygame.quit()

