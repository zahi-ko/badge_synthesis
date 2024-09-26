import os
import pickle
import random
import datetime

import arcade

from config import *
from multiprocessing import Queue
from badge import BadgeSprite, OtherBadge
from effect import ExplosionEffect, SynthesisEffect


class Game(arcade.Window):
    def __init__(self, queue1, queue2):
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
        # self.reset_score = True

        self.scene = None
        self.physics_engine = None

        self.explosion_effects: list[ExplosionEffect] = []
        self.synthesis_effects: list[SynthesisEffect] = []

        self.sprites_to_add = []
        self.sprites_to_remove = []

        self.send_queue = queue1
        self.receive_queue = queue2
        arcade.set_background_color(BACKGROUND_COLOR)


    def setup(self):
        # *设置相机
        self.camera = arcade.Camera(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.gui_camera = arcade.Camera(WINDOW_WIDTH, WINDOW_HEIGHT)

        # *创建徽章，代表当前的玩家
        self.player = BadgeSprite()

        # *初始化啊scene
        self.scene = arcade.Scene()
        # self.scene.add_sprite_list("Score")
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
        self.physics_engine = arcade.PymunkPhysicsEngine(damping=0.8, gravity=(0, -GRAVITY))

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

        self.physics_engine.add_collision_handler("other", "other", post_handler=self.synthesis)
        self.physics_engine.add_collision_handler("player", "other", post_handler=self.synthesis_player)
        self.physics_engine.add_collision_handler("player", "player", post_handler=self.synthesis_player)

        self.physics_engine.add_collision_handler("player", "boundary", begin_handler=lambda: False)
        self.physics_engine.add_collision_handler("other", "boundary", begin_handler=lambda: False)

        self.physics_engine.add_collision_handler("player", "platform", post_handler=self.stop_rotate)

        # 设置计时器
        arcade.schedule(self.generate_badge, 2)

    def on_draw(self):
        self.clear()
        self.camera.use()
        self.scene.draw([
            "Platform",
        ])

        [p.draw_visual() for p in self.scene['Player'] if p]
        [sprite.draw_visual() for sprite in self.scene['Other'] if sprite]
        [effect.draw() for effect in self.explosion_effects]
        [effect.draw() for effect in self.synthesis_effects]

        self.gui_camera.use()
        # self.scene.draw(["Score", ])
        arcade.draw_text(f"Score: {self.score}", 10, 10, arcade.color.BLACK, 20)
        arcade.draw_text("Pause" if not self.paused else "Resume", self.pause_button.center_x - 40, self.pause_button.center_y - 10, arcade.color.WHITE, 25)

    def on_update(self, delta_time: float):
        """Movement and game logic"""
        self.communicate()

        if self.paused: return
        self.process_sprites()
        self.physics_engine.step(delta_time=0.2)

        for effect_list in [self.explosion_effects, self.synthesis_effects]:
            for effect in effect_list:
                effect.update()
            effect_list[:] = [effect for effect in effect_list if effect.particles]
        

        self.set_velocity()

    def process_sprites(self):
        """ 处理需要添加和删除的sprites """

        # 处理需要删除的sprite
        for sprite in self.sprites_to_remove:
            sprite.remove_from_sprite_lists()
            if sprite == self.player:
                self.player = None
                self.generate_player()
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
                max_vertical_velocity=100,

            )
        self.sprites_to_add.clear()

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

    def stop_rotate(self, sp1, sp2, *args):
        sp1.rotate = False        

    def generate_badge(self, *args):
        if self.paused: return

        if random.choice((1, 0, 0, 0)) == 1:
            return
        tmp = OtherBadge()
        self.sprites_to_add.append(tmp)

    def generate_player(self, *args):
        arcade.schedule(self._generate_player, random.uniform(1, 3))
    
    def _generate_player(self, *args):
        self.player = BadgeSprite()
        self.sprites_to_add.append(self.player)

        arcade.unschedule(self._generate_player)

    def set_velocity(self):
        """  更新当前player的速度 """
        (player := self.player) and \
            ((self.physics_engine.is_on_ground(player) and self.generate_player()) or \
            self.physics_engine.apply_impulse(player, (HORIZONTAL_SPEED * int(self.right_pressing) -
                        HORIZONTAL_SPEED * int(self.left_pressing), 0)))

    def play_effect_sound(self, on_ground=False, collide=False, synthesis=False):
        func = lambda x: self.sound_manager.is_playing(x) or \
            self.sound_manager.play_sound(x)

        if not on_ground and any((self.left_pressing, self.right_pressing)):
            func("speedup")
        if collide:
            self.sound_manager.play_sound("collide")
        if synthesis:
            self.sound_manager.play_sound("synthesis")

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
            
            # 添加合成效果
            self.synthesis_effects.append(SynthesisEffect(center))
            
            tmp = OtherBadge(size=sp1.size+1, img_path=sp1.img_path)
            tmp.center_x, tmp.center_y = center

            self.sprites_to_add.append(tmp)

            return sp1.size
        
        return 0
    
    def synthesis_player(self, sp1, sp2, *args):
        self.stop_rotate(sp1, None)
        self.score += self.synthesis(sp1, sp2, *args)
        self.score.__int__()

    def check_sprites_in_explosion_radius(self, explosion_center, radius):
        """检测并消除在爆炸半径内的所有精灵"""
        for sprite_list in self.scene.sprite_lists:
            if sprite_list == self.scene['Platform']:
                continue
            for sprite in sprite_list:
                distance = arcade.get_distance(*explosion_center, sprite.center_x, sprite.center_y)
                if distance <= radius:
                    self.sprites_to_remove.append(sprite)

    def on_deactivate(self):
        self.paused = True

    def communicate(self):
        """ 与其他进程通信 """
        while not self.receive_queue.empty():
            match self.receive_queue.get():
                case "pause":
                    self.paused = True
                case "resume":
                    self.paused = False
                case "exit":
                    arcade.close_window()
                case "save":
                    self.save()
                case "show_save":
                    self.send_queue.put(self.show_save())
                case "load":
                    self.load(self.receive_queue.get())
            
    """ 保存和读取游戏状态 """
    def save(self):
        # 处理add和remove的sprite
        self.process_sprites()

        filename = "save" + datetime.datetime.now().strftime("%Y%m%d%H%M") + ".pkl"
        others = []
        for sprite in self.scene['Other']:
            others.append({
                "size": sprite.size,
                "img_path": sprite.img_path,
                "center_x": sprite.center_x,
                "center_y": sprite.center_y,
                "velocity": self.physics_engine.get_physics_object(sprite).body.velocity,
            })
        
        status = {
            "score": self.score,
            "paused": self.paused,
            "player": {
                "size": self.player.size,
                "img_path": self.player.img_path,
                "center_x": self.player.center_x,
                "center_y": self.player.center_y,
                "angle": self.player.visual_badge.angle,
                "velocity": self.physics_engine.get_physics_object(self.player).body.velocity,
            },
            "others": others,
        }

        if len(tmp := os.listdir("save")) >= 5: 
            oldest_file = min(tmp, key=lambda x: os.path.getctime(os.path.join("save", x)))
            os.remove(os.path.join("save", oldest_file))

        with open(f"save/{filename}", "wb") as f:
            pickle.dump(status, f)
    
    def show_save(self):
        if not os.path.exists("save"):
            os.mkdir("save")
            return []

        res = []
        for file in os.listdir("save"):
            if file.endswith(".pkl"):
                res.append(file)

        return res
    
    def load(self, filename):
        self.setup()

        with open("save\\" + filename, "rb") as f:
            status = pickle.load(f)
        self.score = status["score"]
        self.paused = status["paused"]

        self.player = BadgeSprite(
            size=status["player"]["size"],
            img_path=status["player"]["img_path"]
        )
        self.player.center_x = status["player"]["center_x"]
        self.player.center_y = status["player"]["center_y"]
        self.player.visual_badge.angle = status["player"]["angle"]
        self.sprites_to_add.append(self.player)


        for other in status["others"]:
            tmp = OtherBadge(
            size=other["size"],
            img_path=other["img_path"]
            )
            tmp.center_x = other["center_x"]
            tmp.center_y = other["center_y"]
            self.sprites_to_add.append(tmp)
            self.process_sprites()
            self.physics_engine.set_velocity(tmp, other["velocity"])
        
        self.physics_engine.set_velocity(self.player, status["player"]["velocity"])
    def draw_save(self):
        self.paused = True
        saves = self.show_save()
        if not saves:
            return
        for i, save in enumerate(saves):
            arcade.draw_text(save, 10, 10 + i*20, arcade.color.BLACK, 20)
    

def run(queue1: Queue, queue2: Queue):
    game = Game(queue1, queue2)
    game.setup()
    arcade.run()
