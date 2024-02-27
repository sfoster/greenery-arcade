"""
Prototype of a simple cleanup / castle-defense game
"""

import arcade
import arcade.gui
import math
from pyglet.math import Vec2
from PIL import Image
from copy import deepcopy

DEBUG = False
SPRITE_SCALING = 4
SPRITE_SCALING = 0.5

SOUND_FX_VOLUME = 0.8

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

empty_32x32 = arcade.Texture("empty_32x32", Image.new("RGBA", (32,32), color=(0,0,0,0)))
g_game = None

def get_facing_vec2(entity):
  direction = Vec2()
  if entity.facing == FACING_NORTH:
    direction.y = 1
  elif entity.facing == FACING_SOUTH:
    direction.y = -1
  elif entity.facing == FACING_EAST:
    direction.x = 1
  elif entity.facing == FACING_WEST:
    direction.x = -1
  return direction

class SpriteEntity(arcade.Sprite):
  def __init__(self, game, *args):
    self.game = game
    super(SpriteEntity, self).__init__(*args)

class Player(SpriteEntity):
  def __init__(self, *args):
    super(Player, self).__init__(*args)
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

    self.tool = Tool(self, "shovel", arcade.load_texture("../resources/shovel.png"))
    self.alt_tool = Tool(self, "shovel", arcade.load_texture("../resources/seedbag.png"))
    self.tool_active = False

  def setup_ui(self, ui):
    ui.hotbar.add(self.tool.ui)
    ui.hotbar.add(self.alt_tool.ui)
    print(f"setup tool of type : {type(self.tool.ui).__name__}")


  def get_position_v2(self):
    return Vec2(self.center_x, self.center_y)

  def apply_tool(self, direction):
    posn = self.get_position_v2()
    if self.tool and self.tool.can_use(posn, direction):
      print(f"apply_tool, game: {self.game.name}")
      self.game.attack_list.append(self.tool.use_at_point(posn, direction))

  def on_update(self, dt):
    self.previous_posn = self.get_position_v2()
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

    self.tool.on_update(dt)
    if self.tool_active:
      self.apply_tool(get_facing_vec2(self))
    else:
      pass

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

class GroundSplat(arcade.Sprite):
  def __init__(self, *args):
      super(GroundSplat, self).__init__(*args)

class Whack(SpriteEntity):
  def __init__(self, filename, sound_name, *args):
    super(Whack, self).__init__(*args)
    print(f"Whack init, game is: {self.game.name}")

    self.frame_idx = 0
    print(f"Whack, has sound? { getattr(self.game, 'splash_sound') }")

    self.sound = getattr(self.game, sound_name)
    self.textures = arcade.load_spritesheet(
      filename,
      32, 32, 
      4, 4
    )
    self.collision_radius = 16 # 32/2
    self.hit_box = [ # an octogon ~16px in radius
      [5,-11],
      [-5,-11],
      [-11,-5],
      [-11,5],
      [-5,11],
      [5,11],
      [11,5],
      [11,-5],
    ]
    self.fps = 16
    self.elapsed = 0
    self.texture = self.textures[self.frame_idx]
    self.done_index = len(self.textures)

  def on_update(self, dt):
    if self.frame_idx >= self.done_index:
      self.kill()
      return
    if self.elapsed == 0:
      arcade.play_sound(self.sound, SOUND_FX_VOLUME)
    self.elapsed += dt
    self.frame_idx = min(self.done_index, -1 + math.floor(self.elapsed / (1/self.fps)))
    if self.frame_idx == self.done_index:
      self.texture = empty_32x32
      # print(f"Whack update, using empty texture with frame_idx {self.frame_idx}")
    else:
      # print(f"Whack update, elapsed {self.elapsed} of fps {self.fps}, using texture with frame? {math.floor(self.elapsed / (1/self.fps))}, frame_idx {self.frame_idx}")
      self.texture = self.textures[self.frame_idx]

