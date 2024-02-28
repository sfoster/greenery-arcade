"""
Prototype of a simple cleanup / castle-defense game
"""

import arcade
import arcade.gui
import math
from pyglet.math import Vec2
from PIL import Image
from copy import deepcopy

from settings import *

DEBUG = False
SPRITE_SCALING = 4
SPRITE_SCALING = 0.5

MOVEMENT_SPEED = 4
TRAVEL_PER_WALK_FRAME = 8
WALK_ANIM_FRAMES = 4

FACING_NORTH = 0
FACING_EAST = 1
FACING_SOUTH = 2
FACING_WEST = 3

empty_32x32 = arcade.Texture("empty_32x32", Image.new("RGBA", (32,32), color=(0,0,0,0)))

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
  def __init__(self, *args, **kwargs):
    super(Player, self).__init__(*args, **kwargs)
    # The player sprite should be scaled up unlike the others
    self.hit_box = [[-6, -7], [6, -7], [6, 5], [-6, 5]]
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
    print(f"Player width: {self.width}, height: {self.height}")

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
      self.game.level.attack_list.append(self.tool.use_at_point(posn, direction))

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
  def __init__(self, *args, **kw):
      super(GroundSplat, self).__init__(*args, **kw)

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

class MenuView(arcade.View):
  def on_show_view(self):
      arcade.set_background_color(arcade.color.WHITE)

  def on_draw(self):
      self.clear()
      arcade.draw_text("Menu Screen", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                       arcade.color.BLACK, font_size=50, anchor_x="center")
      arcade.draw_text("Click to advance.", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 75,
                       arcade.color.GRAY, font_size=20, anchor_x="center")

  def on_mouse_press(self, _x, _y, _button, _modifiers):
      game = GameView()
      self.window.show_view(game)

class GameOverView(arcade.View):
  def __init__(self, game_view):
      super().__init__()
      self.game_view = game_view

  def on_show_view(self):
      arcade.set_background_color(arcade.color.AVOCADO)

  def on_draw(self):
      self.clear()
      arcade.draw_text("Game Over", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                       arcade.color.BLACK, font_size=50, anchor_x="center")
      arcade.draw_text(f"Score: {self.game_view.player.score}", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 75,
                       arcade.color.BLACK, font_size=30, anchor_x="center")

class GameWindow(arcade.Window):
  def __init__(self, width, height, title):
      # Call the parent class initializer
      super().__init__(width, height, title)

