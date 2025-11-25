import pygame
import math
import random

# --- CONFIGURATION ---
WIDTH, HEIGHT = 800, 600
FPS = 30
FOV = 500
VIEW_DIST = 6
SCALE = 100

# --- GAME STATES ---
STATE_MENU = "menu"
STATE_GAME = "game"

# --- COLORS ---
SKY_BLUE = (64, 64, 255)
SKY_CYAN = (100, 200, 255)
RED = (255, 0, 0)
RED_ROOF = (220, 20, 20)
BLUE = (0, 0, 255)
SKIN = (255, 218, 185)
BROWN = (139, 69, 19)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
WALL_WHITE = (240, 240, 240)
YELLOW = (255, 255, 0)
GREEN = (34, 139, 34)
DARK_GREEN = (0, 100, 0)
ORANGE = (255, 165, 0)
WATER_BLUE = (50, 100, 200)

# --- ASSET GENERATION ---
def create_eye_sprite(state="open"):
    surf = pygame.Surface((64, 64), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, WHITE, (0, 0, 64, 64))
    if state == "open":
        pygame.draw.ellipse(surf, (50, 50, 255), (16, 8, 32, 48))
        pygame.draw.ellipse(surf, BLACK, (22, 16, 20, 32))
        pygame.draw.circle(surf, WHITE, (36, 24), 6)
    elif state == "half":
        pygame.draw.ellipse(surf, (50, 50, 255), (16, 20, 32, 24))
        pygame.draw.ellipse(surf, BLACK, (22, 24, 20, 16))
        pygame.draw.rect(surf, SKIN, (0, 0, 64, 24))
    elif state == "closed":
        pygame.draw.rect(surf, SKIN, (0, 0, 64, 64))
        pygame.draw.arc(surf, BLACK, (0, 20, 64, 40), 0, math.pi, 3)
    return surf

def create_mouth_sprite(state="neutral"):
    surf = pygame.Surface((64, 32), pygame.SRCALPHA)
    if state == "neutral":
        pygame.draw.line(surf, BLACK, (10, 16), (54, 16), 3)
        pygame.draw.arc(surf, BLACK, (10, 10, 44, 12), math.pi, 0, 2)
    elif state == "smile":
        pygame.draw.arc(surf, BLACK, (5, 0, 54, 30), math.pi, 2*math.pi, 4)
    elif state == "open":
        pygame.draw.ellipse(surf, (100, 0, 0), (10, 0, 44, 32))
        pygame.draw.ellipse(surf, BLACK, (10, 0, 44, 32), 2)
    return surf

def create_window_sprite():
    surf = pygame.Surface((64, 64), pygame.SRCALPHA)
    # Frame
    pygame.draw.circle(surf, (180, 180, 180), (32, 32), 30)
    pygame.draw.circle(surf, (100, 100, 100), (32, 32), 30, 4)
    # Glass
    pygame.draw.circle(surf, (150, 200, 255), (32, 32), 26)
    # Princess abstract shape
    pygame.draw.ellipse(surf, (255, 105, 180), (22, 15, 20, 25))
    pygame.draw.circle(surf, (255, 200, 100), (32, 18), 6)
    return surf

# --- 3D MATH ENGINE ---

class Vector3:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z

def rotate_x(x, y, z, angle):
    c = math.cos(angle)
    s = math.sin(angle)
    return x, y*c - z*s, y*s + z*c

def rotate_y(x, y, z, angle):
    c = math.cos(angle)
    s = math.sin(angle)
    return x*c + z*s, y, -x*s + z*c

def rotate_z(x, y, z, angle):
    c = math.cos(angle)
    s = math.sin(angle)
    return x*c - y*s, x*s + y*c, z

def project(x, y, z, width, height, scale_factor=1.0):
    if z + VIEW_DIST <= 0.1: return None
    factor = (FOV * scale_factor) / (z + VIEW_DIST)
    px = x * factor + width / 2
    py = -y * factor + height / 2
    return (int(px), int(py), factor)

