# by Giu
# https://github.com/o-giu

import pygame
import random
import sys
from enum import Enum, auto
from typing import Tuple, Optional, Dict, List
from dataclasses import dataclass

@dataclass
class GameConfig:
    WINDOW_SIZE: Tuple[int, int] = (800, 600)
    PADDLE_WIDTH: int = 15
    PADDLE_HEIGHT: int = 90
    BALL_SIZE: int = 15
    PADDLE_SPEED: int = 7
    BALL_SPEED: int = 5
    BALL_MAX_SPEED: int = 15
    SPEED_INCREMENT: float = 0.2
    COLORS: Dict[str, Tuple[int, int, int]] = None
    
    def __post_init__(self):
        self.COLORS = {
            'background': (15, 15, 15),
            'paddle': (200, 200, 200),
            'ball': (255, 255, 255),
            'text': (255, 255, 255),
            'divider': (100, 100, 100)
        }

class Direction(Enum):
    UP = auto()
    DOWN = auto()

class Ball:
    def __init__(self, config: GameConfig):
        self.config = config
        self.x: float = 0
        self.y: float = 0
        self.speed_x: float = 0
        self.speed_y: float = 0
        self.reset()
        
    def reset(self) -> None:
        self.x = self.config.WINDOW_SIZE[0] // 2
        self.y = self.config.WINDOW_SIZE[1] // 2
        self.speed_x = self.config.BALL_SPEED * random.choice([-1, 1])
        self.speed_y = self.config.BALL_SPEED * random.choice([-1, 1])
        
    def move(self) -> None:
        self.x += self.speed_x
        self.y += self.speed_y
        
        if self.y <= 0 or self.y >= self.config.WINDOW_SIZE[1] - self.config.BALL_SIZE:
            self.speed_y *= -1
            
    def increase_speed(self) -> None:
        speed_increment = self.config.SPEED_INCREMENT
        
        new_speed_x = self.speed_x * (1 + speed_increment)
        new_speed_y = self.speed_y * (1 + speed_increment)
        
        if abs(new_speed_x) <= self.config.BALL_MAX_SPEED:
            self.speed_x = new_speed_x
        if abs(new_speed_y) <= self.config.BALL_MAX_SPEED:
            self.speed_y = new_speed_y

class Paddle:
    def __init__(self, is_left: bool, config: GameConfig):
        self.config = config
        self.is_left = is_left
        self.x: float = 0
        self.y: float = 0
        self.reset()
        
    def reset(self) -> None:
        self.y = (self.config.WINDOW_SIZE[1] - self.config.PADDLE_HEIGHT) // 2
        if self.is_left:
            self.x = 50
        else:
            self.x = self.config.WINDOW_SIZE[0] - 50 - self.config.PADDLE_WIDTH
            
    def move(self, direction: Direction) -> None:
        if direction == Direction.UP:
            self.y = max(0, self.y - self.config.PADDLE_SPEED)
        elif direction == Direction.DOWN:
            self.y = min(self.config.WINDOW_SIZE[1] - self.config.PADDLE_HEIGHT, 
                        self.y + self.config.PADDLE_SPEED)
            
    def check_collision(self, ball: Ball) -> bool:
        return (self.x < ball.x + ball.config.BALL_SIZE and
                self.x + self.config.PADDLE_WIDTH > ball.x and
                self.y < ball.y + ball.config.BALL_SIZE and
                self.y + self.config.PADDLE_HEIGHT > ball.y)

@dataclass
class MenuTitle:
    surfaces: List[Tuple[pygame.Surface, int]]
    total_width: int

