import os
import random

import pymunk
import arcade

from config import *


class BadgeSprite(arcade.SpriteCircle):
    def __init__(self, image_path, scale=BADGE_SCALE, radius=BADGE_RADIUS, color=(0, 0, 0, 0), soft=False):
        super().__init__(radius, color, soft)

        self.size = 1
        self._hit_box_algorithm = "Detailed"

        self.center_x = WINDOW_WIDTH // 2
        self.center_y = WINDOW_HEIGHT

        self.on_ground = False

        # !当使用全透明后，sprite似乎不会自动生成hitbox，所以需要手动设置
        self.set_hit_box([
            (-radius, -radius),
            (radius, -radius),
            (radius, radius),
            (-radius, radius)
        ])

        self.visual_badge = arcade.Sprite(image_path, scale=scale, hit_box_algorithm="None")

    def draw_visual(self):
        self.visual_badge.center_x = self.center_x
        self.visual_badge.center_y = self.center_y
        if not self.on_ground:
            self.visual_badge.angle += ROTATION_SPEED
        self.visual_badge.draw()


class OtherBadge(BadgeSprite):
    def __init__(self, scale=BADGE_SCALE):
        img = random.choice(RANDOM_BADGE)
        super().__init__(img, scale=scale)
        
        self.left = random.randint(10, WINDOW_WIDTH-10)
        self.top = WINDOW_HEIGHT + 100


