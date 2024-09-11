import enum
import os
import arcade
import pymunk

from config import *


class BadgeSprite(arcade.Sprite):
    def __init__(self, image_path, scale=1):
        super().__init__(image_path, scale=scale)
        self.size = 1
        self.center_x = WINDOW_WIDTH // 2
        self.center_y = WINDOW_HEIGHT // 2

class Game(arcade.Window):
    def __init__(self):
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, update_rate=1/FPS)
        
        file_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(file_path)

        self.player_badge = None

        self.camera = None
        self.gui_camera = None

        self.score = 0
        self.reset_score = True

        self.scene = None
        self.physics_engine = None

        self.speedup_sound = arcade.load_sound(SPEEDUP_SOUND_PATH)
        self.collide_sound = arcade.load_sound(COLLIDE_SOUND_PATH)
        self.synthesis_sound = arcade.load_sound(SYNTHESIS_SOUND_PATH)

        arcade.set_background_color(arcade.csscolor.CORNFLOWER_BLUE)


    def setup(self):
        # *设置相机
        self.camera = arcade.Camera(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.gui_camera = arcade.Camera(WINDOW_WIDTH, WINDOW_HEIGHT)

        # *创建徽章
        self.player_badge = BadgeSprite(BADGE_PATH, scale=0.3)

        # *初始化啊scene
        self.scene = arcade.Scene()
        self.scene.add_sprite_list("Score")
        self.scene.add_sprite_list("Other")
        self.scene.add_sprite_list_after("Player", "Score")
        self.scene.add_sprite_list("Platform", use_spatial_hash=True)

        # *添加平台元素
        list(map(lambda x: \
                self.scene['Platform'].append(
                    arcade.Sprite(PLATFORM_PATH, PLATFORM_SCALE, center_x=x, center_y=PLATFORM_HEIGHT)),
                range(0, WINDOW_WIDTH, int(128 * PLATFORM_SCALE))
                 ))
        
        self.scene['Player'].append(self.player_badge)
        

        # *初始化物理引擎
        self.physics_engine = arcade.PymunkPhysicsEngine(damping=PLAYER_DAMPING,
                                                          gravity=(0, -GRAVITY))
        
        # *添加sprites到物理引擎
        self.physics_engine.add_sprite_list(self.scene['Player'],
                                        elasticity=0.3,
                                        mass=PLAYER_MASS,
                                        friction=PLYAYER_FRICITON,
                                        collision_type="player")
        
        self.physics_engine.add_sprite_list(self.scene['Other'],
                                            elasticity=0.3,
                                            mass=PLAYER_MASS,
                                            collision_type="dynamic",
                                            friction=DYNAMIC_ITEMS_FRICTION)
                
        self.physics_engine.add_sprite_list(self.scene['Platform'],
                                            collision_type="static",
                                            friction=PLATFORM_FRICTION,
                                            body_type=arcade.PymunkPhysicsEngine.STATIC)
        
        # self.physics_engine.add_collision_handler("player", "static", lambda *args: True)

    def on_draw(self):
        self.clear()
        self.camera.use()
        self.scene.draw([
            "Platform",
            "Player",
            "Other",
        ])

        self.gui_camera.use()
        self.scene.draw(["Score", ])

    def on_update(self, delta_time: float):
        """Movement and game logic"""

        self.physics_engine.step(delta_time=0.125)
        self.limit_velocity(["Player", "Other"])

    def limit_velocity(self, names: list[str]):
        sprites = (sprite for name in names for sprite in self.scene[name])
        bodys = [self.physics_engine.get_physics_object(sprite).body for sprite in sprites]
        speed = [(body.velocity.x, body.velocity.y) for body in bodys]

        # *尝试运用海象运算符、map替代循环
        list(map(lambda i_x: \
                setattr(i_x[1], "velocity", 
                        pymunk.Vec2d(MAX_HORIZONTAL_SPEED if (tmp:=speed[i_x[0]][0]) > MAX_HORIZONTAL_SPEED else tmp,
                                        MAX_VERTICAL_SPEED if (tmp:=speed[i_x[0]][1]) < MAX_VERTICAL_SPEED else tmp)
                ), enumerate(bodys)))




    def on_key_press(self, symbol: int, modifiers: int):
        pass
    
    def on_key_release(self, symbol: int, modifiers: int):
        pass


def main():
    game = Game()
    game.setup()
    arcade.run()


if __name__ == "__main__":
    main()