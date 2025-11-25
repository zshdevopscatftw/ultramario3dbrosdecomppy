#!/usr/bin/env python3
import pygame
import math
import sys

# --- CONFIGURATION ---
WIDTH, HEIGHT = 800, 600
FPS = 60
FOV = 400
VIEW_DIST = 4
SENSITIVITY = 0.01

# --- COLORS ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (220, 0, 0)
BLUE = (0, 0, 220)
SKIN = (255, 200, 150)
BROWN = (100, 50, 0)
YELLOW = (255, 215, 0)
SKY_BLUE = (135, 206, 235)
GRASS_GREEN = (34, 139, 34)

# --- 3D MATH HELPERS ---
def rotate_x(x, y, z, angle):
    rad = angle
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    return x, y * cos_a - z * sin_a, y * sin_a + z * cos_a

def rotate_y(x, y, z, angle):
    rad = angle
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    return x * cos_a + z * sin_a, y, -x * sin_a + z * cos_a

def project(x, y, z, width, height, scale=FOV, distance=VIEW_DIST):
    factor = scale / (z + distance)
    x_2d = x * factor + width / 2
    y_2d = -y * factor + height / 2  # Invert Y for screen coords
    return int(x_2d), int(y_2d), factor

# --- CLASSES ---

class Vertex:
    def __init__(self, x, y, z, color):
        self.x = x
        self.y = y
        self.z = z
        self.base_x = x
        self.base_y = y
        self.base_z = z
        self.color = color
        self.vx = 0
        self.vy = 0
        self.vz = 0

    def update_elastic(self):
        # Spring physics to return to base shape
        k = 0.1   # Spring constant
        d = 0.85  # Damping
        
        ax = (self.base_x - self.x) * k
        ay = (self.base_y - self.y) * k
        az = (self.base_z - self.z) * k
        
        self.vx += ax
        self.vy += ay
        self.vz += az
        
        self.vx *= d
        self.vy *= d
        self.vz *= d
        
        self.x += self.vx
        self.y += self.vy
        self.z += self.vz

class MarioFace:
    def __init__(self):
        self.vertices = []
        self.rotation_y = 0
        self.dragging_point = None
        
        # Generate Geometry (Low Poly Sphere approximation)
        # Face (Skin)
        for i in range(100):
            theta = math.acos(1 - 2 * (i + 0.5) / 100)
            phi = math.pi * (1 + 5**0.5) * (i + 0.5)
            r = 1.0
            x = r * math.sin(theta) * math.cos(phi)
            y = r * math.sin(theta) * math.sin(phi)
            z = r * math.cos(theta)
            
            # Color logic based on position
            col = SKIN
            if y > 0.4 and z > 0: col = RED # Hat
            elif z > 0.8 and y < 0.2: col = SKIN # Nose area
            
            # Nose bump
            if z > 0.8 and y < 0:
                z += 0.3
                
            self.vertices.append(Vertex(x, y, z, col))

        # Hat Brim
        for i in range(20):
            angle = (i / 20) * math.pi * 2
            x = math.cos(angle) * 1.2
            z = math.sin(angle) * 1.2 + 0.2
            y = 0.4
            if z > 0: # Only front brim
                 self.vertices.append(Vertex(x, y, z, RED))

        # Mustache
        self.vertices.append(Vertex(-0.5, -0.2, 0.9, BLACK))
        self.vertices.append(Vertex(0.5, -0.2, 0.9, BLACK))
        self.vertices.append(Vertex(0, -0.1, 1.1, SKIN)) # Nose tip

    def update(self, mouse_pos, mouse_down, width, height):
        self.rotation_y += 0.01
        
        mx, my = mouse_pos
        
        # Spring physics
        for v in self.vertices:
            v.update_elastic()

        # Interaction
        if mouse_down:
            # Find closest vertex to mouse in 2D projection
            closest = None
            min_dist = 50 # Grab radius
            
            for v in self.vertices:
                # Calculate current projected position
                # Apply rotation first
                rx, ry, rz = rotate_y(v.x, v.y, v.z, self.rotation_y)
                px, py, scale = project(rx, ry, rz, width, height, FOV, 3.5)
                
                dist = math.hypot(px - mx, py - my)
                if dist < min_dist:
                    min_dist = dist
                    closest = v
            
            if closest:
                # Pull vertex towards mouse (approximate unprojection)
                # This is a hacky "pull", essentially dragging the vertex in 3D space
                # relative to camera plane
                closest.x += (mx - width/2) * 0.001
                closest.y -= (my - height/2) * 0.001
    
    def draw(self, surface):
        # Sort vertices by Z depth for painter's algorithm
        # We need to compute rotated positions first
        projected_points = []
        
        for v in self.vertices:
            rx, ry, rz = rotate_y(v.x, v.y, v.z, self.rotation_y)
            px, py, scale = project(rx, ry, rz, WIDTH, HEIGHT, FOV, 3.5)
            projected_points.append((rz, px, py, scale, v.color))
            
        projected_points.sort(key=lambda x: x[0], reverse=False)
        
        for p in projected_points:
            rz, px, py, scale, color = p
            size = max(2, int(10 * scale))
            pygame.draw.circle(surface, color, (px, py), size)
            
            # Simple shading
            if rz < 0:
                pygame.draw.circle(surface, (0,0,0), (px, py), size, 1)

