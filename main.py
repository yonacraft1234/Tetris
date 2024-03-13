import random
import sys
import pygame

# Initialize Pygame
pygame.init()
pygame.font.init()
font = pygame.font.Font(None, 36)
game_over_font = pygame.font.Font(None, 48)
credits_font = pygame.font.Font(None, 24)

# Define constants
SCREEN_WIDTH, SCREEN_HEIGHT = 350, 600
BLOCK_SIZE = 30
BOARD_WIDTH, BOARD_HEIGHT = 10, 20
TARGET_FPS = 60
FPS = 2
BLOCK_MOVE_INTERVAL = 1000
HORIZONTAL_MOVE_INTERVAL = 100
VERTICAL_MOVE_INTERVAL = 50

INITIAL_MOVE_INTERVAL = 100
ACCELERATED_MOVE_INTERVAL = -5

# Define colors
WHITE = (255, 255, 255)
GREY = (128, 128, 128)
LIGHT_GREY = (192, 192, 192)

COLORS = [
    (0, 255, 255), (255, 255, 0), (128, 0, 128),
    (0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 127, 0)
]

# Tetromino shapes
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[0, 1, 0], [1, 1, 1]],  # T
    [[0, 1, 1], [1, 1, 0]],  # S
    [[1, 1, 0], [0, 1, 1]],  # Z
    [[0, 0, 1], [1, 1, 1]],  # J
    [[1, 0, 0], [1, 1, 1]]  # L
]

# Associate each Tetromino shape with a specific color
TETROMINO_COLORS = {
    'I': 0,  # Cyan
    'O': 1,  # Yellow
    'T': 2,  # Purple
    'S': 3,  # Green
    'Z': 4,  # Red
    'J': 5,  # Blue
    'L': 6,  # Orange
}

# Define the screen object
PREVIEW_WIDTH = 4
WINDOW_WIDTH = SCREEN_WIDTH + (PREVIEW_WIDTH * BLOCK_SIZE)
WINDOW_HEIGHT = SCREEN_HEIGHT

# Define the screen object with the new window size
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('Tetris')


def is_mouse_over_area(area_rect):
    # Check if the mouse cursor is over the specified area.
    mouse_x, mouse_y = pygame.mouse.get_pos()
    return area_rect.collidepoint(mouse_x, mouse_y)


