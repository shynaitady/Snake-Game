import pygame as pg
from time import sleep
import unittest
from random import randrange
from game import *

class MockPygameEvent:
    def __init__(self, event_type, key=None):
        self.type = event_type
        self.key = key

class MockGame:
    def __init__(self):
        pg.init()
        self.WINDOW_SIZE = 800
        self.TILE_SIZE = 50
        self.screen = pg.display.set_mode((self.WINDOW_SIZE, self.WINDOW_SIZE))
        self.score = MockScore()

class MockScore:
    def __init__(self):
        self.score = 0

    def add_score(self, points):
        self.score += points
        
class TestSetup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pg.init()

    @classmethod
    def tearDownClass(cls):
        pg.quit()

class TestSnake(TestSetup):
    def setUp(self):
        self.game = MockGame()  # MockGame now doesn't need to call pg.init()
        self.snake = Snake(self.game)
        self.snake.rect.center = (400, 400)

    def test_move(self):
        self.snake.delta_time = lambda: True  # Force delta_time to always return True
        initial_position = self.snake.rect.center
        self.snake.direction = pg.math.Vector2(50, 0)  # moving right
        self.snake.move()
        self.assertNotEqual(initial_position, self.snake.rect.center)

    def test_eat_food(self):
        self.snake.rect.center = (400, 400)
        food = Food(self.game)
        food.rect.center = (400, 400)
        self.game.food = food
        self.snake.check_food()
        self.assertEqual(self.snake.length, 2)  # Assuming the snake grows by 1
        self.assertEqual(self.game.score.score, 10)  # Assuming each food is worth 10 points

class TestFood(unittest.TestCase):
    def setUp(self):
        self.game = MockGame()
        self.food = Food(self.game)

    def test_food_reaction_normal(self):
        snake = Snake(self.game)
        self.food.react(snake)
        self.assertEqual(snake.length, 2)  # Assuming normal food grows the snake by 1
        self.assertEqual(self.game.score.score, 10)  # Assuming each food is worth 10 points

class TestScore(unittest.TestCase):
    def setUp(self):
        self.game = MockGame()
        self.score = Score(self.game)

    def test_score_addition(self):
        self.score.add_score(10)
        self.assertEqual(self.score.score, 10)

    def test_score_display(self):
        self.score.add_score(20)
        self.score.draw()



if __name__ == '__main__':
    unittest.main()