class DemoRunner:
    def __init__(self):
        self.time = 0
        self.cam_angle = 0
        
    def draw_cube(self, surface, x, y, z, w, h, d, color):
        # A simple cube renderer
        # Define 8 corners
        corners = [
            (x-w, y-h, z-d), (x+w, y-h, z-d), (x+w, y+h, z-d), (x-w, y+h, z-d),
            (x-w, y-h, z+d), (x+w, y-h, z+d), (x+w, y+h, z+d), (x-w, y+h, z+d)
        ]
        
        # Rotate world around camera
        rot_corners = []
        for cx, cy, cz in corners:
            # Rotate around Y (orbit)
            rx, ry, rz = rotate_y(cx, cy, cz, -self.cam_angle)
            # Offset for camera
            rz += 15 # Move world away from camera
            ry -= 2  # Camera height
            rot_corners.append((rx, ry, rz))
            
        # Project
        proj_points = []
        for rx, ry, rz in rot_corners:
            px, py, s = project(rx, ry, rz, WIDTH, HEIGHT, FOV, 0)
            proj_points.append((px, py))
            
        # Draw edges (Wireframe style for speed)
        edges = [
            (0,1), (1,2), (2,3), (3,0), # Back face
            (4,5), (5,6), (6,7), (7,4), # Front face
            (0,4), (1,5), (2,6), (3,7)  # Connecting
        ]
        
        for s, e in edges:
            pygame.draw.line(surface, color, proj_points[s], proj_points[e], 3)
            
        # Fill center (rough)
        center_x = sum(p[0] for p in proj_points) // 8
        center_y = sum(p[1] for p in proj_points) // 8
        pygame.draw.circle(surface, color, (center_x, center_y), 5)

    def update_and_draw(self, surface):
        self.time += 0.05
        self.cam_angle += 0.01
        
        # Floor grid
        for i in range(-5, 6):
            # Horizontal lines
            p1 = rotate_y(i*2, -2, -10, -self.cam_angle)
            p2 = rotate_y(i*2, -2, 10, -self.cam_angle)
            pp1 = project(p1[0], p1[1]-2, p1[2]+15, WIDTH, HEIGHT, FOV, 0)
            pp2 = project(p2[0], p2[1]-2, p2[2]+15, WIDTH, HEIGHT, FOV, 0)
            pygame.draw.line(surface, (50, 100, 50), (pp1[0], pp1[1]), (pp2[0], pp2[1]), 1)
            
            # Vertical lines
            p3 = rotate_y(-10, -2, i*2, -self.cam_angle)
            p4 = rotate_y(10, -2, i*2, -self.cam_angle)
            pp3 = project(p3[0], p3[1]-2, p3[2]+15, WIDTH, HEIGHT, FOV, 0)
            pp4 = project(p4[0], p4[1]-2, p4[2]+15, WIDTH, HEIGHT, FOV, 0)
            pygame.draw.line(surface, (50, 100, 50), (pp3[0], pp3[1]), (pp4[0], pp4[1]), 1)

        # Animate Mario
        # Running circle path
        mx = math.sin(self.time) * 5
        mz = math.cos(self.time) * 5
        my = math.sin(self.time * 5) * 0.5 # Bobbing
        
        facing = self.time + math.pi/2 # Face tangent to circle
        
        # Draw Body Parts relative to Mario Pos
        def draw_part(off_x, off_y, off_z, w, h, d, col, anim_rot=0):
            # 1. Rotate part local
            # 2. Translate to Mario Pos
            # 3. Rotate Mario around World Origin
            
            # Simplified: Just calculating world positions manually for demo
            
            # Limb animation
            lx = off_x
            ly = off_y
            lz = off_z
            
            # Apply Mario rotation
            rx, ry, rz = rotate_y(lx, ly, lz, facing)
            
            # World pos
            wx = mx + rx
            wy = my + ry
            wz = mz + rz
            
            self.draw_cube(surface, wx, wy, wz, w, h, d, col)

        # Torso
        draw_part(0, 0, 0, 0.5, 0.6, 0.3, RED)
        # Head
        draw_part(0, 1.0, 0, 0.4, 0.4, 0.4, SKIN)
        # Hat
        draw_part(0, 1.4, 0, 0.5, 0.1, 0.5, RED)
        
        # Limbs (Simple Swing)
        leg_swing = math.sin(self.time * 10) * 0.5
        arm_swing = math.cos(self.time * 10) * 0.5
        
        # Left Leg
        draw_part(-0.3, -1.0, leg_swing, 0.2, 0.4, 0.2, BLUE)
        # Right Leg
        draw_part(0.3, -1.0, -leg_swing, 0.2, 0.4, 0.2, BLUE)
        # Left Arm
        draw_part(-0.7, 0.2, arm_swing, 0.15, 0.4, 0.15, RED)
        # Right Arm
        draw_part(0.7, 0.2, -arm_swing, 0.15, 0.4, 0.15, RED)

