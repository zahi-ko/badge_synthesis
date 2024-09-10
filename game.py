import os
import arcade

from config import *


class BadgeSprite(arcade.Sprite):
    def __init__(self, image_path, scale=1):
        super().__init__(image_path, scale=scale)
        self.size = 1

class Game(arcade.Window):
    def __init__(self):
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, update_rate=1/FPS)
        
        file_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(file_path)

        self.player_badge = None
        self.gui_componets = None

        self.camera = None
        self.gui_camera = None

        self.score = 0
        self.reset_score = True

        self.scene = None
        self.physical_engine = None

        self.speedup_sound = arcade.load_sound(SPEEDUP_SOUND_PATH)
        self.collide_sound = arcade.load_sound(COLLIDE_SOUND_PATH)
        self.synthesis_sound = arcade.load_sound(SYNTHESIS_SOUND_PATH)

    def setup(self):
        self.camera = arcade.Camera(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.gui_camera = arcade.Camera(WINDOW_WIDTH, WINDOW_HEIGHT)

        self.gui_componets = arcade.SpriteList()

        self.scene = arcade.Scene()
        self.scene.add_sprite_list("Other")
        self.scene.add_sprite_list("Platform", use_spatial_hash=True)

        self.scene.add_sprite_list_before("Player", "Other")

        self.physical_engine = arcade.PymunkPhysicsEngine(damping=PLAYER_DAMPING,
                                                          gravity=(0, -GRAVITY))
        
        self.physical_engine.add_sprite(self.player_badge,
                                        elasticity=0.3,
                                        mass=PLAYER_MASS,
                                        friction=PLYAYER_FRICITON,
                                        collision_type="player",
                                        moment=arcade.PymunkPhysicsEngine.MOMENT_INF,
                                        max_horizontal_speed=PLAYER_MAX_HORIZONTAL_SPEED,
                                        max_vertical_speed=PLAYER_MAX_VERTICAL_SPEED)
        
        self.physical_engine.add_sprite_list(self.scene['Other'],
                                            elasticity=0.3,
                                            mass=PLAYER_MASS,
                                            collision_type="dynamic",
                                            friction=DYNAMIC_ITEMS_FRICTION,
                                            moment=arcade.PymunkPhysicsEngine.MOMENT_INF,
                                            max_horizontal_speed=PLAYER_MAX_HORIZONTAL_SPEED,
                                            max_vertical_speed=PLAYER_MAX_VERTICAL_SPEED)
        
        self.physical_engine.add_sprite_list(self.scene['Platform'],
                                            collision_type="static",
                                            friction=PLATFORM_FRICTION,
                                            body_type=arcade.PymunkPhysicsEngine.STATIC)

    def on_draw(self):
        self.clear()
        arcade.set_viewport(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
        self.camera.use()
        self.scene.draw()

        self.gui_camera.use()
        self.gui_componets.draw()

    def on_update(self, delta_time: float):
        """Movement and game logic"""

        self.physical_engine.step()
        self.scene.update()

        self.gui_componets.update()