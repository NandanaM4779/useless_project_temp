import sys
import math
import serial
import time
import pygame

# --- Serial and Pygame Setup ---
SERIAL_PORT = 'COM7'
BAUD_RATE = 115200

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600

# Sensor positions defined in centimeters.
x0, y0 = 0.0, 30.0  # Left-bottom corner
x1, y1 = 30.0, 30.0  # Right-bottom corner
x2, y2 = 15.0, 0.0   # Top-middle corner

# Dynamic scale factor based on the physical dimensions of the box
# The 1.25 factor adds padding to ensure the entire box fits on the screen.
max_x = max(x0, x1, x2)
max_y = max(y0, y1, y2)
max_dim = max(max_x, max_y)
SCALE = SCREEN_WIDTH / (max_dim * 1.25)

# --- Color Definitions ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 100, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
ORANGE = (255, 165, 0)

# --- Global Variables for Filtering ---
d1_history, d2_history, d3_history = [], [], []
FILTER_SIZE = 5

def trilaterate(d1, d2, d3):
    """
    Calculates the (x, y) coordinates of an object given three distances and
    three known sensor positions.
    """
    A = 2 * (x1 - x0)
    B = 2 * (y1 - y0)
    C = d1**2 - d2**2 - x0**2 + x1**2 - y0**2 + y1**2
    D = 2 * (x2 - x1)
    E = 2 * (y2 - y1)
    F = d2**2 - d3**2 - x1**2 + x2**2 - y1**2 + y2**2

    det = A * E - B * D
    if det == 0:
        return None

    x_coordinate = (C * E - B * F) / det
    y_coordinate = (A * F - C * D) / det

    return (x_coordinate, y_coordinate)

def draw_sensor_layout(screen, SCALE):
    """Draws a visual representation of the sensor layout."""
    font = pygame.font.Font(None, 24)
    # Scale sensor positions to Pygame coordinates for drawing
    s0_x, s0_y = int(x0 * SCALE), int(SCREEN_HEIGHT - (y0 * SCALE))
    s1_x, s1_y = int(x1 * SCALE), int(SCREEN_HEIGHT - (y1 * SCALE))
    s2_x, s2_y = int(x2 * SCALE), int(SCREEN_HEIGHT - (y2 * SCALE))

    # Draw circles for each sensor
    pygame.draw.circle(screen, GREEN, (s0_x, s0_y), 5)
    pygame.draw.circle(screen, GREEN, (s1_x, s1_y), 5)
    pygame.draw.circle(screen, GREEN, (s2_x, s2_y), 5)

    # Draw a polygon representing the box perimeter
    pygame.draw.polygon(screen, GREEN, [(s0_x, s0_y), (s1_x, s1_y), (s2_x, s2_y)], 1)

    # Add text labels for sensor positions
    text0 = font.render(f"({x0}, {y0})", True, GREEN)
    text1 = font.render(f"({x1}, {y1})", True, GREEN)
    text2 = font.render(f"({x2}, {y2})", True, GREEN)
    screen.blit(text0, (s0_x + 10, s0_y))
    screen.blit(text1, (s1_x + 10, s1_y))
    screen.blit(text2, (s2_x + 10, s2_y))

def filter_distances(d1, d2, d3):
    """Applies a simple moving average filter to the distances."""
    d1_history.append(d1)
    d2_history.append(d2)
    d3_history.append(d3)
    
    if len(d1_history) > FILTER_SIZE:
        d1_history.pop(0)
        d2_history.pop(0)
        d3_history.pop(0)
    
    avg_d1 = sum(d1_history) / len(d1_history)
    avg_d2 = sum(d2_history) / len(d2_history)
    avg_d3 = sum(d3_history) / len(d3_history)
    
    return avg_d1, avg_d2, avg_d3

# --- Main Program Loop ---
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
    print(f"Successfully connected to Arduino on {SERIAL_PORT}")

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Wheres the ball")
    clock = pygame.time.Clock()
    path = []
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        try:
            value = ser.readline()
            valueInString = value.decode('utf-8').strip()
            if valueInString:
                distances = valueInString.split(',')
                if len(distances) == 3:
                    try:
                        d1_raw = float(distances[0])
                        d2_raw = float(distances[1])
                        d3_raw = float(distances[2])
                        
                        d1, d2, d3 = filter_distances(d1_raw, d2_raw, d3_raw)
                        
                        pos = trilaterate(d1, d2, d3)

                        if pos:
                            x, y = pos
                            
                            pygame_x = int(x * SCALE)
                            pygame_y = int(SCREEN_HEIGHT - (y * SCALE))

                            path.append((pygame_x, pygame_y))
                            
                            if len(path) > 100:
                                path.pop(0)
                            
                            print(f"Coordinates: X={x:.2f}, Y={y:.2f}")

                    except ValueError:
                        print("Could not convert distance to number")
                else:
                    print(f"Received an incomplete line: {valueInString}")
        except Exception as e:
            print(f"Error reading from serial: {e}")
        
        screen.fill(BLACK)
        draw_sensor_layout(screen, SCALE)
        
        for i, pos_on_screen in enumerate(path):
            dot_color = (int(255 * (i % 3) / 2), int(255 * ((i+1) % 3) / 2), int(255 * ((i+2) % 3) / 2))
            pygame.draw.circle(screen, dot_color, pos_on_screen, 3)

        if path:
            pygame.draw.circle(screen, RED, path[-1], 6)
        
        pygame.display.flip()
        clock.tick(30)

except serial.SerialException as e:
    print(f"Could not open serial port {SERIAL_PORT}. Check connection. Error: {e}")
    sys.exit()
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    sys.exit()
finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
    if pygame.get_init():
        pygame.quit()
    sys.exit()