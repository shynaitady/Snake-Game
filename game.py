import pygame as pg
from time import sleep
import unittest
import sys
import random
from random import randrange
from abc import ABC, abstractmethod
import os
vec2 = pg.math.Vector2
red = (255,0,0)
blue = (0,0,255)
class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]
    
class GameObject(ABC):
    def __init__(self, game):
        self.game = game
        self.size = game.TILE_SIZE
        self.rect = pg.rect.Rect([0, 0, self.size - 2, self.size - 2])
        self.rect.center = self.get_random_position()

    def get_random_position(self):
        range = self.size // 2, self.game.WINDOW_SIZE - self.size // 2, self.size
        return [randrange(*range), randrange(*range)]

    @abstractmethod
    def draw(self):
        """ Draw the object on the game's screen. Must be overridden by subclasses. """
        pass

class Snake(GameObject):
    def __init__(self, game):
        super().__init__(game)
        self.direction = vec2(0, 0)
        self.step_delay = 100  # milliseconds
        self.time = 0
        self.point = 10
        self.score = 0
        self.length = 1
        self.segments = []
        self.directions = {pg.K_w: 1, pg.K_s: 1, pg.K_a: 1, pg.K_d: 1, pg.K_UP: 1, pg.K_DOWN: 1, pg.K_LEFT: 1, pg.K_RIGHT: 1}

    def control(self, event):
        if event.type == pg.KEYDOWN:
            if (event.key == pg.K_w or event.key == pg.K_UP) and self.directions[pg.K_w] and self.directions[pg.K_UP]:
                self.direction = vec2(0, -self.size)
                self.directions = {key: (key in [pg.K_w, pg.K_a, pg.K_d, pg.K_UP, pg.K_LEFT, pg.K_RIGHT]) for key in self.directions}

            if (event.key == pg.K_s or event.key == pg.K_DOWN) and self.directions[pg.K_s] and self.directions[pg.K_DOWN]:
                self.direction = vec2(0, self.size)
                self.directions = {key: (key in [pg.K_s, pg.K_a, pg.K_d, pg.K_DOWN, pg.K_LEFT, pg.K_RIGHT]) for key in self.directions}

            if (event.key == pg.K_a or event.key == pg.K_LEFT) and self.directions[pg.K_a] and self.directions[pg.K_LEFT]:
                self.direction = vec2(-self.size, 0)
                self.directions = {key: (key in [pg.K_w, pg.K_s, pg.K_a, pg.K_LEFT, pg.K_UP, pg.K_DOWN]) for key in self.directions}

            if (event.key == pg.K_d or event.key == pg.K_RIGHT) and self.directions[pg.K_d] and self.directions[pg.K_RIGHT]:
                self.direction = vec2(self.size, 0)
                self.directions = {key: (key in [pg.K_w, pg.K_s, pg.K_d, pg.K_RIGHT, pg.K_UP, pg.K_DOWN]) for key in self.directions}

    def delta_time(self):
        time_now = pg.time.get_ticks()
        if time_now - self.time > self.step_delay:
            self.time = time_now
            return True
        return False
    
    def check_borders(self):
        if self.rect.left < 0 or self.rect.right > self.game.WINDOW_SIZE or self.rect.top < 0 or self.rect.bottom > self.game.WINDOW_SIZE:
            self.game.end_game()

    def check_selfeating(self):
        if len(self.segments) != len(set(segment.center for segment in self.segments)):
            self.game.end_game()
            

    def check_food(self):
        if self.rect.center == self.game.food.rect.center:
            self.game.food.react(self)  
            if random.random() < 0.3:
                self.game.food = Food(self.game, 'bonus')
            else:
                self.game.food = Food(self.game) 
    def move(self):
        if self.delta_time():
            self.rect.move_ip(self.direction)
            self.segments.append(self.rect.copy())
            self.segments = self.segments[-self.length:]


    def draw(self):
        [pg.draw.rect(self.game.screen, 'green', segment) for segment in self.segments]

class Food(GameObject):
    def __init__(self, game, food_type='normal'):
        super().__init__(game)
        self.food_type = food_type

    def draw(self):
        if self.food_type == 'normal':
            pg.draw.rect(self.game.screen, red, self.rect)
        elif self.food_type == 'bonus':
            pg.draw.rect(self.game.screen, blue, self.rect)

    def react(self, snake):
        if self.food_type == 'normal':
            snake.length += 1
            snake.game.score.add_score(10)
        elif self.food_type == 'bonus':
            snake.length += 2
            snake.game.score.add_score(20)


class Score:
    def __init__(self, game):
        self.game = game
        self.font = pg.font.Font(None, 36)
        self.score = 0 


    def add_score(self, points):
        self.score += points

    def draw(self):
        score_text = f'Score: {self.score}'
        score_surface = self.font.render(score_text, True, pg.Color('white'))
        self.game.screen.blit(score_surface, (10, 10))

class Leaderboard(metaclass=Singleton):
    def __init__(self):
        self.file_path = "scores.txt"
        self.scores = self.load_scores()

    def load_scores(self):
        if not os.path.exists(self.file_path):
            return []
        with open(self.file_path, "r") as file:
            scores = file.readlines()
        scores = [int(score.strip()) for score in scores if score.strip().isdigit()]
        scores.sort(reverse=True)
        return scores[:5]  

    def save_score(self, score):
        self.scores.append(score)
        self.scores.sort(reverse=True)
        self.scores = self.scores[:5]  
        with open(self.file_path, "w") as file:
            for score in self.scores:
                file.write(f"{score}\n")

    def clear_scores(self):
        self.scores = []
        with open(self.file_path, "w") as file:
            file.truncate()

    def get_top_scores(self):
        return self.scores