class Mesh:
    """Represents a 3D part"""
    def __init__(self, w, h, d, color):
        self.w, self.h, self.d = w, h, d
        self.color = color
        self.vertices = [
            Vector3(-w/2, -h/2, -d/2), Vector3(w/2, -h/2, -d/2),
            Vector3(w/2, h/2, -d/2),   Vector3(-w/2, h/2, -d/2),
            Vector3(-w/2, -h/2, d/2),  Vector3(w/2, -h/2, d/2),
            Vector3(w/2, h/2, d/2),    Vector3(-w/2, h/2, d/2)
        ]
        self.faces = [
            (0, 1, 2, 3), (5, 4, 7, 6), (4, 0, 3, 7),
            (1, 5, 6, 2), (3, 2, 6, 7), (4, 5, 1, 0)
        ]

    def get_world_polygons(self, px, py, pz, rx, ry, rz, sx=1, sy=1, sz=1):
        transformed_verts = []
        for v in self.vertices:
            tx, ty, tz = v.x * sx, v.y * sy, v.z * sz
            tx, ty, tz = rotate_x(tx, ty, tz, rx)
            tx, ty, tz = rotate_y(tx, ty, tz, ry)
            tx, ty, tz = rotate_z(tx, ty, tz, rz)
            transformed_verts.append((tx + px, ty + py, tz + pz))
            
        polygons = []
        for face_indices in self.faces:
            points_3d = [transformed_verts[i] for i in face_indices]
            # Updated to support triangles (len 3) or quads (len 4)
            avg_z = sum(p[2] for p in points_3d) / len(points_3d)
            
            # Basic Backface Culling
            if len(points_3d) >= 3:
                v1 = (points_3d[1][0] - points_3d[0][0], points_3d[1][1] - points_3d[0][1], points_3d[1][2] - points_3d[0][2])
                v2 = (points_3d[2][0] - points_3d[1][0], points_3d[2][1] - points_3d[1][1], points_3d[2][2] - points_3d[1][2])
                normal_z = v1[0]*v2[1] - v1[1]*v2[0]
                # if normal_z > 0: 
                polygons.append({ 'type': 'poly', 'z': avg_z, 'points_3d': points_3d, 'color': self.color })
        return polygons

class PyramidMesh(Mesh):
    """Represents a Roof/Spire"""
    def __init__(self, w, h, d, color):
        self.w, self.h, self.d = w, h, d
        self.color = color
        self.vertices = [
            Vector3(0, h/2, 0),          # 0: Apex
            Vector3(-w/2, -h/2, -d/2),   # 1: FL
            Vector3(w/2, -h/2, -d/2),    # 2: FR
            Vector3(w/2, -h/2, d/2),     # 3: BR
            Vector3(-w/2, -h/2, d/2)     # 4: BL
        ]
        self.faces = [
            (0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1), # Sides
            (4, 3, 2, 1) # Bottom
        ]

# --- GAME OBJECTS ---

class Castle:
    def __init__(self):
        self.parts = []
        self.window_sprite = create_window_sprite()
        
        # 1. Main Tower
        self.parts.append({'mesh': Mesh(4, 3, 4, WALL_WHITE), 'pos': (0, 0, 0)})
        self.parts.append({'mesh': PyramidMesh(4.5, 2, 4.5, RED_ROOF), 'pos': (0, 2.5, 0)})
        
        # 2. Side Towers
        offsets = [(-3, -2), (3, -2), (-3, 2), (3, 2)]
        for ox, oz in offsets:
            self.parts.append({'mesh': Mesh(1.5, 4, 1.5, WALL_WHITE), 'pos': (ox, -0.5, oz)})
            self.parts.append({'mesh': PyramidMesh(1.8, 1.5, 1.8, RED_ROOF), 'pos': (ox, 2.0, oz)})
            
        # 3. Bridge
        self.parts.append({'mesh': Mesh(2, 0.2, 6, BROWN), 'pos': (0, -1.5, 5)})
        
        # 4. Water/Moat
        self.parts.append({'mesh': Mesh(15, 0.1, 10, WATER_BLUE), 'pos': (0, -2.0, 5)})

    def get_render_data(self, cam_angle_y):
        render_list = []
        
        # Add stained glass window sprite
        # We need to manually rotate the sprite position around the world origin (0,0,0) based on camera
        wx, wy, wz = 0, 0.5, 2.1 # Local position on castle front
        rwx, rwy, rwz = rotate_y(wx, wy, wz, cam_angle_y)
        
        render_list.append({
            'type': 'sprite',
            'z': rwz,
            'pos': (rwx, rwy, rwz),
            'img': self.window_sprite,
            'size': 0.8
        })

        for part in self.parts:
            # Rotate part POSITION around world center (0,0,0) by camera angle
            px, py, pz = part['pos']
            rpx, rpy, rpz = rotate_y(px, py, pz, cam_angle_y)
            
            # Rotate part GEOMETRY by camera angle
            render_list.extend(part['mesh'].get_world_polygons(rpx, rpy, rpz, 0, cam_angle_y, 0))
            
        return render_list

