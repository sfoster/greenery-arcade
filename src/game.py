"""
Sprite Facing Left or Right
Face left or right depending on our direction

Simple program to show basic sprite usage.

Artwork from https://kenney.nl

If Python and Arcade are installed, this example can be run from the command line with:
python -m arcade.examples.sprite_face_left_or_right
"""

import arcade
import math
from pyglet.math import Vec2

SPRITE_SCALING = 4
SPRITE_SCALING = 0.5

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Work-in-progress"

MOVEMENT_SPEED = 4
TRAVEL_PER_WALK_FRAME = 8
WALK_ANIM_FRAMES = 4

FACING_NORTH = 0
FACING_EAST = 1
FACING_SOUTH = 2
FACING_WEST = 3


class Player(arcade.Sprite):
    def __init__(self):
        super().__init__()
        # The player sprite should be scaled up unlike the others
        self.scale = 4
        self.frame_idx = 0
        self.previous_posn = Vec2()
        textures = arcade.load_spritesheet("../resources/Hero.png", 16, 16, 8, 24, 0, "None")
        self.texture_direction = [
          textures[0:4],
          textures[12:16],
          textures[4:8],
          textures[8:12],
        ]
        # The cumulative distance we travelled in the current direction
        # Used to set the walking animation frame
        self.travelled = 0
        # By default, face down.
        self.facing = FACING_SOUTH
        self.texture = self.texture_direction[self.facing][self.frame_idx]

        self.score = 0;

    def update(self):
        self.previous_posn = Vec2(self.center_x, self.center_y)
        self.center_x += self.change_x
        self.center_y += self.change_y
        self.was_facing = self.facing
        movement = Vec2(self.change_x, self.change_y)

        if movement.mag > 0:
          # Figure out if we should face left or right
          if self.change_x < 0:
            self.facing = FACING_WEST
          elif self.change_x > 0:
            self.facing = FACING_EAST
          if self.change_y < 0:
            self.facing = FACING_SOUTH
          elif self.change_y > 0:
            self.facing = FACING_NORTH
        else:
          # set back to the idle/at-rest frame
          self.frame_idx = 0
          self.travelled = 0
        if self.was_facing != self.facing:
          # if we turned, reset to the first frame
          self.frame_idx = 0
          self.travelled = 0


    def post_update(self):
      # after updating physics, did we actually move?
      moved = Vec2(self.center_x, self.center_y) - self.previous_posn;

      if self.was_facing == self.facing and moved.mag > 0:
        # we continued in the same direction
        self.travelled += moved.mag
        # Move to next animation (of 4) frame each 8px of travel
        self.frame_idx = math.floor(self.travelled / TRAVEL_PER_WALK_FRAME) % WALK_ANIM_FRAMES
        self.texture = self.texture_direction[self.facing][self.frame_idx]
        # print(f"facing: {self.facing}, frame_idx: {self.frame_idx}, len: {len(self.texture_direction[self.facing])}")


class TextLabel():
  def __init__(self, text, start_x, start_y):
    self.start_x = start_x
    self.start_y = start_y
    self.color = [255,255,255]
    self.bgcolor = [0,0,0]

    self.text = arcade.Text(text, start_x, start_y, self.color)
    self.text.font_name="Kenney Pixel Square"

    text_width, text_height = self.text.content_size

    self.back = arcade.create_rectangle_filled(
      start_x + text_width/2+4, start_y + text_height/2 -2,
      text_width+26, text_height+8, 
      self.bgcolor
    )

  def update(self, value):
    self.text.text = str(value)

  def draw(self):
    self.back.draw()
    self.text.draw()

class MyGame(arcade.Window):
    def __init__(self, width, height, title):
      # Call the parent class initializer
      super().__init__(width, height, title)

      # Variables that will hold sprite lists
      self.player_sprite_list = None

      # Set up the player info
      self.player_sprite = None

      self.wall_list = None

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
      self.wall_list = arcade.SpriteList()
      self.coin_list = arcade.SpriteList()

      # Set up the player
      self.setup_player()
      self.score = TextLabel("Score: 0   ", 80, 6)
      self.fps = TextLabel("00", 6, 6)

      # Set up the level's wall
      self.setup_walls()
      self.setup_coins()

      self.physics_engine = arcade.PhysicsEngineSimple(self.player_sprite,
                                                       self.wall_list)

    def setup_player(self):
      self.player_sprite = Player()
      self.player_sprite.center_x = SCREEN_WIDTH / 2
      self.player_sprite.center_y = SCREEN_HEIGHT / 2
      self.player_sprite_list.append(self.player_sprite)

    def setup_walls(self):
      # -- Set up the walls
      # Create a row of boxes
      for x in range(173, 650, 64):
          wall = arcade.Sprite(":resources:images/tiles/boxCrate_double.png",
                               SPRITE_SCALING)
          wall.center_x = x
          wall.center_y = 200
          self.wall_list.append(wall)

      # Create a column of boxes
      for y in range(273, 500, 64):
          wall = arcade.Sprite(":resources:images/tiles/boxCrate_double.png",
                               SPRITE_SCALING)
          wall.center_x = 465
          wall.center_y = y
          self.wall_list.append(wall)

    def setup_coins(self):
      for i in range(5):
        coin = arcade.Sprite(":resources:images/items/coinGold.png", 0.25)
        coin.center_x = 150
        coin.center_y = 50 + (i*30)
        self.coin_list.append(coin)

    def on_draw(self):
      # This command has to happen before we start drawing
      self.clear()

      # Draw all the sprites.
      self.player_sprite_list.draw()
      self.wall_list.draw()
      self.coin_list.draw()
      self.score.draw()
      self.fps.draw()


    def on_update(self, delta_time):
      """ Movement and game logic """
      self.player_sprite_list.update()
      self.physics_engine.update()

      coin_hits = self.player_sprite.collides_with_list(self.coin_list)
      for coin in coin_hits:
        # print(f"hit a coin: {len(coin_hits)}")
        self.coin_list.remove(coin)
        self.player_sprite.score += 1

      # post-update
      self.player_sprite.post_update()

      self.score.update(f"Score: {self.player_sprite.score}")
      self.fps.update( f"{arcade.get_fps():.0f}" )


    def update_player_speed(self):
      # Calculate speed based on the keys pressed
      direction = Vec2(0, 0)

      if self.up_pressed and not self.down_pressed:
          direction.y = 1
      elif self.down_pressed and not self.up_pressed:
          direction.y = -1
      if self.left_pressed and not self.right_pressed:
          direction.x = -1
      elif self.right_pressed and not self.left_pressed:
          direction.x = 1
      scaled_change = direction.from_magnitude(MOVEMENT_SPEED)
      # scale the movement so we get equal speed on diagonals
      self.player_sprite.change_x = scaled_change.x
      self.player_sprite.change_y = scaled_change.y

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
    arcade.enable_timings()
    arcade.run()


if __name__ == "__main__":
    main()