class Game:
    def __init__(self):
        pg.init()
        self.WINDOW_SIZE = 800
        self.TILE_SIZE = 50
        self.screen = pg.display.set_mode([self.WINDOW_SIZE] * 2)
        self.clock = pg.time.Clock()
        self.running = True
        self.score = Score(self)
        self.new_game()

    def draw_grid(self):
        [pg.draw.line(self.screen, [50] * 3, (x, 0), (x, self.WINDOW_SIZE))
                                             for x in range(0, self.WINDOW_SIZE, self.TILE_SIZE)]
        [pg.draw.line(self.screen, [50] * 3, (0, y), (self.WINDOW_SIZE, y))
                                             for y in range(0, self.WINDOW_SIZE, self.TILE_SIZE)]

    def new_game(self):
        self.snake = Snake(self)
        if random.random() < 0.3:
            self.food = Food(self, 'bonus')
        else:
            self.food = Food(self)
        self.score.score = 0
    def update(self):
        self.snake.check_borders()
        self.snake.check_food()
        self.snake.check_selfeating()
        self.snake.move()  
        pg.display.flip()
        self.clock.tick(60)

    def draw(self):
        self.screen.fill('black')
        self.draw_grid()
        self.food.draw()
        self.snake.draw()
        self.score.draw()

    def run(self):
        self.running = True
        while self.running:
            self.check_event()
            self.update()
            self.draw()
            pg.display.flip()
            self.clock.tick(60)
        return self.score.score

    def check_event(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False  
                pg.quit()
                sys.exit()
            self.snake.control(event)
    def end_game(self):
        leaderboard = Leaderboard()
        leaderboard.save_score(self.score.score)
        self.running = False
    def save_score(self, score):
        with open("scores.txt", "a") as file:
            file.write(f"{score}\n") 
class Menu:
    def __init__(self) -> None:
        pg.init()
        self.screen = pg.display.set_mode((800, 800))
        self.font = pg.font.Font(None, 36)
        pg.display.set_caption("Game Menu")
        self.GREEN = (0, 255, 0)
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GREY = (200, 200, 200)
        self.last_score = None

    def load_scores(self):
        if not os.path.exists("scores.txt"):
            return []
        with open("scores.txt", "r") as file:
            scores = file.readlines()
        scores = [int(score.strip()) for score in scores if score.strip().isdigit()]
        scores.sort(reverse=True)
        return scores[:5]  
    def draw_leaderboard(self):
        leaderboard = Leaderboard()
        running = True
        while running:
            for event in pg.event.get():
                if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                    running = False
                elif event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()

            self.screen.fill(self.GREEN)
            scores = leaderboard.get_top_scores()
            title_text = "Leaderboard - Top 5 Scores"
            self.draw_text_with_border(title_text, self.font, 400, 200, self.WHITE, self.BLACK, 2)

            for i, score in enumerate(scores):
                score_text = f"{i + 1}. {score}"
                self.draw_text_with_border(score_text, self.font, 400, 300 + i * 50, self.WHITE, self.BLACK, 2)

            if self.draw_button("Clear Scores", 250, 550, 300, 50, self.GREY, self.WHITE):
                leaderboard.clear_scores()  
                scores = leaderboard.get_top_scores()  

            instruction_text = "Press ESC to return to menu"
            self.draw_text_with_border(instruction_text, self.font, 400, 700, self.WHITE, self.BLACK, 1)

            pg.display.flip()
    def draw_button(self, text, x, y, w, h, active_color, inactive_color):
        mouse = pg.mouse.get_pos()
        click = pg.mouse.get_pressed()
        if x + w > mouse[0] > x and y + h > mouse[1] > y:
            pg.draw.rect(self.screen, active_color, (x, y, w, h))
            if click[0] == 1:
                return True
        else:
            pg.draw.rect(self.screen, inactive_color, (x, y, w, h))

        text_surf = self.font.render(text, True, self.BLACK)
        text_rect = text_surf.get_rect()
        text_rect.center = ((x + (w // 2)), (y + (h // 2)))
        self.screen.blit(text_surf, text_rect)
        return False

    def draw_text_with_border(self, text, font, x, y, text_color, border_color, border_width):
        text_surface = font.render(text, True, text_color)
        text_rect = text_surface.get_rect(center=(x, y))

        for dx, dy in [(-border_width, -border_width), (border_width, -border_width),
                       (-border_width, border_width), (border_width, border_width)]:
            border_surface = font.render(text, True, border_color)
            border_rect = border_surface.get_rect(center=(x + dx, y + dy))
            self.screen.blit(border_surface, border_rect)
        self.screen.blit(text_surface, text_rect)

    def save_score(self, score):
        with open("scores.txt", "a") as file:
            file.write(f"{score}\n")


    def draw_score(self):
        if self.last_score is not None:
            score_text = f"Last Score: {self.last_score}"
            self.draw_text_with_border(score_text, self.font, 400, 250, self.WHITE, self.BLACK, 2)



    def main_menu(self):
        while True:
            self.screen.fill(self.GREEN)
            if self.draw_button("Play", 250, 300, 300, 50, self.GREY, self.WHITE):
                game = Game()
                self.last_score = game.run()  
            if self.draw_button("Leaderboard", 250, 400, 300, 50, self.GREY, self.WHITE):
                self.draw_leaderboard()
            if self.draw_button("Quit", 250, 500, 300, 50, self.GREY, self.WHITE):
                pg.quit()
                sys.exit()

            self.draw_score()  

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()

            pg.display.flip()


if __name__ == '__main__':

    menu = Menu()
    menu.main_menu()