class MarioHead:
    def __init__(self):
        self.face_mesh = Mesh(2.0, 1.8, 1.8, SKIN)
        self.hat_dome = Mesh(2.1, 1.0, 2.0, RED)
        self.hat_brim = Mesh(2.2, 0.2, 1.0, RED)
        self.nose_mesh = Mesh(0.6, 0.5, 0.6, SKIN)
        self.mustache_mesh = Mesh(1.2, 0.3, 0.2, BLACK)
        self.sprites = {
            'eye_open': create_eye_sprite('open'),
            'eye_closed': create_eye_sprite('closed'),
            'mouth_neutral': create_mouth_sprite('neutral'),
            'mouth_smile': create_mouth_sprite('smile'),
            'mouth_open': create_mouth_sprite('open')
        }
        self.blink_timer = 0
        self.eye_state = 'eye_open'

    def get_render_data(self, mx, my, time_val):
        render_list = []
        rot_x, rot_y = my * 0.5, mx * 0.5
        
        def t(ox, oy, oz):
            tx, ty, tz = rotate_x(ox, oy, oz, rot_x)
            tx, ty, tz = rotate_y(tx, ty, tz, rot_y)
            return 0 + tx, 0 + ty, -1 + tz

        # Geometry
        render_list.extend(self.face_mesh.get_world_polygons(*t(0,0,0), rot_x, rot_y, 0))
        render_list.extend(self.hat_dome.get_world_polygons(*t(0,0.8,0), rot_x, rot_y, 0))
        render_list.extend(self.hat_brim.get_world_polygons(*t(0,0.7,0.8), rot_x+0.2, rot_y, 0))
        render_list.extend(self.nose_mesh.get_world_polygons(*t(0,-0.1,1.0), rot_x, rot_y, 0))
        render_list.extend(self.mustache_mesh.get_world_polygons(*t(0,-0.4,1.05), rot_x, rot_y, 0))
        
        # Eyes/Mouth Logic
        self.blink_timer += 1
        if self.blink_timer > 150: self.eye_state = 'eye_closed'
        if self.blink_timer > 155: self.eye_state, self.blink_timer = 'eye_open', 0
            
        lex, ley, lez = t(-0.4, 0.2, 0.92)
        rex, rey, rez = t(0.4, 0.2, 0.92)
        mox, moy, moz = t(0, -0.6, 0.9)
        
        render_list.append({'type':'sprite', 'z':lez, 'pos':(lex,ley,lez), 'img':self.sprites[self.eye_state], 'size':0.4})
        render_list.append({'type':'sprite', 'z':rez, 'pos':(rex,rey,rez), 'img':self.sprites[self.eye_state], 'size':0.4})
        render_list.append({'type':'sprite', 'z':moz, 'pos':(mox,moy,moz), 'img':self.sprites['mouth_neutral'], 'size':0.5})

        return render_list

class MarioActor:
    def __init__(self):
        self.body = Mesh(0.5, 0.6, 0.4, BLUE)
        self.head = Mesh(0.4, 0.4, 0.4, SKIN)
        self.limb = Mesh(0.15, 0.4, 0.15, RED)
        self.limb_b = Mesh(0.15, 0.4, 0.15, BLUE)
        self.pos = Vector3(0, -1.2, 4) # Start on bridge
        self.yaw = 0
        self.face = create_eye_sprite('open')

    def get_render_data(self, time_val, cam_angle_y):
        render_list = []
        gx, gy, gz = self.pos.x, self.pos.y, self.pos.z
        
        def add(mesh, ox, oy, oz, rx, color=None):
            # Rotate offset by Actor Yaw
            tox, toy, toz = rotate_y(ox, oy, oz, self.yaw)
            # Global Pos
            fx, fy, fz = gx + tox, gy + toy, gz + toz
            # Rotate Global Pos by Camera
            cfx, cfy, cfz = rotate_y(fx, fy, fz, cam_angle_y)
            polys = mesh.get_world_polygons(cfx, cfy, cfz, rx, self.yaw + cam_angle_y, 0)
            if color: 
                for p in polys: p['color'] = color
            render_list.extend(polys)
            return cfx, cfy, cfz

        # Body & Head
        add(self.body, 0, -0.5, 0, 0)
        hx, hy, hz = add(self.head, 0, 0.1, 0, 0)
        
        # Face Sprite
        render_list.append({'type':'sprite', 'z':hz, 'pos':(hx,hy,hz+0.2), 'img':self.face, 'size':0.15})

        # Limbs (Simple Walk Cycle)
        w = math.sin(time_val*10)
        add(self.limb, -0.3, -0.5, 0, w, RED)
        add(self.limb, 0.3, -0.5, 0, -w, RED)
        add(self.limb_b, -0.2, -1.0, 0, -w, BLUE)
        add(self.limb_b, 0.2, -1.0, 0, w, BLUE)
        return render_list