class Game(arcade.Window):
    def __init__(self):
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, update_rate=1/FPS)
        
        file_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(file_path)

        self.left_pressing = False
        self.right_pressing = False

        self.visual_bagde = None
        self.current_badge = None

        self.camera = None
        self.gui_camera = None

        self.score = 0
        self.reset_score = True

        self.scene = None
        self.physics_engine = None

        # TODO 使用media.Player来播放声音，便于管理，创建一个SoundManager类
        """
        self.sound_manager = SoundManager()
        self.sound_manager.add_sound(SPEEDUP_SOUND_PATH, "speedup")
        self.sound_manager.add_sound(COLLIDE_SOUND_PATH, "collide")
        self.sound_manager.add_sound(SYNTHESIS_SOUND_PATH, "synthesis")
        """
        arcade.set_background_color(BACKGROUND_COLOR)


    def setup(self):
        # *设置相机
        self.camera = arcade.Camera(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.gui_camera = arcade.Camera(WINDOW_WIDTH, WINDOW_HEIGHT)

        # *创建徽章，代表当前的玩家
        self.current_badge = BadgeSprite(BADGE_PATH)

        # *初始化啊scene
        self.scene = arcade.Scene()
        self.scene.add_sprite_list("Score")
        self.scene.add_sprite_list("Other")
        self.scene.add_sprite_list("Platform", use_spatial_hash=True)
        self.scene.add_sprite_list("Boundary", use_spatial_hash=True)

        # *此处的Player非玩家控制的Sprite，而是玩家可以与之合成的对象
        self.scene.add_sprite_list("CurrentBadge")
        self.scene.add_sprite_list_after("Player", "Score")

        self.scene['CurrentBadge'].append(self.current_badge)
        self.scene['Other'].append(OtherBadge())
        
        # *添加边界
        for i in range(tmp := int(-128*PLATFORM_SCALE) , WINDOW_WIDTH - tmp, int(-tmp)):
            platform = arcade.Sprite(
                PLATFORM_PATH,
                   PLATFORM_SCALE,
                         center_x=i,
                         center_y=PLATFORM_HEIGHT)
        
            
            self.scene['Platform'].append(platform)

        for i in range(tmp := int(-128*PLATFORM_SCALE), WINDOW_HEIGHT - tmp, int(-tmp)):
            platform1 = arcade.Sprite(
                PLATFORM_PATH,
                PLATFORM_SCALE,
                center_x=int(-64*PLATFORM_SCALE),
                center_y=i
            )
            platform2 = arcade.Sprite(
                PLATFORM_PATH,
                PLATFORM_SCALE,
                center_x=int(64*PLATFORM_SCALE) + WINDOW_WIDTH,
                center_y=i
            )
            self.scene['Platform'].append(platform1)
            self.scene['Platform'].append(platform2)
        
        # *初始化物理引擎
        self.physics_engine = arcade.PymunkPhysicsEngine(damping=PLAYER_DAMPING,
                                                          gravity=(0, -GRAVITY))

        # *添加sprites到物理引擎
        self.update_spritelist('CurrentBadge',
                       elasticity=0,
                       mass=PLAYER_MASS,
                       collision_type="current",
                       moment_of_intertia=arcade.PymunkPhysicsEngine.MOMENT_INF)


        self.update_spritelist('Player',
                       elasticity=0,
                       moment_of_intertia=arcade.PymunkPhysicsEngine.MOMENT_INF,
                       mass=PLAYER_MASS,
                       collision_type="player")

        self.update_spritelist('Other',
                       elasticity=0,
                       mass=PLAYER_MASS,
                       collision_type="dynamic",
                       friction=DYNAMIC_ITEMS_FRICTION)

        self.update_spritelist('Platform',
                       collision_type="static",
                       friction=PLATFORM_FRICTION,
                       body_type=arcade.PymunkPhysicsEngine.STATIC)

        self.update_spritelist('Boundary',
                       collision_type="static",
                       body_type=arcade.PymunkPhysicsEngine.STATIC)
        
        self.physics_engine.add_collision_handler("dynamic", "static", post_handler=self.stop_rotation)

    def on_draw(self):
        if random.random() < 0.01:
            self.scene['Other'].append(tmp := OtherBadge())
            self.physics_engine.add_sprite(tmp, mass=PLAYER_MASS, collision_type="dynamic", friction=DYNAMIC_ITEMS_FRICTION)

        self.clear()
        self.camera.use()
        self.scene.draw([
            "Platform",
            "Player",
            "Other",
        ])

        self.current_badge.draw_visual()
        [sprite.draw_visual() for sprite in self.scene['Other']]

        self.gui_camera.use()
        self.scene.draw(["Score", ])

    def on_update(self, delta_time: float):
        """Movement and game logic"""

        self.physics_engine.step(delta_time=0.125)
        self.update_on_ground(self.scene['CurrentBadge'][0])
        [self.update_on_ground(sprite) for sprite in self.scene['Other']]
        

        self.set_velocity(["Other", "CurrentBadge"])

        # self.play_effect_sound(on_ground=self.flags['on_ground'])

    def update_on_ground(self, sprite):
        if self.physics_engine.is_on_ground(sprite):
            sprite.on_ground = True

    def set_velocity(self, names: list[str]):
        sprites = (sprite for name in names for sprite in self.scene[name])
        bodys = (self.physics_engine.get_physics_object(sprite).body for sprite in sprites)

        (player := self.scene['CurrentBadge'][0]) and \
            player.on_ground or \
            self.physics_engine.apply_impulse(player, (HORIZONTAL_SPEED * int(self.right_pressing) -
                        HORIZONTAL_SPEED * int(self.left_pressing), 0))

        for body in bodys:
            body.velocity = pymunk.Vec2d(
                body.velocity.x,
                MAX_VERTICAL_SPEED if body.velocity.y < MAX_VERTICAL_SPEED else body.velocity.y
            )

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol in (arcade.key.A, arcade.key.LEFT):
            self.left_pressing = True
        elif symbol in (arcade.key.D, arcade.key.RIGHT):
            self.right_pressing = True
        else:
            return
    
    def on_key_release(self, symbol: int, modifiers: int):
        if symbol in (arcade.key.A, arcade.key.LEFT):
            self.left_pressing = False
        elif symbol in (arcade.key.D, arcade.key.RIGHT):
            self.right_pressing = False
        else:
            return

    def play_effect_sound(self, on_ground=False, collide=False, synthesis=False):
        func = lambda x: self.sound_manager.is_playing(x) or \
            self.sound_manager.play_sound(x)

        if not on_ground and any((self.left_pressing, self.right_pressing)):
            func("speedup")
        if collide:
            self.sound_manager.play_sound("collide")
        if synthesis:
            self.sound_manager.play_sound("synthesis")
        
    def stop_rotation(self, player_sprite, platform_sprite, arbiter, space, data):
        self.physics_engine.get_physics_object(player_sprite).body.angular_velocity = 0
        return True

    def update_spritelist(self, name: str, **kwargs):
        self.physics_engine.add_sprite_list(self.scene[name], **kwargs)

def main():
    game = Game()
    game.setup()
    arcade.run()


if __name__ == "__main__":
    main()