class GameView(arcade.View):
  def __init__(self):
      super().__init__()

      self.name = "The GameView"
       # a UIManager to handle the UI.
      self.manager = arcade.gui.UIManager()
      self.manager.enable()

      self.level = None

      # Set up the player info
      self.player = None

      # Track the current state of what key is pressed
      self.left_pressed = False
      self.right_pressed = False
      self.up_pressed = False
      self.down_pressed = False

      self.width = SCREEN_WIDTH
      self.height = SCREEN_HEIGHT

      # Used in scrolling
      self.view_bottom = 0
      self.view_left = 0

      self.camera_sprites = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
      self.camera_gui = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

      self.setup()

  def setup(self):
      """ Set up the game and initialize the variables. """

      # Set the background color
      arcade.set_background_color(arcade.color.AMAZON)

      # Set up the player
      self.setup_player()

      self.level = LevelMap(LEVEL_MAP, self.player)

      # Setup the UI
      self.ui = GameUI(self.width, self.height)

      # Create a widget to hold the toolbar widget, that will center the buttons
      self.manager.add(
        self.ui.anchor
      )
      self.player.setup_ui(self.ui)

      self.splash_sound = arcade.load_sound("../resources/splash.wav")

      self.physics_engine = arcade.PhysicsEngineSimple(self.player,
                                                       self.level.wall_list)

  def setup_player(self):
      self.player = Player(self)
      self.player.game = self

  def place_grass(self, center_x, center_y):
      TERRAIN_TILE_SCALE = 2;
      grass = arcade.Sprite("../resources/grass_tileset_16x16.png",
                             TERRAIN_TILE_SCALE, 
                             64,0, # x, y offsets into the tileset
                             32,32, # width, height
                           )
      grass.center_x = center_x
      grass.center_y = center_y
      self.level.terrain_list.append(grass)

  def on_show_view(self):
      arcade.set_background_color(arcade.color.AMAZON)

  def scroll_to_player(self):
      """
      Scroll the window to the player.
      This method will attempt to keep the player at least VIEWPORT_MARGIN
      pixels away from the edge.

      if CAMERA_SPEED is 1, the camera will immediately move to the desired position.
      Anything between 0 and 1 will have the camera move to the location with a smoother
      pan.
      """

      # --- Manage Scrolling ---

      # Scroll left
      left_boundary = self.view_left + VIEWPORT_MARGIN
      if self.player.left < left_boundary:
          self.view_left -= left_boundary - self.player.left

      # Scroll right
      right_boundary = self.view_left + self.width - VIEWPORT_MARGIN
      if self.player.right > right_boundary:
          self.view_left += self.player.right - right_boundary

      # Scroll up
      top_boundary = self.view_bottom + self.height - VIEWPORT_MARGIN
      if self.player.top > top_boundary:
          self.view_bottom += self.player.top - top_boundary

      # Scroll down
      bottom_boundary = self.view_bottom + VIEWPORT_MARGIN
      if self.player.bottom < bottom_boundary:
          self.view_bottom -= bottom_boundary - self.player.bottom

      # Scroll to the proper location
      position = self.view_left, self.view_bottom
      self.camera_sprites.move_to(position, CAMERA_SPEED)

  def on_draw(self):
      # This command has to happen before we start drawing
      self.clear()
      # Select the camera we'll use to draw all our sprites
      self.camera_sprites.use()

      self.draw_list = arcade.SpriteList()

      # Draw all the sprites
      self.level.terrain_list.draw()
      self.level.target_list.draw()
      self.draw_list.extend(self.level.wall_list)
      self.draw_list.extend(self.level.player_list)
      self.draw_list.extend(self.level.attack_list)

      self.draw_list.sort(key=lambda x: x.position[1], reverse=True)
      self.draw_list.draw()

      if DEBUG:
        self.player.draw_hit_box()
        for attack in self.level.attack_list:
          attack.draw_hit_box()

      arcade.draw_lrtb_rectangle_filled(
        left=0, right=self.width, top=44, bottom=0,
        color=arcade.color.DARK_JUNGLE_GREEN
      )

      self.manager.draw()

  def on_update(self, delta_time):
      """ Movement and game logic """

      if not len(self.level.target_list):
        gameover = GameOverView(self)
        self.window.show_view(gameover)
        return

      self.level.player_list.on_update(delta_time)
      self.physics_engine.update()
      self.level.attack_list.on_update(delta_time)

      for attack in self.level.attack_list:
        target_hits = arcade.check_for_collision_with_list(attack, self.level.target_list)
        for target in target_hits:
          print(f"hit a target: {type(target).__name__}")
          self.level.target_list.remove(target)
          self.player.score += 1
          if isinstance(target, GroundSplat):
            self.place_grass(target.center_x, target.center_y)

      # post-update
      self.player.post_update()

      self.scroll_to_player()

      self.ui.score.text = f"Score: {self.player.score}"
      self.ui.fps.text = f"FPS: {arcade.get_fps():.0f}"
      self.player.tool.ui.border_color = arcade.color.AQUA


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
      self.player.change_x = scaled_change.x
      self.player.change_y = scaled_change.y

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
          self.player.tool_active = True
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
          self.player.tool_active = False

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

class LevelMap():
  def __init__(self, map_data, player):
    self.player = player

    # Variables that will hold sprite lists
    self.player_list = arcade.SpriteList()
    self.terrain_list = arcade.SpriteList()
    self.wall_list = arcade.SpriteList()
    self.target_list = arcade.SpriteList()
    self.attack_list = arcade.SpriteList()

    last_y = len(map_data)
    for row_index,line, in enumerate(map_data):
      y = (last_y - row_index) * TILESIZE
      for col_index,c in enumerate(line):
        x = col_index * TILESIZE
        if c == "X": 
          wall = arcade.Sprite(":resources:images/tiles/boxCrate_double.png",
                               SPRITE_SCALING, center_x=x, center_y=y)
          # wall.center_x = x
          # wall.center_y = 200
          self.wall_list.append(wall)
        elif c == "S": 
          puddle = GroundSplat("../resources/grass_tileset_16x16.png",
                                 1, 
                                 0,144, # x, y offsets into the tileset
                                 64,64, # width, height
                                 center_x=x, center_y=y)
          self.target_list.append(puddle)
        elif c == "P": 
          player.center_x = x
          player.center_y = y
          self.player_list.append(self.player)

def main():
    """ Main function """
    window = GameWindow(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    menu_view = MenuView()
    arcade.enable_timings()
    window.show_view(menu_view)
    arcade.run()


if __name__ == "__main__":
    main()