class Tetris:
    def __init__(self, width=10, height=20):
        self.width = width
        self.height = height
        self.board = [[0] * width for _ in range(height)]
        self.game_over = False
        self.score = 0
        self.current_piece = None
        self.next_piece = self.new_piece()
        self.life_saver_piece = self.new_piece()
        self.spawn_piece()
        self.block_move_timer = 0
        self.total_lines_cleared = 0
        self.block_move_interval = 1000

    def new_piece(self):
        # Tetromino shapes
        shapes = {
            'I': [[1, 1, 1, 1]],
            'O': [[1, 1], [1, 1]],
            'T': [[0, 1, 0], [1, 1, 1]],
            'S': [[0, 1, 1], [1, 1, 0]],
            'Z': [[1, 1, 0], [0, 1, 1]],
            'J': [[0, 0, 1], [1, 1, 1]],
            'L': [[1, 0, 0], [1, 1, 1]]
        }
        tetromino_type = random.choice(list(shapes.keys()))
        color_index = TETROMINO_COLORS[tetromino_type]
        return (shapes[tetromino_type], color_index + 1)

    def spawn_piece(self):
        self.current_piece = self.next_piece
        self.next_piece = self.new_piece()
        self.piece_x = self.width // 2 - len(self.current_piece[0][0]) // 2
        self.piece_y = 0

        if not self.can_move(0, 0):
            self.game_over = True

    def calculate_ghost_piece_position(self):
        ghost_y = self.piece_y
        while self.can_move(0, 1, ghost_y):
            ghost_y += 1
        return ghost_y

    def can_move(self, dx, dy, piece_y=None):
        if piece_y is None:
            piece_y = self.piece_y
        piece_shape, _ = self.current_piece
        for y, row in enumerate(piece_shape):
            for x, block in enumerate(row):
                if block:
                    new_x = self.piece_x + x + dx
                    new_y = piece_y + y + dy
                    if (new_x < 0 or new_x >= self.width or
                            new_y < 0 or new_y >= self.height or
                            self.board[new_y][new_x]):
                        return False
        return True

    def lock_piece(self):
        piece_shape, color = self.current_piece
        for y, row in enumerate(piece_shape):
            for x, block in enumerate(row):
                if block:
                    if (
                            self.piece_x + x < 0 or
                            self.piece_x + x >= self.width or
                            self.piece_y + y >= self.height or
                            self.board[self.piece_y + y][self.piece_x + x] != 0
                    ):
                        # The piece is outside the board or collides with another piece
                        self.game_over = True
                        return
                    self.board[self.piece_y + y][self.piece_x + x] = color
        self.clear_lines()
        self.spawn_piece()

    def clear_lines(self):
        new_board = [row for row in self.board if any(cell == 0 for cell in row)]
        lines_cleared = self.height - len(new_board)

        # Increase the score based on the number of lines cleared
        self.score += lines_cleared

        # Update the total number of lines cleared
        self.total_lines_cleared += lines_cleared

        # Increase speed every 2 lines cleared
        if self.total_lines_cleared >= 1:
            global BLOCK_MOVE_INTERVAL
            BLOCK_MOVE_INTERVAL = max(100, BLOCK_MOVE_INTERVAL - 50)  # Decrease interval, minimum limit 100
            self.total_lines_cleared = 0  # Reset the counter

        # Fill the cleared lines with new empty lines
        for _ in range(lines_cleared):
            new_board.insert(0, [0 for _ in range(self.width)])
        self.board = new_board

    def rotate_piece(self):
        piece_shape, color = self.current_piece
        new_shape = list(zip(*piece_shape[::-1]))  # This creates the rotated shape

        # Perform bounds checks and shift piece into the board if it's out of bounds
        for y, row in enumerate(new_shape):
            for x, block in enumerate(row):
                if block:
                    new_x = self.piece_x + x
                    new_y = self.piece_y + y
                    if (new_x < 0 or new_x >= self.width or new_y >= self.height or self.board[new_y][new_x] != 0):
                        # Attempt to shift the piece into a valid position
                        if new_x < 0:
                            self.piece_x += 1
                        elif new_x >= self.width:
                            self.piece_x -= 1

        # After attempting to shift, check if the new position is valid
        if self.piece_x < 0 or self.piece_x + len(new_shape[0]) > self.width:
            # The piece is still out of bounds, so cancel the rotation
            return

        # Now we need to check if the new rotated position is overlapping with existing blocks
        for y, row in enumerate(new_shape):
            for x, block in enumerate(row):
                if block:
                    new_x = self.piece_x + x
                    new_y = self.piece_y + y
                    if self.board[new_y][new_x] != 0:
                        # There is a collision with existing blocks, so cancel the rotation
                        return

        self.current_piece = (new_shape, color)

    def hard_drop(self):
        while self.can_move(0, 1):
            self.piece_y += 1
        self.lock_piece()

    def move(self, dx, dy):
        if self.can_move(dx, dy):
            self.piece_x += dx
            self.piece_y += dy

    def step(self):
        if not self.game_over:
            if not self.can_move(0, 1):
                self.lock_piece()
            else:
                self.piece_y += 1

    def swap_life_saver(self):
        if not self.life_saver_piece:
            self.life_saver_piece = self.current_piece
            self.spawn_piece()
        else:
            # If the position where the current piece is to be swapped isn't free, do not swap
            if not self.can_move(0, 0, piece_y=0):
                return
            self.current_piece, self.life_saver_piece = self.life_saver_piece, self.current_piece
            self.piece_x = self.width // 2 - len(self.current_piece[0][0]) // 2
            self.piece_y = 0

    def draw(self):
        screen.fill(WHITE)

        # Render the "Created by yonacraft1234" text once
        created_by_text = credits_font.render('Created By', True, (0, 0, 0))
        yonacraft1234_text = credits_font.render('yonacraft1234', True, (0, 0, 0))
        created_by_rect = created_by_text.get_rect(bottomright=(WINDOW_WIDTH - 25, WINDOW_HEIGHT - 30))
        yonacraft1234_rect = yonacraft1234_text.get_rect(bottomright=(WINDOW_WIDTH - 10, WINDOW_HEIGHT - 10))
        screen.blit(created_by_text, created_by_rect)
        screen.blit(yonacraft1234_text, yonacraft1234_rect)

        # Render the score text
        score_text = font.render('Score: ' + str(self.score), True, (0, 0, 0))
        score_rect = score_text.get_rect(topleft=(SCREEN_WIDTH - 15, 10))
        screen.blit(score_text, score_rect)

        # Draw the Tetris board with light grey lines for the grid
        for x in range(self.width):
            for y in range(self.height):
                rect = pygame.Rect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
                color = COLORS[self.board[y][x] - 1] if self.board[y][x] else WHITE
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, LIGHT_GREY, rect, 1)  # Light grey border for grid

        # Draw the ghost-piece
        if self.current_piece:
            ghost_y = self.calculate_ghost_piece_position()
            piece_shape, color = self.current_piece
            for x in range(len(piece_shape[0])):
                for y in range(len(piece_shape)):
                    if piece_shape[y][x]:
                        rect = pygame.Rect((self.piece_x + x) * BLOCK_SIZE,
                                           (ghost_y + y) * BLOCK_SIZE,
                                           BLOCK_SIZE, BLOCK_SIZE)
                        # Make the ghost color brighter
                        base_color = COLORS[color - 1]
                        bright_color = tuple(
                            min(255, c + 100) for c in base_color)  # Increase each color channel by 100
                        pygame.draw.rect(screen, bright_color, rect)
                        pygame.draw.rect(screen, LIGHT_GREY, rect, 1)  # Light grey border for ghost piece

        next_piece_x = SCREEN_WIDTH + (WINDOW_WIDTH - SCREEN_WIDTH - PREVIEW_WIDTH * BLOCK_SIZE) // 2 - BLOCK_SIZE // 2
        next_piece_y = 2 * BLOCK_SIZE

        # Draw the current piece
        if self.current_piece:
            piece_shape, color = self.current_piece
            for x in range(len(piece_shape[0])):
                for y in range(len(piece_shape)):
                    if piece_shape[y][x]:
                        rect = pygame.Rect((self.piece_x + x) * BLOCK_SIZE,
                                           (self.piece_y + y) * BLOCK_SIZE,
                                           BLOCK_SIZE, BLOCK_SIZE)
                        pygame.draw.rect(screen, COLORS[color - 1], rect)
                        pygame.draw.rect(screen, LIGHT_GREY, rect, 1)  # Light grey border for current piece
            # Draw the next piece
            for x in range(len(self.next_piece[0][0])):
                for y in range(len(self.next_piece[0])):
                    if self.next_piece[0][y][x]:
                        rect = pygame.Rect(next_piece_x + x * BLOCK_SIZE,
                                           next_piece_y + y * BLOCK_SIZE,
                                           BLOCK_SIZE, BLOCK_SIZE)
                        pygame.draw.rect(screen, COLORS[self.next_piece[1] - 1], rect)
                        pygame.draw.rect(screen, LIGHT_GREY, rect, 1)  # Light grey border for next piece

        # Draw the Life Saver piece
        if self.life_saver_piece:
            life_saver_x = SCREEN_WIDTH + (
                    WINDOW_WIDTH - SCREEN_WIDTH - PREVIEW_WIDTH * BLOCK_SIZE) // 2 - BLOCK_SIZE // 2
            life_saver_y = next_piece_y + 4 * BLOCK_SIZE  # Adjust as needed for spacing
            for y, row in enumerate(self.life_saver_piece[0]):
                for x, cell in enumerate(row):
                    if cell:
                        pygame.draw.rect(
                            screen, COLORS[self.life_saver_piece[1] - 1],
                            (life_saver_x + x * BLOCK_SIZE, life_saver_y + y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
                        )
                        pygame.draw.rect(
                            screen, LIGHT_GREY,
                            (life_saver_x + x * BLOCK_SIZE, life_saver_y + y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 1)

        pygame.display.flip()


def main():
    clock = pygame.time.Clock()
    game = Tetris(BOARD_WIDTH, BOARD_HEIGHT)
    global exit_rect
    last_horizontal_move_time = 0
    last_vertical_move_time = 0
    horizontal_move_direction = 0
    is_down_pressed = False
    is_paused = False

    while not game.game_over:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                    game.swap_life_saver()
                if event.key == pygame.K_LEFT:
                    horizontal_move_direction = -1
                    last_horizontal_move_time = pygame.time.get_ticks()
                    game.move(-1, 0)
                if event.key == pygame.K_RIGHT:
                    horizontal_move_direction = 1
                    last_horizontal_move_time = pygame.time.get_ticks()
                    game.move(1, 0)
                if event.key == pygame.K_DOWN:
                    is_down_pressed = True
                    last_vertical_move_time = pygame.time.get_ticks()
                    game.move(0, 1)
                if event.key == pygame.K_UP:
                    game.rotate_piece()
                if event.key == pygame.K_SPACE:
                    game.hard_drop()
                if event.key == pygame.K_ESCAPE:
                    is_paused = not is_paused  # Toggle pause state

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT and horizontal_move_direction == -1:
                    horizontal_move_direction = 0
                if event.key == pygame.K_RIGHT and horizontal_move_direction == 1:
                    horizontal_move_direction = 0
                if event.key == pygame.K_DOWN:
                    is_down_pressed = False

        if not is_paused:
            current_time = pygame.time.get_ticks()

            # Apply continuous horizontal movement
            if horizontal_move_direction != 0:
                if current_time - last_horizontal_move_time >= HORIZONTAL_MOVE_INTERVAL:
                    game.move(horizontal_move_direction, 0)
                    last_horizontal_move_time = current_time

            # Apply continuous vertical movement when down key is held
            if is_down_pressed:
                if current_time - last_vertical_move_time >= VERTICAL_MOVE_INTERVAL:
                    game.move(0, 1)
                    last_vertical_move_time = current_time

            # Move the piece down automatically at a set interval
            if current_time - game.block_move_timer >= BLOCK_MOVE_INTERVAL:
                game.step()
                game.block_move_timer = current_time

        game.draw()
        pygame.display.flip()
        clock.tick(TARGET_FPS)

        if is_paused:
            # Display the pause and exit message
            pause_text = game_over_font.render('PAUSE', True, (0, 0, 0))
            pause_rect = pause_text.get_rect(center=(WINDOW_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(pause_text, pause_rect)
            exit_text = game_over_font.render('EXIT', True, (255, 0, 0))  # Red text for "EXIT"
            exit_rect = exit_text.get_rect(center=(WINDOW_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
            screen.blit(exit_text, exit_rect)
            pygame.display.flip()

        while is_paused:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    is_paused = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if is_mouse_over_area(exit_rect):
                        pygame.quit()
                        sys.exit()

    # Display the game over screen
    game_over_text = game_over_font.render('GAME OVER!', True, (0, 0, 0))
    game_over_rect = game_over_text.get_rect(center=(WINDOW_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.blit(game_over_text, game_over_rect)
    pygame.display.flip()
    pygame.time.wait(2000)


if __name__ == '__main__':
    while True:
        main()
