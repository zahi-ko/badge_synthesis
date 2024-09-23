import datetime
import os
import random
import pickle

import arcade.csscolor
import pymunk
import arcade

from config import *

class Particle(arcade.SpriteCircle):
    def __init__(self, position, velocity, lifetime, color):
        super().__init__(radius=3, color=color)
        self.center_x, self.center_y = position
        self.change_x, self.change_y = velocity
        self.lifetime = lifetime

    def update(self):
        super().update()
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.remove_from_sprite_lists()

class ExplosionEffect:
    def __init__(self, position, particle_count=50):
        self.particles = arcade.SpriteList()
        self.position = position
        for _ in range(particle_count):
            velocity = (random.uniform(-4, 4), random.uniform(-4, 4))
            lifetime = random.randint(30, 60)
            color = random.choice([arcade.color.RED, arcade.color.ORANGE, arcade.color.YELLOW])
            particle = Particle(position, velocity, lifetime, color)
            self.particles.append(particle)

    def update(self):
        self.particles.update()

    def draw(self):
        self.particles.draw()

class BadgeSprite(arcade.SpriteCircle):
    def __init__(self, scale=BADGE_SCALE, radius=BADGE_RADIUS, color=(0, 0, 0, 0), soft=False, size=-1, img_path=None):
        super().__init__(radius, color, soft)
        

        if size > 0:
            self.size = size
        elif (size := random.random()) and False: 
            pass
        elif size <= 0.6:
            self.size = 1
        elif size <= 0.85:
            self.size = 1.5
        elif size <= 0.95:
            self.size = 2
        else:
            self.size = 3

        radius *= self.size

        self._hit_box_algorithm = "Detailed"

        self.left = random.randint(radius // 1, WINDOW_WIDTH-radius//1)
        self.top = WINDOW_HEIGHT + 100

        self.rotate = True

        # # !当使用全透明后，sprite似乎不会自动生成hitbox，所以需要手动设置
        self.set_hit_box([
            (-radius, -radius),
            (radius, -radius),
            (radius, radius),
            (-radius, radius)
        ])
        # self.set_hit_box(self.get_adjusted_hit_box())

        self.img_path = img_path if img_path else random.choice(RANDOM_BADGE) 
        self.visual_badge = arcade.Sprite(self.img_path, scale=scale*self.size, hit_box_algorithm="None")

    def draw_visual(self):
        self.visual_badge.center_x = self.center_x
        self.visual_badge.center_y = self.center_y

        if self.rotate:
            self.visual_badge.angle += ROTATION_SPEED
        self.visual_badge.draw()


class OtherBadge(BadgeSprite):
    def __init__(self, scale=BADGE_SCALE, size=-1, img_path=None):
        super().__init__(scale=scale, size=size, img_path=img_path)
        self.rotate = False


class Game(arcade.Window):
    def __init__(self):
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, update_rate=1/FPS)
        
        file_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(file_path)

        self.left_pressing = False
        self.right_pressing = False
        self.down_pressing = False

        self.visual_bagde = None
        self.player = None

        self.camera = None
        self.gui_camera = None

        self.score = 0
        self.reset_score = True

        self.scene = None
        self.physics_engine = None

        self.explosion_effects: list[ExplosionEffect] = []

        self.sprites_to_add = []
        self.sprites_to_remove = []

        arcade.set_background_color(BACKGROUND_COLOR)


    def setup(self):
        # *设置相机
        self.camera = arcade.Camera(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.gui_camera = arcade.Camera(WINDOW_WIDTH, WINDOW_HEIGHT)

        # *创建徽章，代表当前的玩家
        self.player = BadgeSprite()

        # *初始化啊scene
        self.scene = arcade.Scene()
        self.scene.add_sprite_list("Score")
        self.scene.add_sprite_list("Other")
        self.scene.add_sprite_list("Platform", use_spatial_hash=True)
        self.scene.add_sprite_list("Boundary", use_spatial_hash=True)

        # *此处的Player为玩家控制的Sprite
        self.scene.add_sprite_list("Player")

        # 创建暂停按钮
        self.paused = False
        self.pause_button = arcade.SpriteSolidColor(100, 50, arcade.color.GRAY)
        self.pause_button.center_x = WINDOW_WIDTH - 60
        self.pause_button.center_y = WINDOW_HEIGHT - 30
        self.scene.add_sprite("GUI", self.pause_button)
        
        for i in range(tmp := int(-128*PLATFORM_SCALE), WINDOW_WIDTH - tmp, int(-tmp)):
            platform = arcade.SpriteSolidColor(
                int(128 * PLATFORM_SCALE),
                int(128 * PLATFORM_SCALE),
                arcade.csscolor.ANTIQUE_WHITE
            )
            platform.center_x = i
            platform.center_y = 0
            
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
        self.physics_engine = arcade.PymunkPhysicsEngine(damping=1., gravity=(0, -GRAVITY))

        # *添加sprites到物理引擎
        self.sprites_to_add.append(self.player)


        self.update_spritelist('Platform',
                       collision_type="static",
                       body_type=arcade.PymunkPhysicsEngine.STATIC,
        )

        self.update_spritelist('Boundary',
                       collision_type="boundary",
                       body_type=arcade.PymunkPhysicsEngine.STATIC
        )
        
        self.physics_engine.add_collision_handler("other", "static", post_handler=self.stop_rotation)
        self.physics_engine.add_collision_handler("player", "static", post_handler=self.stop_rotation)

        self.physics_engine.add_collision_handler("other", "other", post_handler=self.synthesis)
        self.physics_engine.add_collision_handler("player", "other", post_handler=self.synthesis_player)
        self.physics_engine.add_collision_handler("player", "player", post_handler=self.synthesis_player)

        self.physics_engine.add_collision_handler("player", "boundary", begin_handler=lambda: False)
        self.physics_engine.add_collision_handler("other", "boundary", begin_handler=lambda: False)

        # 设置计时器
        arcade.schedule(self.generate_badge, 0.5)

    def on_draw(self):
        self.clear()
        self.camera.use()
        self.scene.draw([
            "Platform",
        ])

        [p.draw_visual() for p in self.scene['Player'] if p]
        [sprite.draw_visual() for sprite in self.scene['Other'] if sprite]
        [effect.draw() for effect in self.explosion_effects]

        self.gui_camera.use()
        # self.scene.draw(["Score", ])
        arcade.draw_text(f"Score: {self.score}", 10, 10, arcade.color.BLACK, 20)
        arcade.draw_text("Pause" if not self.paused else "Resume", self.pause_button.center_x - 40, self.pause_button.center_y - 10, arcade.color.WHITE, 14)

    def on_update(self, delta_time: float):
        """Movement and game logic"""
        if self.paused: return
        self.physics_engine.step(delta_time=0.2)

        for explosion_effect in self.explosion_effects:
            explosion_effect.update()

        self.explosion_effects = [effect for effect in self.explosion_effects if effect.particles]

        # 处理需要删除的sprite
        for sprite in self.sprites_to_remove:
            sprite.remove_from_sprite_lists()
            if sprite == self.player:
                self.player = None
                arcade.schedule(self.generate_player, 1)
        self.sprites_to_remove.clear()
        
        # 处理需要添加的sprite
        for sprite in self.sprites_to_add:
            collsion_type = "player"
            if isinstance(sprite, OtherBadge):
                self.scene['Other'].append(sprite)
                collsion_type = "other"
            else:
                self.scene['Player'].append(sprite)
            self.physics_engine.add_sprite(
                sprite=sprite,
                collision_type=collsion_type,
                max_horizontal_velocity=HORIZONTAL_SPEED,
                max_vertical_velocity=MAX_VERTICAL_SPEED,

            )
        self.sprites_to_add.clear()

        # self.set_velocity(["Other", ])

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol in (arcade.key.A, arcade.key.LEFT):
            self.left_pressing = True
        elif symbol in (arcade.key.D, arcade.key.RIGHT):
            self.right_pressing = True
        elif symbol in (arcade.key.S, arcade.key.DOWN):
            self.down_pressing = True
    
    def on_key_release(self, symbol: int, modifiers: int):
        if symbol in (arcade.key.A, arcade.key.LEFT):
            self.left_pressing = False
        elif symbol in (arcade.key.D, arcade.key.RIGHT):
            self.right_pressing = False
        elif symbol in (arcade.key.S, arcade.key.DOWN):
            self.down_pressing = False

    def on_mouse_press(self, x, y, *args):
        if self.pause_button.collides_with_point((x, y)):
            self.paused = not self.paused

    def generate_badge(self, *args):
        if random.choice((1, 0, 0, 0)) == 1:
            return
        tmp = OtherBadge()
        self.sprites_to_add.append(tmp)

    def generate_player(self, *args):
        self.player = BadgeSprite()
        self.sprites_to_add.append(self.player)

        arcade.unschedule(self.generate_player)

    def set_velocity(self):
        """  更新当前player的速度 """
        (player := self.player) and \
            ((self.physics_engine.is_on_ground(player) and self.generate_player()) or \
            self.physics_engine.apply_impulse(player, (HORIZONTAL_SPEED * int(self.right_pressing) -
                        HORIZONTAL_SPEED * int(self.left_pressing), 0)))

        player_speed = MAX_VERTICAL_SPEED - VERTICAL_SPEEDUP * self.down_pressing
        if player and (body := self.physics_engine.get_physics_object(player).body):
            body.velocity = pymunk.Vec2d(
                body.velocity.x,
                player_speed if body.velocity.y < player_speed else body.velocity.y
            )

    def play_effect_sound(self, on_ground=False, collide=False, synthesis=False):
        func = lambda x: self.sound_manager.is_playing(x) or \
            self.sound_manager.play_sound(x)

        if not on_ground and any((self.left_pressing, self.right_pressing)):
            func("speedup")
        if collide:
            self.sound_manager.play_sound("collide")
        if synthesis:
            self.sound_manager.play_sound("synthesis")
        
    def stop_rotation(self, player_sprite, *args):
        return 
        self.physics_engine.get_physics_object(player_sprite).body.angular_velocity = 0

    def update_spritelist(self, name: str, **kwargs):
        self.physics_engine.add_sprite_list(self.scene[name], **kwargs)

    def synthesis(self, sp1, sp2, *args):
        if sp1.img_path == sp2.img_path and sp1.size == sp2.size:
            self.sprites_to_remove.append(sp1)
            self.sprites_to_remove.append(sp2)

            center = ((sp1.center_x + sp2.center_x) // 2, (sp1.center_y + sp2.center_y) // 2)

            if sp1.size == 3:
                # 添加爆炸效果
                self.explosion_effects.append(ExplosionEffect(center))
                self.check_sprites_in_explosion_radius(center, 200)
                return 5

            tmp = OtherBadge(size=sp1.size+1, img_path=sp1.img_path)
            tmp.center_x, tmp.center_y = center

            self.sprites_to_add.append(tmp)

            return sp1.size
        
        return 0
    
    def synthesis_player(self, sp1, sp2, *args):
        self.score += self.synthesis(sp1, sp2, *args)

    def check_sprites_in_explosion_radius(self, explosion_center, radius):
        """检测并消除在爆炸半径内的所有精灵"""
        for sprite_list in self.scene.sprite_lists:
            if sprite_list == self.scene['Platform']:
                continue
            for sprite in sprite_list:
                distance = arcade.get_distance(*explosion_center, sprite.center_x, sprite.center_y)
                if distance <= radius:
                    self.sprites_to_remove.append(sprite)

    def save(self):
        filename = "save" + datetime.now().strftime("%Y%m%d") + ".pkl"
        status = {
            "score": self.score,
            "player": self.player,
            "sprites_to_add": self.sprites_to_add,
            "sprites_to_remove": self.sprites_to_remove,
            "explosion_effects": self.explosion_effects,
            "scene": self.scene,
            "paused": self.paused
        }

        with open(filename, "wb") as f:
            pickle.dump(status, f)

def main():
    game = Game()
    game.setup()
    arcade.run()


if __name__ == "__main__":
    main()