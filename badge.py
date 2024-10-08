import random
import arcade

from config import *

class BadgeSprite(arcade.SpriteCircle):
    def __init__(self, scale=BADGE_SCALE, radius=BADGE_RADIUS, color=(0, 0, 0, 0), soft=False, size=-1, img_path=None):
        super().__init__(radius, color, soft)
        
        ss_map = {
            1: 1,
            2: 1.2,
            3: 1.5
        }

        if size > 0:
            self.size = size
        elif (size := random.random()) <= 0.6:
            self.size = 1
        elif size <= 0.9:
            self.size = 2
        else:
            self.size = 3

        sscale = ss_map[self.size]

        radius *= sscale

        self._hit_box_algorithm = "Detailed"

        self.left = random.uniform(int(radius), int(WINDOW_WIDTH - radius))
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
        self.visual_badge = arcade.Sprite(self.img_path, scale=scale*sscale, hit_box_algorithm="None")

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

