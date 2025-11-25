#!/usr/bin/env python3
import pygame
import math
import random
import sys

# Initialize Pygame
pygame.init()

# Screen setup
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SUPER MARIO 64 - Pygame Edition")
clock = pygame.time.Clock()

# Colors
SKY_BLUE = (0, 120, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
BROWN = (139, 69, 19)
BLUE = (0, 0, 255)
BEIGE = (255, 220, 150)

# Mario head parameters
head_radius = 80
head_x, head_y = WIDTH // 2, HEIGHT // 2
rotation_angle = 0
stretch_factor = 1.0
dragging = False

# Text setup
title_font = pygame.font.SysFont('Arial', 80, bold=True)
press_font = pygame.font.SysFont('Arial', 36)
blink_timer = 0
show_press_text = True

def draw_mario_head(surface, x, y, radius, rotation, stretch):
    # Draw head (ellipse for stretch effect)
    head_rect = pygame.Rect(x - radius * stretch, y - radius, radius * 2 * stretch, radius * 2)
    pygame.draw.ellipse(surface, BEIGE, head_rect)
    
    # Draw cap (red)
    cap_rect = pygame.Rect(x - radius * 1.1 * stretch, y - radius * 0.7, radius * 2.2 * stretch, radius * 1.3)
    pygame.draw.ellipse(surface, RED, cap_rect)
    
    # Draw eyes
    eye_offset_x = radius * 0.5 * math.cos(rotation) * stretch
    eye_offset_y = radius * 0.5 * math.sin(rotation)
    
    # Left eye
    pygame.draw.circle(surface, WHITE, (int(x - eye_offset_x), int(y - eye_offset_y)), int(radius * 0.3))
    pygame.draw.circle(surface, BLUE, (int(x - eye_offset_x), int(y - eye_offset_y)), int(radius * 0.15))
    pygame.draw.circle(surface, BLACK, (int(x - eye_offset_x), int(y - eye_offset_y)), int(radius * 0.08))
    
    # Right eye
    pygame.draw.circle(surface, WHITE, (int(x + eye_offset_x), int(y - eye_offset_y)), int(radius * 0.3))
    pygame.draw.circle(surface, BLUE, (int(x + eye_offset_x), int(y - eye_offset_y)), int(radius * 0.15))
    pygame.draw.circle(surface, BLACK, (int(x + eye_offset_x), int(y - eye_offset_y)), int(radius * 0.08))
    
    # Draw nose
    nose_x = x + radius * 0.7 * math.cos(rotation) * stretch
    nose_y = y + radius * 0.1 * math.sin(rotation)
    pygame.draw.circle(surface, ORANGE, (int(nose_x), int(nose_y)), int(radius * 0.25))
    
    # Draw mustache
    mustache_y = y + radius * 0.2
    mustache_width = radius * 0.8 * stretch
    mustache_height = radius * 0.2
    
    # Left mustache
    left_mustache = pygame.Rect(
        int(x - mustache_width - radius * 0.1), 
        int(mustache_y), 
        int(mustache_width), 
        int(mustache_height)
    )
    pygame.draw.ellipse(surface, BLACK, left_mustache)
    
    # Right mustache
    right_mustache = pygame.Rect(
        int(x + radius * 0.1), 
        int(mustache_y), 
        int(mustache_width), 
        int(mustache_height)
    )
    pygame.draw.ellipse(surface, BLACK, right_mustache)

def draw_title_screen():
    global blink_timer, show_press_text
    
    # Draw sky background
    screen.fill(SKY_BLUE)
    
    # Draw title
    title_text = title_font.render("SUPER MARIO 64", True, YELLOW)
    title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 4))
    screen.blit(title_text, title_rect)
    
    # Draw blinking "PRESS START" text
    blink_timer += 1
    if blink_timer >= 60:  # Blink every second
        show_press_text = not show_press_text
        blink_timer = 0
    
    if show_press_text:
        press_text = press_font.render("PRESS SPACE TO START", True, WHITE)
        press_rect = press_text.get_rect(center=(WIDTH // 2, HEIGHT * 3 // 4))
        screen.blit(press_text, press_rect)
    
    # Draw Mario head
    draw_mario_head(screen, head_x, head_y, head_radius, rotation_angle, stretch_factor)

def draw_game_screen():
    screen.fill((100, 200, 255))  # Light blue background
    
    # Draw ground
    pygame.draw.rect(screen, (50, 200, 50), (0, HEIGHT - 100, WIDTH, 100))
    
    # Draw platforms
    for i in range(5):
        platform_x = 100 + i * 150
        platform_y = HEIGHT - 200 - i * 50
        pygame.draw.rect(screen, (200, 200, 100), (platform_x, platform_y, 100, 20))
    
    # Draw Mario (simple red square)
    mario_size = 40
    mario_x = WIDTH // 2
    mario_y = HEIGHT - 140
    pygame.draw.rect(screen, RED, (mario_x - mario_size // 2, mario_y - mario_size, mario_size, mario_size))
    
    # Draw eyes on Mario
    pygame.draw.circle(screen, WHITE, (mario_x - 10, mario_y - mario_size + 15), 5)
    pygame.draw.circle(screen, WHITE, (mario_x + 10, mario_y - mario_size + 15), 5)
    pygame.draw.circle(screen, BLACK, (mario_x - 10, mario_y - mario_size + 15), 2)
    pygame.draw.circle(screen, BLACK, (mario_x + 10, mario_y - mario_size + 15), 2)
    
    # Draw cap
    pygame.draw.rect(screen, RED, (mario_x - mario_size // 2, mario_y - mario_size - 10, mario_size, 15))
    
    # Draw instructions
    instr_font = pygame.font.SysFont('Arial', 24)
    instr_text = instr_font.render("Use ARROW KEYS to move, SPACE to jump", True, BLACK)
    screen.blit(instr_text, (20, 20))

# Game states
TITLE_SCREEN = 0
GAME_SCREEN = 1
current_state = TITLE_SCREEN

# Mario position for game screen
mario_pos = [WIDTH // 2, HEIGHT - 140]
mario_velocity = [0, 0]
mario_speed = 5
jump_power = 15
gravity = 0.8
on_ground = False

# Main game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            if current_state == TITLE_SCREEN and event.key == pygame.K_SPACE:
                current_state = GAME_SCREEN
            elif current_state == GAME_SCREEN and event.key == pygame.K_SPACE and on_ground:
                mario_velocity[1] = -jump_power
                on_ground = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if current_state == TITLE_SCREEN:
                # Check if clicking on Mario head for stretch effect
                mouse_x, mouse_y = pygame.mouse.get_pos()
                distance = math.sqrt((mouse_x - head_x)**2 + (mouse_y - head_y)**2)
                if distance <= head_radius:
                    dragging = True
        
        if event.type == pygame.MOUSEBUTTONUP:
            dragging = False
    
    # Update
    if current_state == TITLE_SCREEN:
        rotation_angle += 0.02
        
        # Handle stretching
        if dragging:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            distance = math.sqrt((mouse_x - head_x)**2 + (mouse_y - head_y)**2)
            stretch_factor = max(0.5, min(2.0, distance / head_radius))
        else:
            # Gradually return to normal
            stretch_factor += (1.0 - stretch_factor) * 0.1
    
    elif current_state == GAME_SCREEN:
        # Handle movement
        keys = pygame.key.get_pressed()
        mario_velocity[0] = 0
        
        if keys[pygame.K_LEFT]:
            mario_velocity[0] = -mario_speed
        if keys[pygame.K_RIGHT]:
            mario_velocity[0] = mario_speed
        
        # Apply gravity
        mario_velocity[1] += gravity
        
        # Update position
        mario_pos[0] += mario_velocity[0]
        mario_pos[1] += mario_velocity[1]
        
        # Ground collision
        if mario_pos[1] >= HEIGHT - 140:
            mario_pos[1] = HEIGHT - 140
            mario_velocity[1] = 0
            on_ground = True
        
        # Platform collisions (simple)
        for i in range(5):
            platform_x = 100 + i * 150
            platform_y = HEIGHT - 200 - i * 50
            
            if (mario_pos[0] > platform_x - 20 and mario_pos[0] < platform_x + 120 and
                mario_pos[1] > platform_y - 40 and mario_pos[1] < platform_y and
                mario_velocity[1] > 0):
                mario_pos[1] = platform_y - 40
                mario_velocity[1] = 0
                on_ground = True
        
        # Screen boundaries
        mario_pos[0] = max(20, min(WIDTH - 20, mario_pos[0]))
    
    # Draw
    if current_state == TITLE_SCREEN:
        draw_title_screen()
    elif current_state == GAME_SCREEN:
        draw_game_screen()
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
