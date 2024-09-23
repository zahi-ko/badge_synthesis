import random
import arcade
import arcade.color

class Particle(arcade.SpriteCircle):
    def __init__(self, position, velocity, lifetime, color):
        super().__init__(radius=3, color=color)
        self.position = position
        self.velocity = velocity
        self.lifetime = lifetime

    def update(self):
        super().update()
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.remove_from_sprite_lists()

class Effect:
    def __init__(self, position, particle_count, color, lifetime=(30, 50)):
        self.particles = arcade.SpriteList()
        self.position = position
        for _ in range(particle_count):
            velocity = (random.uniform(-4, 4), random.uniform(-4, 4))
            plifetime = random.randint(*lifetime)
            pcolor = random.choice(color)
            particle = Particle(position, velocity, plifetime, pcolor)
            self.particles.append(particle)

    def update(self):
        self.particles.update()

    def draw(self):
        self.particles.draw()

class ExplosionEffect(Effect):
    def __init__(self, position, particle_count=50):
        super().__init__(
            position,
            particle_count=particle_count,
            color=[
                arcade.color.RED, 
                arcade.color.ORANGE, 
                arcade.color.YELLOW, 
                arcade.color.PINK, 
                arcade.color.LIGHT_CORAL
        ])

class SynthesisEffect(Effect):
    def __init__(self, position, particle_count=50):
        super().__init__(
            position=position,
            particle_count=particle_count,
            lifetime=(20, 40),
            color=[
                arcade.color.CYAN, 
                arcade.color.MAGENTA, 
                arcade.color.LIME_GREEN, 
                arcade.color.TURQUOISE, 
                arcade.color.HOT_PINK
            ],
        )