class Tool():
  def __init__(self, owner, id, button_texture):
    self.owner = owner
    self.radius = 100
    self.arc = 90
    self.color = [255,0,0]
    self.center_x = 0
    self.center_y = 0
    self.cooldown = 0
    self.range = 30

    button = arcade.gui.UITextureButton(texture=button_texture)
    self.ui = arcade.gui.UIBorder(
      child=button,
      border_color=arcade.color.AQUA,
    )
    # How to update the border color on the fly? 
    # self.ui.color = (255, 0, 0)
    print(f"Tool init, ui: {vars(self.ui)}")

  def on_update(self, dt):
    self.cooldown = max(0, self.cooldown - dt)

  def can_use(self, pt, direction):
    print(f"can_use, current cooldown: {self.cooldown}")
    return self.cooldown == 0

  def use_at_point(self, pt, direction):
    self.cooldown = 1.0 # seconds
    print(f"use_at_point, game: {self.owner.game.name}")
    whack = Whack("../resources/green-explosion.png", "splash_sound", self.owner.game)
    x = pt.x + self.range * direction.x
    y = pt.y + self.range * direction.y
    print(f"use_at_point: direction: {direction.x}, {direction.y}; result: {x}, {y} from {pt.x},{pt.y}")
    whack.center_x = x
    whack.center_y = y
    return whack

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

      self.name = "The Game"

       # a UIManager to handle the UI.
      self.manager = arcade.gui.UIManager()
      self.manager.enable()

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
      self.terrain_list = arcade.SpriteList()
      self.wall_list = arcade.SpriteList()
      self.target_list = arcade.SpriteList()

      self.attack_list = arcade.SpriteList()

      # Set up the player
      self.setup_player()

      # Setup the UI
      self.ui = GameUI(self.width, self.height)

      # Create a widget to hold the toolbar widget, that will center the buttons
      self.manager.add(
        self.ui.anchor
      )
      self.player_sprite.setup_ui(self.ui)

      # Set up the level's walls etc.
      self.setup_terrain()
      self.setup_walls()
      self.setup_targets()

      self.splash_sound = arcade.load_sound("../resources/splash.wav")

      self.physics_engine = arcade.PhysicsEngineSimple(self.player_sprite,
                                                       self.wall_list)

    def setup_player(self):
      self.player_sprite = Player(self)
      self.player_sprite.game = self
      self.player_sprite.center_x = SCREEN_WIDTH / 2
      self.player_sprite.center_y = SCREEN_HEIGHT / 2
      self.player_sprite_list.append(self.player_sprite)

    def place_grass(self, center_x, center_y):
      TERRAIN_TILE_SCALE = 2;
      grass = arcade.Sprite("../resources/grass_tileset_16x16.png",
                             TERRAIN_TILE_SCALE, 
                             64,0, # x, y offsets into the tileset
                             32,32, # width, height
                           )
      grass.center_x = center_x
      grass.center_y = center_y
      self.terrain_list.append(grass)

    def place_puddle(self, center_x, center_y):
      puddle = GroundSplat("../resources/grass_tileset_16x16.png",
                             1, 
                             0,144, # x, y offsets into the tileset
                             64,64, # width, height
                           )
      puddle.center_x = center_x
      puddle.center_y = center_y
      self.target_list.append(puddle)

    def setup_terrain(self):
      self.place_grass(100, 400)

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

    def setup_targets(self):
      self.place_puddle(100, 400)
      self.place_puddle(60, 60)
      self.place_puddle(700, 100)

    def on_draw(self):
      # This command has to happen before we start drawing
      self.clear()

      # Draw all the sprites.
      self.terrain_list.draw()
      self.wall_list.draw()
      self.target_list.draw()
      self.player_sprite_list.draw()
      self.attack_list.draw()
      if DEBUG:
        for attack in self.attack_list:
          attack.draw_hit_box()

      arcade.draw_lrtb_rectangle_filled(
        left=0, right=self.width, top=44, bottom=0,
        color=arcade.color.DARK_JUNGLE_GREEN
      )
      self.manager.draw()

    def on_update(self, delta_time):
      """ Movement and game logic """
      self.player_sprite_list.on_update(delta_time)
      self.physics_engine.update()
      self.attack_list.on_update(delta_time)

      for attack in self.attack_list:
        target_hits = arcade.check_for_collision_with_list(attack, self.target_list)
        for target in target_hits:
          print(f"hit a target: {type(target).__name__}")
          self.target_list.remove(target)
          self.player_sprite.score += 1
          if isinstance(target, GroundSplat):
            self.place_grass(target.center_x, target.center_y)

      # post-update
      self.player_sprite.post_update()

      self.ui.score.text = f"Score: {self.player_sprite.score}"
      self.ui.fps.text = f"FPS: {arcade.get_fps():.0f}"
      self.player_sprite.tool.ui.border_color = arcade.color.AQUA


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
      elif key == arcade.key.SPACE:
          self.player_sprite.tool_active = True
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
      elif key == arcade.key.SPACE:
          self.player_sprite.tool_active = False

      self.update_player_speed()

class GameUI():
  def __init__(self, width, height):
    toolbar = arcade.gui.UIBoxLayout(
      x=0, y=0, 
      vertical=False,
      space_between=20
    )
    self.toolbar = toolbar

    fps = arcade.gui.UILabel(
      text="FPS: 00",
      text_color=[255,255,255],
      align="right"
    )
    self.fps = fps
    toolbar.add(fps.with_space_around(right=20))

    score = arcade.gui.UILabel(
      #width=60, height=48, 
      text="Score: 0",
      text_color=[255,255,255],
      align="right"
    )
    self.score = score
    toolbar.add(score.with_space_around(right=20))

    hotbar = arcade.gui.UIBoxLayout(
      x=0, y=0, 
      vertical=False,
    )
    self.hotbar = hotbar
    toolbar.add(hotbar.with_space_around(right=20))

    self.anchor = arcade.gui.UIAnchorWidget(
        anchor_x="left",
        anchor_y="bottom",
        align_x=8,
        align_y=4,
        child=toolbar
    )

def main():
    """ Main function """
    g_game = window = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.setup()
    arcade.enable_timings()
    arcade.run()


if __name__ == "__main__":
    main()