# --- MAIN ---

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("ULTRA MARIO 3D BROS")
    clock = pygame.time.Clock()
    font_title = pygame.font.SysFont("Arial", 64, bold=True)
    font_sub = pygame.font.SysFont("Arial", 32)
    
    face = MarioFace()
    demo = DemoRunner()
    
    state = "MENU" # MENU or DEMO
    
    running = True
    while running:
        mouse_down = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_down = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if state == "MENU":
                        state = "DEMO"
                    else:
                        state = "MENU"
        
        screen.fill(SKY_BLUE)
        
        if state == "MENU":
            # Draw Face
            face.update(pygame.mouse.get_pos(), pygame.mouse.get_pressed()[0], WIDTH, HEIGHT)
            face.draw(screen)
            
            # Draw UI
            title = font_title.render("ULTRA MARIO 3D", True, YELLOW)
            shadow = font_title.render("ULTRA MARIO 3D", True, BLACK)
            
            # Bouncing Text
            y_off = math.sin(pygame.time.get_ticks() * 0.005) * 10
            
            screen.blit(shadow, (WIDTH//2 - title.get_width()//2 + 4, 54 + y_off))
            screen.blit(title, (WIDTH//2 - title.get_width()//2, 50 + y_off))
            
            sub = font_sub.render("PRESS SPACE TO START", True, WHITE)
            screen.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT - 100))
            
            info = font_sub.render("(Click & Drag Face!)", True, BLACK)
            screen.blit(info, (WIDTH//2 - info.get_width()//2, HEIGHT - 50))
            
        elif state == "DEMO":
            # Draw Demo
            # Draw Ground Plane Half
            pygame.draw.rect(screen, GRASS_GREEN, (0, HEIGHT//2, WIDTH, HEIGHT//2))
            
            demo.update_and_draw(screen)
            
            # UI
            txt = font_sub.render("DEMO MODE - AI RUNNING", True, WHITE)
            screen.blit(txt, (20, 20))
            
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
