import pygame
import random

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
PLAYER_RADIUS = 10
BALL_RADIUS = 8
PLAYER_SPEED = 5
BALL_SPEED = 3

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Initialize screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Electronic Foosball")

clock = pygame.time.Clock()

class Rod:
    def __init__(self, x, y_positions, color, left_key, right_key):
        self.x = x
        self.y_positions = y_positions
        self.color = color
        self.left_key = left_key
        self.right_key = right_key
        self.speed = PLAYER_SPEED

    def move_left(self):
        self.x -= self.speed
        if self.x < 50:
            self.x = 50

    def move_right(self):
        self.x += self.speed
        if self.x > WIDTH - 50:
            self.x = WIDTH - 50

    def draw(self, surface):
        for y in self.y_positions:
            pygame.draw.circle(surface, self.color, (self.x, y), PLAYER_RADIUS)

class Ball:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.dx = random.choice([-BALL_SPEED, BALL_SPEED])
        self.dy = random.choice([-BALL_SPEED, BALL_SPEED])
        self.radius = BALL_RADIUS

    def update(self):
        self.x += self.dx
        self.y += self.dy

    def draw(self, surface):
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.radius)

# Create game objects
left_defensive = Rod(100, [200, 300, 400], RED, pygame.K_a, pygame.K_d)
left_offensive = Rod(200, [200, 300, 400], RED, pygame.K_w, pygame.K_s)
right_defensive = Rod(700, [200, 300, 400], BLUE, pygame.K_LEFT, pygame.K_RIGHT)
right_offensive = Rod(600, [200, 300, 400], BLUE, pygame.K_UP, pygame.K_DOWN)
ball = Ball()

# Goals
left_goal = pygame.Rect(0, 200, 50, 200)
right_goal = pygame.Rect(WIDTH - 50, 200, 50, 200)

# Score
left_score = 0
right_score = 0
font = pygame.font.Font(None, 74)

def check_collision(ball, player_x, player_y):
    distance = ((ball.x - player_x)**2 + (ball.y - player_y)**2)**0.5
    return distance < ball.radius + PLAYER_RADIUS

running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Move rods
    keys = pygame.key.get_pressed()
    
    if keys[left_defensive.left_key]:
        left_defensive.move_left()
    if keys[left_defensive.right_key]:
        left_defensive.move_right()
    
    if keys[left_offensive.left_key]:
        left_offensive.move_left()
    if keys[left_offensive.right_key]:
        left_offensive.move_right()
    
    if keys[right_defensive.left_key]:
        right_defensive.move_left()
    if keys[right_defensive.right_key]:
        right_defensive.move_right()
    
    if keys[right_offensive.left_key]:
        right_offensive.move_left()
    if keys[right_offensive.right_key]:
        right_offensive.move_right()

    # Update ball position
    ball.update()

    # Check collisions with walls
    if ball.y - ball.radius <= 0 or ball.y + ball.radius >= HEIGHT:
        ball.dy *= -1

    # Check goals
    ball_rect = pygame.Rect(ball.x - ball.radius, ball.y - ball.radius, 
                           ball.radius*2, ball.radius*2)
    
    if left_goal.colliderect(ball_rect):
        right_score += 1
        ball.reset()
    elif right_goal.colliderect(ball_rect):
        left_score += 1
        ball.reset()
    else:
        # Check field boundaries
        if ball.x - ball.radius <= 50 or ball.x + ball.radius >= WIDTH - 50:
            ball.dx *= -1

    # Check collisions with players
    rods = [left_defensive, left_offensive, right_defensive, right_offensive]
    for rod in rods:
        for y in rod.y_positions:
            if check_collision(ball, rod.x, y):
                # Simple collision response
                ball.dx *= -1
                ball.dy *= -1

    # Draw everything
    screen.fill(GREEN)
    
    # Draw field
    pygame.draw.rect(screen, WHITE, (0, 0, WIDTH, HEIGHT), 5)
    pygame.draw.rect(screen, RED, left_goal)
    pygame.draw.rect(screen, BLUE, right_goal)
    
    # Draw rods
    for rod in rods:
        rod.draw(screen)
    
    # Draw ball
    ball.draw(screen)
    
    # Draw scores
    text = font.render(str(left_score), True, WHITE)
    screen.blit(text, (WIDTH//4, 10))
    text = font.render(str(right_score), True, WHITE)
    screen.blit(text, (3*WIDTH//4, 10))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
