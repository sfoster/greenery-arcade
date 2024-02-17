"""
Sprite Facing Left or Right
Face left or right depending on our direction

Simple program to show basic sprite usage.

Artwork from https://kenney.nl

If Python and Arcade are installed, this example can be run from the command line with:
python -m arcade.examples.sprite_face_left_or_right
"""

import arcade
from pyglet.math import Vec2

SPRITE_SCALING = 4

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Work-in-progress"

MOVEMENT_SPEED = 4

FACING_NORTH = 0
FACING_EAST = 1
FACING_SOUTH = 2
FACING_WEST = 3


class Player(arcade.Sprite):
    def __init__(self):
        super().__init__()
        self.scale = SPRITE_SCALING
        self.frame_idx = 0
        self.move_change = Vec2()
        textures = arcade.load_spritesheet("../resources/Hero.png", 16, 16, 8, 24, 0, "None")
        self.texture_direction = [
          textures[0:4],
          textures[12:16],
          textures[4:8],
          textures[8:12],
        ]
        self.travelled = 0
        # By default, face down.
        self.facing = FACING_SOUTH
        self.texture = self.texture_direction[self.facing][self.frame_idx]

    def update(self):
        self.center_x += self.move_change.x
        self.center_y += self.move_change.y
        moved = self.move_change.mag
        was_facing = self.facing

        if moved > 0:
          # Figure out if we should face left or right
          if self.move_change.x < 0:
            self.facing = FACING_WEST
          elif self.move_change.x > 0:
            self.facing = FACING_EAST
          if self.move_change.y < 0:
            self.facing = FACING_SOUTH
          elif self.move_change.y > 0:
            self.facing = FACING_NORTH

          if was_facing == self.facing:
            self.travelled += moved
          else:
            self.frame_idx = 0
            self.travelled = 0

          # Figure out if we need to advance the animatoin
          if self.travelled > 8:
            self.frame_idx += 1
            self.travelled = 0
          if self.frame_idx >= 4:
            self.frame_idx = 0
          print(f"facing: {self.facing}, frame_idx: {self.frame_idx}, len: {len(self.texture_direction[self.facing])}")
        else:
          self.frame_idx = 0
        self.texture = self.texture_direction[self.facing][self.frame_idx]

class MyGame(arcade.Window):
    """
    Main application class.
    """

    def __init__(self, width, height, title):
        # Call the parent class initializer
        super().__init__(width, height, title)

        # Variables that will hold sprite lists
        self.player_sprite_list = None

        # Set up the player info
        self.player_sprite = None

        # Set the background color
        arcade.set_background_color(arcade.color.AMAZON)

        # Track the current state of what key is pressed
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False


    def setup(self):
        """ Set up the game and initialize the variables. """

        # Sprite lists
        self.player_sprite_list = arcade.SpriteList()

        # Set up the player
        self.player_sprite = Player()
        self.player_sprite.center_x = SCREEN_WIDTH / 2
        self.player_sprite.center_y = SCREEN_HEIGHT / 2
        self.player_sprite_list.append(self.player_sprite)

    def update_player_speed(self):
        # Calculate speed based on the keys pressed
        move_change = Vec2(0, 0)

        if self.up_pressed and not self.down_pressed:
            move_change.y = 1
        elif self.down_pressed and not self.up_pressed:
            move_change.y = -1
        if self.left_pressed and not self.right_pressed:
            move_change.x = -1
        elif self.right_pressed and not self.left_pressed:
            move_change.x = 1
        # scale the movement so we get equal speed on diagonals
        self.player_sprite.move_change = move_change.from_magnitude(MOVEMENT_SPEED)

    def on_draw(self):
        # This command has to happen before we start drawing
        self.clear()

        # Draw all the sprites.
        self.player_sprite_list.draw()

    def on_update(self, delta_time):
        """ Movement and game logic """

        # Call update on all sprites (The sprites don't do much in this
        # example though.)
        self.player_sprite_list.update()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP:
            self.up_pressed = True
        elif key == arcade.key.DOWN:
            self.down_pressed = True
        elif key == arcade.key.LEFT:
            self.left_pressed = True
        elif key == arcade.key.RIGHT:
            self.right_pressed = True
        self.update_player_speed()

    def on_key_release(self, key, modifiers):
        if key == arcade.key.UP:
            self.up_pressed = False
        elif key == arcade.key.DOWN:
            self.down_pressed = False
        elif key == arcade.key.LEFT:
            self.left_pressed = False
        elif key == arcade.key.RIGHT:
            self.right_pressed = False
        self.update_player_speed()

def main():
    """ Main function """
    window = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()