# --- RENDERER ---
def render_scene(screen, render_list):
    visible = [p for p in render_list if p['z'] + VIEW_DIST > 0.5]
    visible.sort(key=lambda p: p['z'], reverse=True)
    
    for item in visible:
        if item['type'] == 'poly':
            p2d = []
            for p3d in item['points_3d']:
                proj = project(p3d[0], p3d[1], p3d[2], WIDTH, HEIGHT)
                if proj: p2d.append((proj[0], proj[1]))
            if len(p2d) > 2:
                pygame.draw.polygon(screen, item['color'], p2d)
                pygame.draw.polygon(screen, (0,0,0,50), p2d, 1)
        elif item['type'] == 'sprite':
            proj = project(item['pos'][0], item['pos'][1], item['pos'][2], WIDTH, HEIGHT)
            if proj:
                size = int(item['size'] * SCALE * proj[2])
                if size > 0:
                    img = pygame.transform.scale(item['img'], (size, size))
                    screen.blit(img, (proj[0]-size//2, proj[1]-size//2))

# --- MAIN ---
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("SM64: PEACH CASTLE LOADING...")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 30, bold=True)

    mario_head = MarioHead()
    mario_actor = MarioActor()
    castle = Castle()
    
    game_state = STATE_MENU
    time_val = 0
    cam_angle_y = 0
    
    running = True
    while running:
        mx, my = pygame.mouse.get_pos()
        norm_mx, norm_my = (mx - WIDTH/2)/(WIDTH/2), (my - HEIGHT/2)/(HEIGHT/2)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    if game_state == STATE_MENU: game_state = STATE_GAME

        keys = pygame.key.get_pressed()
        if game_state == STATE_GAME:
            if keys[pygame.K_LEFT]: cam_angle_y += 0.05
            if keys[pygame.K_RIGHT]: cam_angle_y -= 0.05
            # Tank controls for Mario
            rad = mario_actor.yaw
            if keys[pygame.K_w]: 
                mario_actor.pos.z -= math.cos(rad) * 0.1
                mario_actor.pos.x -= math.sin(rad) * 0.1
            if keys[pygame.K_s]: 
                mario_actor.pos.z += math.cos(rad) * 0.1
                mario_actor.pos.x += math.sin(rad) * 0.1
            if keys[pygame.K_a]: mario_actor.yaw -= 0.1
            if keys[pygame.K_d]: mario_actor.yaw += 0.1

        time_val += 0.05
        screen.fill(BLACK)
        
        if game_state == STATE_MENU:
            screen.fill(SKY_BLUE)
            render_scene(screen, mario_head.get_render_data(norm_mx, norm_my, time_val))
            
            txt = font.render("PRESS START", True, ORANGE)
            screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT - 80))
            
        elif game_state == STATE_GAME:
            screen.fill(SKY_CYAN)
            
            # Draw Green Floor Ground (Infinite Plane illusion)
            pygame.draw.rect(screen, GREEN, (0, HEIGHT/2, WIDTH, HEIGHT/2))
            
            # Render List: Castle -> Mario
            game_objs = []
            game_objs.extend(castle.get_render_data(cam_angle_y))
            game_objs.extend(mario_actor.get_render_data(time_val, cam_angle_y))
            
            render_scene(screen, game_objs)
            
            # HUD
            hud = font.render("- x 0", True, YELLOW)
            screen.blit(hud, (WIDTH - 80, 20))

        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()

if __name__ == "__main__":
    main()