class Menu:
    def __init__(self, screen: pygame.Surface, font: pygame.font.Font, config: GameConfig):
        self.screen = screen
        self.font = font
        self.config = config
        self.options = ["Single Player", "Two Players", "Quit"]
        self.selected_index = 0
        self.title = self._initialize_title()
    
    def _initialize_title(self) -> MenuTitle:
        title = "Giu - Pong Game v1.0"
        gradient_colors = [
            (255, 255, 255),
            (200, 200, 200),
            (150, 150, 150)
        ]
        
        title_font = pygame.font.Font(None, 72)
        surfaces = []
        total_width = 0
        
        for i, letter in enumerate(title):
            color_idx = (i / (len(title) - 1)) * (len(gradient_colors) - 1)
            base_idx = int(color_idx)
            next_idx = min(base_idx + 1, len(gradient_colors) - 1)
            blend = color_idx - base_idx
            
            color = tuple(
                int(gradient_colors[base_idx][j] * (1 - blend) + 
                    gradient_colors[next_idx][j] * blend)
                for j in range(3)
            )
            
            letter_surface = title_font.render(letter, True, color)
            surfaces.append((letter_surface, total_width))
            total_width += letter_surface.get_width()
        
        return MenuTitle(surfaces=surfaces, total_width=total_width)

    def handle_input(self) -> int:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 2
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_index = (self.selected_index - 1) % len(self.options)
                elif event.key == pygame.K_DOWN:
                    self.selected_index = (self.selected_index + 1) % len(self.options)
                elif event.key == pygame.K_RETURN:
                    return self.selected_index
                elif event.key == pygame.K_ESCAPE:
                    return 2
        return -1

    def draw(self) -> None:
        self.screen.fill(self.config.COLORS['background'])
        
        # Draw title
        title_start_x = (self.config.WINDOW_SIZE[0] - self.title.total_width) // 2
        title_y = 100
        for surface, offset in self.title.surfaces:
            self.screen.blit(surface, (title_start_x + offset, title_y))
        
        # Draw options
        for i, option in enumerate(self.options):
            color = self.config.COLORS['text'] if i == self.selected_index else (100, 100, 100)
            option_text = self.font.render(option, True, color)
            option_rect = option_text.get_rect(center=(self.config.WINDOW_SIZE[0] // 2, 250 + i * 50))
            self.screen.blit(option_text, option_rect)
        
        pygame.display.flip()

class PongAI:
    def __init__(self, config: GameConfig, difficulty: float = 0.5):
        self.config = config
        self.difficulty = difficulty
        self.reaction_delay = 4
        self.frame_counter = 0
        self.target_y = 0
        self.movement_speed_factor = 0.7
    
    def predict_ball_position(self, ball: Ball, paddle: Paddle) -> float:
        if (paddle.is_left and ball.speed_x > 0) or (not paddle.is_left and ball.speed_x < 0):
            return self.config.WINDOW_SIZE[1] / 2 - self.config.PADDLE_HEIGHT / 2
        
        time_to_intercept = abs((paddle.x - ball.x) / ball.speed_x)
        future_y = ball.y + ball.speed_y * time_to_intercept
        
        while future_y < 0 or future_y > self.config.WINDOW_SIZE[1]:
            if future_y < 0:
                future_y = -future_y
            if future_y > self.config.WINDOW_SIZE[1]:
                future_y = 2 * self.config.WINDOW_SIZE[1] - future_y
        
        max_error = self.config.PADDLE_HEIGHT * (1.5 - self.difficulty)
        error = random.uniform(-max_error, max_error)
        
        if random.random() > self.difficulty:
            error *= 2
        
        return min(max(future_y - self.config.PADDLE_HEIGHT / 2 + error, 0),
                  self.config.WINDOW_SIZE[1] - self.config.PADDLE_HEIGHT)

    def update(self, paddle: Paddle, ball: Ball) -> None:
        self.frame_counter += 1
        if self.frame_counter >= self.reaction_delay:
            self.frame_counter = 0
            self.target_y = self.predict_ball_position(ball, paddle)
        
        if abs(paddle.y - self.target_y) > self.config.PADDLE_SPEED:
            if paddle.y < self.target_y:
                paddle.move(Direction.DOWN)
                paddle.y -= (1 - self.movement_speed_factor) * self.config.PADDLE_SPEED
            elif paddle.y > self.target_y:
                paddle.move(Direction.UP)
                paddle.y += (1 - self.movement_speed_factor) * self.config.PADDLE_SPEED

class PauseMenu:
    def __init__(self, screen: pygame.Surface, font: pygame.font.Font, config: GameConfig):
        self.screen = screen
        self.font = font
        self.config = config
        self.options = ["Return to Game", "Back to Menu", "Quit"]
        self.selected_index = 0

    def draw(self) -> None:
        overlay = pygame.Surface(self.config.WINDOW_SIZE)
        overlay.fill((0, 0, 0))
        overlay.set_alpha(128)
        self.screen.blit(overlay, (0, 0))
        
        pause_text = self.font.render("Paused", True, self.config.COLORS['text'])
        pause_rect = pause_text.get_rect(center=(self.config.WINDOW_SIZE[0] // 2, 100))
        self.screen.blit(pause_text, pause_rect)

        for i, option in enumerate(self.options):
            color = self.config.COLORS['text'] if i == self.selected_index else (100, 100, 100)
            option_text = self.font.render(option, True, color)
            option_rect = option_text.get_rect(center=(self.config.WINDOW_SIZE[0] // 2, 200 + i * 50))
            self.screen.blit(option_text, option_rect)

        pygame.display.flip()

    def handle_input(self) -> int:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 2
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_index = (self.selected_index - 1) % len(self.options)
                elif event.key == pygame.K_DOWN:
                    self.selected_index = (self.selected_index + 1) % len(self.options)
                elif event.key == pygame.K_RETURN:
                    return self.selected_index
                elif event.key == pygame.K_ESCAPE:
                    return 0
        return -1

class GameOver:
    def __init__(self, screen: pygame.Surface, font: pygame.font.Font, config: GameConfig, 
                 winner: str, final_score: Tuple[int, int]):
        self.screen = screen
        self.font = font
        self.config = config
        self.winner = winner
        self.final_score = final_score
        self.options = ["Play Again", "Main Menu", "Quit"]
        self.selected_index = 0
        self.title_font = pygame.font.Font(None, 72)

    def draw(self) -> None:
        self.screen.fill(self.config.COLORS['background'])
        
        game_over_text = self.title_font.render(f"{self.winner} Wins!", True, (255, 255, 255))
        game_over_rect = game_over_text.get_rect(center=(self.config.WINDOW_SIZE[0] // 2, 100))
        self.screen.blit(game_over_text, game_over_rect)
        
        score_text = self.font.render(f"Final Score: {self.final_score[0]} - {self.final_score[1]}", 
                                    True, self.config.COLORS['text'])
        score_rect = score_text.get_rect(center=(self.config.WINDOW_SIZE[0] // 2, 180))
        self.screen.blit(score_text, score_rect)

        for i, option in enumerate(self.options):
            color = self.config.COLORS['text'] if i == self.selected_index else (100, 100, 100)
            option_text = self.font.render(option, True, color)
            option_rect = option_text.get_rect(center=(self.config.WINDOW_SIZE[0] // 2, 280 + i * 50))
            self.screen.blit(option_text, option_rect)

        pygame.display.flip()

    def handle_input(self) -> int:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 2
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_index = (self.selected_index - 1) % len(self.options)
                elif event.key == pygame.K_DOWN:
                    self.selected_index = (self.selected_index + 1) % len(self.options)
                elif event.key == pygame.K_RETURN:
                    return self.selected_index
                elif event.key == pygame.K_ESCAPE:
                    return 1
        return -1

class PongGame:
    def __init__(self):
        if not pygame.get_init():
            pygame.init()
                
        self.config = GameConfig()
        self.screen = pygame.display.set_mode(self.config.WINDOW_SIZE)
        pygame.display.set_caption("Giu - Pong Game v1.0")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        
        self.left_paddle = Paddle(True, self.config)
        self.right_paddle = Paddle(False, self.config)
        self.ball = Ball(self.config)
        
        self.score_left = 0
        self.score_right = 0
        self.single_victories_left = 0
        self.single_victories_right = 0
        self.multi_victories_left = 0
        self.multi_victories_right = 0
        
        self.ai_difficulty = 0.5
        self.ai = PongAI(self.config, difficulty=self.ai_difficulty)
        self.game_mode: Optional[str] = None

    def draw(self) -> None:
        self.screen.fill(self.config.COLORS['background'])
        
        # Draw center line
        for y in range(0, self.config.WINDOW_SIZE[1], 30):
            pygame.draw.rect(self.screen, self.config.COLORS['divider'],
                           (self.config.WINDOW_SIZE[0] // 2 - 5, y, 10, 15))
        
        # Draw paddles
        pygame.draw.rect(self.screen, self.config.COLORS['paddle'],
                        (self.left_paddle.x, self.left_paddle.y,
                         self.config.PADDLE_WIDTH, self.config.PADDLE_HEIGHT))
        pygame.draw.rect(self.screen, self.config.COLORS['paddle'],
                        (self.right_paddle.x, self.right_paddle.y,
                         self.config.PADDLE_WIDTH, self.config.PADDLE_HEIGHT))
        
        # Draw ball
        pygame.draw.rect(self.screen, self.config.COLORS['ball'],
                        (self.ball.x, self.ball.y,
                         self.config.BALL_SIZE, self.config.BALL_SIZE))
        
        # Draw current game scores
        score_left = self.font.render(str(self.score_left), True, self.config.COLORS['text'])
        score_right = self.font.render(str(self.score_right), True, self.config.COLORS['text'])
        
        self.screen.blit(score_left, (self.config.WINDOW_SIZE[0] // 4, 20))
        self.screen.blit(score_right, (3 * self.config.WINDOW_SIZE[0] // 4, 20))
        
        # Draw victory counts based on game mode
        if self.game_mode == "single":
            victories_text = self.font.render(
                f'Wins (Single): {self.single_victories_left} x {self.single_victories_right}', 
                True, self.config.COLORS['text'])
        else:
            victories_text = self.font.render(
                f'Wins (Multi): {self.multi_victories_left} x {self.multi_victories_right}', 
                True, self.config.COLORS['text'])
        
        victories_rect = victories_text.get_rect(center=(self.config.WINDOW_SIZE[0] // 2, 20))
        self.screen.blit(victories_text, victories_rect)
        
        pygame.display.flip()

    def handle_input(self) -> str:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "pause"
        
        keys = pygame.key.get_pressed()
        
        if self.game_mode == "single":
            # In single player mode, human player uses arrow keys to control the left paddle.
            if keys[pygame.K_UP]:
                self.left_paddle.move(Direction.UP)
            if keys[pygame.K_DOWN]:
                self.left_paddle.move(Direction.DOWN)
        else:  # two_players
            # In two player mode:
            # - Player 1 (left) uses the arrow keys
            if keys[pygame.K_UP]:
                self.left_paddle.move(Direction.UP)
            if keys[pygame.K_DOWN]:
                self.left_paddle.move(Direction.DOWN)
            # - Player 2 (right) uses W/S
            if keys[pygame.K_w]:
                self.right_paddle.move(Direction.UP)
            if keys[pygame.K_s]:
                self.right_paddle.move(Direction.DOWN)
        
        return "continue"

    def update(self) -> bool:
        self.ball.move()

        # Updates AI if in single player mode (now on right paddle)
        if self.game_mode == "single":
            self.ai.update(self.right_paddle, self.ball)
        
        # Check paddle collisions
        if self.left_paddle.check_collision(self.ball):
            self.ball.x = self.left_paddle.x + self.config.PADDLE_WIDTH
            self.ball.speed_x *= -1
            self.ball.increase_speed()
        
        if self.right_paddle.check_collision(self.ball):
            self.ball.x = self.right_paddle.x - self.config.BALL_SIZE
            self.ball.speed_x *= -1
            self.ball.increase_speed()
        
        # Check scoring
        if self.ball.x <= 0:
            self.score_right += 1
            if self.score_right >= 11:  # Win condition
                if self.game_mode == "single":
                    self.single_victories_right += 1
                else:
                    self.multi_victories_right += 1
                return False
            self.ball.reset()
        elif self.ball.x >= self.config.WINDOW_SIZE[0] - self.config.BALL_SIZE:
            self.score_left += 1
            if self.score_left >= 11:  # Win condition
                if self.game_mode == "single":
                    self.single_victories_left += 1
                else:
                    self.multi_victories_left += 1
                return False
            self.ball.reset()
            
        return True

    def reset_game(self) -> None:
        self.score_left = 0
        self.score_right = 0
        self.left_paddle.reset()
        self.right_paddle.reset()
        self.ball.reset()

    def run(self) -> None:
        try:
            while True:
                # Main menu loop
                menu = Menu(self.screen, self.font, self.config)
                menu_running = True
                while menu_running:
                    menu.draw()
                    selection = menu.handle_input()
                    if selection == 0:  # Single Player
                        self.game_mode = "single"
                        menu_running = False
                    elif selection == 1:  # Two Players
                        self.game_mode = "two_players"
                        menu_running = False
                    elif selection == 2:  # Quit
                        return
                
                # Game loop
                self.reset_game()
                game_running = True
                
                while game_running:
                    input_result = self.handle_input()
                    
                    if input_result == "quit":
                        return
                    elif input_result == "pause":
                        pause_menu = PauseMenu(self.screen, self.font, self.config)
                        paused = True
                        while paused:
                            pause_menu.draw()
                            pause_selection = pause_menu.handle_input()
                            if pause_selection == 0:  # Return to Game
                                paused = False
                            elif pause_selection == 1:  # Back to Menu
                                game_running = False
                                paused = False
                            elif pause_selection == 2:  # Quit
                                return
                    
                    if not game_running:  # Skip the rest if going back to menu
                        break
                    
                    if not self.update():
                        # Game Over screen
                        winner = "Left Player" if self.score_left >= 11 else "Right Player"
                        game_over = GameOver(self.screen, self.font, self.config, 
                                        winner, (self.score_left, self.score_right))
                        game_over_running = True
                        
                        while game_over_running:
                            game_over.draw()
                            game_over_selection = game_over.handle_input()
                            
                            if game_over_selection == 0:  # Play Again
                                self.reset_game()
                                game_over_running = False
                            elif game_over_selection == 1:  # Main Menu
                                game_running = False
                                game_over_running = False
                            elif game_over_selection == 2:  # Quit
                                return
                        continue
                    
                    self.draw()
                    self.clock.tick(60)  # 60 FPS
                    
        finally:
            pygame.quit()

if __name__ == "__main__":
    try:
        game = PongGame()
        game.run()
    except Exception as e:
        import traceback
        error_msg = f"An error occurred:\n{str(e)}\n\n{traceback.format_exc()}"
        print(error_msg)
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, error_msg, "Error", 0)
        except:
            input("Press Enter to exit...")
    finally:
        pygame.quit()
