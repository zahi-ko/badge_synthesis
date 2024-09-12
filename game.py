import os

import arcade.csscolor
import arcade.csscolor
import pymunk
import arcade
import arcade.key

from config import *


class BadgeSprite(arcade.SpriteCircle):
    def __init__(self, image_path, scale, radius=32, color=(0, 0, 0, 0), soft=False):
        super().__init__(radius, color, soft)

        self.size = 1
        self._hit_box_algorithm = "Detailed"

        self.center_x = WINDOW_WIDTH // 2
        self.center_y = WINDOW_HEIGHT

        # !当使用全透明后，sprite似乎不会自动生成hitbox，所以需要手动设置
        self.set_hit_box([
            (-radius, -radius),
            (radius, -radius),
            (radius, radius),
            (-radius, radius)
        ])
        

        self.visual_badge = arcade.Sprite(image_path, scale=scale, hit_box_algorithm="None")

    def draw_visual(self, on_ground=False):
        self.visual_badge.center_x = self.center_x
        self.visual_badge.center_y = self.center_y
        if not on_ground:
            self.visual_badge.angle += 5
        self.visual_badge.draw()

    

class Game(arcade.Window):
    def __init__(self):
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, update_rate=1/FPS)
        
        file_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(file_path)

        self.left_pressing = False
        self.right_pressing = False

        self.visual_bagde = None
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
        self.sound_util = self.speedup_sound
        self.players_dict = {}

        arcade.set_background_color(BACKGROUND_COLOR)


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

        # # *添加平台元素
        # list(map(lambda x: \
        #         self.scene['Platform'].append(
        #             arcade.Sprite(PLATFORM_PATH, PLATFORM_SCALE, center_x=x, center_y=PLATFORM_HEIGHT, hit_box_algorithm=None)),
        #         range(0, WINDOW_WIDTH, int(128 * PLATFORM_SCALE))
        #          ))
        
        # *使用loop替代map
        for i in range(0, WINDOW_WIDTH, int(128 * PLATFORM_SCALE)):
            platform = arcade.Sprite(
                PLATFORM_PATH,
                   PLATFORM_SCALE,
                         center_x=i,
                         center_y=PLATFORM_HEIGHT,
                         hit_box_algorithm="Detailed")
            
            self.scene['Platform'].append(platform)
        
        self.scene['Player'].append(self.player_badge)
        
        # *初始化物理引擎
        self.physics_engine = arcade.PymunkPhysicsEngine(damping=PLAYER_DAMPING,
                                                          gravity=(0, -GRAVITY))
        
        # *添加sprites到物理引擎
        self.physics_engine.add_sprite_list(self.scene['Player'],
                                        elasticity=0.3,
                                        moment_of_intertia=arcade.PymunkPhysicsEngine.MOMENT_INF,
                                        mass=PLAYER_MASS,
                                        # friction=PLYAYER_FRICITON,
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
        
        # self.physics_engine.add_collision_handler("player", "static", post_handler=self.stop_rotation)

    def on_draw(self):
        self.clear()
        self.camera.use()
        self.scene.draw([
            "Platform",
            "Player",
            "Other",
        ])
        self.player_badge.draw_visual(self.physics_engine.is_on_ground(self.player_badge))

        self.gui_camera.use()
        self.scene.draw(["Score", ])

    def on_update(self, delta_time: float):
        """Movement and game logic"""

        self.physics_engine.step(delta_time=0.125)
        self.check_bounds(self.scene["Player"])
        self.set_velocity(["Player", "Other"])


    def set_velocity(self, names: list[str]):
        sprites = (sprite for name in names for sprite in self.scene[name])
        bodys = (self.physics_engine.get_physics_object(sprite).body for sprite in sprites)

        # *通过将True和False转换为1和0，再乘以速度，来实现按键控制
        # vertical_v = int(not self.left_pressing) * HORIZONTAL_SPEED + \
        #                 int(not self.right_pressing) * (-HORIZONTAL_SPEED)
        (player := self.scene['Player'][0]) and \
            not self.physics_engine.is_on_ground(player) and \
                self.physics_engine.apply_impulse(player, (HORIZONTAL_SPEED * int(self.right_pressing) -
                            HORIZONTAL_SPEED * int(self.left_pressing), 0))
                # (self.apply_rotation(player))

        for body in bodys:
            body.velocity = pymunk.Vec2d(
                body.velocity.x,
                MAX_VERTICAL_SPEED if body.velocity.y < MAX_VERTICAL_SPEED else body.velocity.y
            )

        # # *尝试运用海象运算符、map替代循环
        # list(map(lambda i_x: \
        #         setattr(i_x[1].velocity, "velocity", 
        #                 pymunk.Vec2d(speed[i_x[0]][0],
        #                                 MAX_VERTICAL_SPEED if (tmp:=speed[i_x[0]][1]) < MAX_VERTICAL_SPEED else tmp)
        #         ), enumerate(bodys)))


    def on_key_press(self, symbol: int, modifiers: int):
        if symbol in (arcade.key.A, arcade.key.LEFT):
            self.left_pressing = True
        elif symbol in (arcade.key.D, arcade.key.RIGHT):
            self.right_pressing = True
        else:
            return
        if not self.players_dict.get("speedup"):
            self.players_dict["speedup"] = self.speedup_sound.play()



    
    def on_key_release(self, symbol: int, modifiers: int):
        if symbol in (arcade.key.A, arcade.key.LEFT):
            self.left_pressing = False
        elif symbol in (arcade.key.D, arcade.key.RIGHT):
            self.right_pressing = False
        else:
            return


    def check_bounds(self, sprites: arcade.SpriteList | arcade.Sprite):
        if isinstance(sprites, arcade.SpriteList):
            for sprite in sprites:
                self.check_bounds(sprite)
        elif isinstance(sprites, arcade.Sprite):
            (sprites.left < 0) and setattr(sprites, "left", 0)
            (sprites.right > WINDOW_WIDTH) and setattr(sprites, "right", WINDOW_WIDTH)
            (sprites.bottom < 0) and setattr(sprites, "bottom", 0)
            (sprites.top > WINDOW_HEIGHT) and setattr(sprites, "top", WINDOW_HEIGHT)
            
    def stop_rotation(self, player_sprite, platform_sprite, arbiter, space, data):
        self.physics_engine.get_physics_object(player_sprite).body.angular_velocity = 0.05
        return True
    
    def apply_rotation(self, sprite):
        self.physics_engine.get_physics_object(sprite).body.angular_velocity = 1
        impulse_magnitude = HORIZONTAL_SPEED * int(self.right_pressing) - \
                            HORIZONTAL_SPEED * int(self.left_pressing)

        return True
        # return (
        #     math.cos(math.radians(sprite.angle)) * impulse_magnitude,
        #     math.sin(math.radians(sprite.angle)) * impulse_magnitude,
        # )

        
        
        return True

def main():
    game = Game()
    game.setup()
    arcade.run()


if __name__ == "__main__":
    main()