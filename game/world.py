from gameobjects.vector2 import Vector2
from pygame.surface import Surface
from pytmx.util_pygame import load_pygame

from game_funcs import initial_guards, create_random_stones, \
    render_score_message, draw_background_with_tiled_map, create_random_guards
from settings import game_settings


class World(object):
    def __init__(self, screen):
        self.entities = {}
        self.entity_id = 0
        self.energy_stones = {}
        self.game_map = load_pygame(game_settings.MAP_DIR)
        self.guard_nums = {"green": 0, "red": 0}
        self.background_layer = Surface(game_settings.SCREEN_SIZE).convert_alpha()
        self.player_layer = Surface(game_settings.SCREEN_SIZE).convert_alpha()
        self.player_layer.fill((0, 0, 0, 0))
        # initial double-side guards
        draw_background_with_tiled_map(self.background_layer, self.game_map)
        screen.blit(self.background_layer, game_settings.SCREEN_SIZE)

        initial_guards(self)

    def add_entity(self, entity):
        self.entities[self.entity_id] = entity
        entity.id = self.entity_id
        self.entity_id += 1
        self.guard_nums[entity.guard_type] += 1

    def remove_entity(self, entity):
        self.guard_nums[entity.guard_type] -= 1
        del self.entities[entity.id]

    def get(self, entity_id):
        if entity_id in self.entities:
            return self.entities[entity_id]

        return None

    def random_emit(self):
        create_random_guards(self)
        create_random_stones(self)

    def process(self, time_passed):
        time_passed_seconds = time_passed / 1000.0
        for entity in self.entities.values():
            entity.process(time_passed_seconds)

    def render(self, surface):
        surface.fill((255, 255, 255))
        self.player_layer.fill((0, 0, 0, 0))

        # render entities
        for entity in self.energy_stones.values():
            entity.render(self.player_layer)

        for entity in self.entities.values():
            entity.render(self.player_layer)

        render_score_message(self.player_layer)
        surface.blit(self.background_layer, (0, 0))
        surface.blit(self.player_layer, (0, 0))

    def get_close_entity(self, name, location, search_range=100.0):
        location = Vector2(*location)
        for entity in self.entities.values():
            if entity.name == name:
                distance = location.get_distance_to(entity.location)
                if distance < search_range:
                    return entity

        return None

    def get_close_energy(self, location, search_range=100.0):
        location = Vector2(*location)
        for entity in self.energy_stones.values():
            distance = location.get_distance_to(entity.location)
            if distance < search_range:
                return entity

        return None

    def get_energy_stone(self, energy_id):
        if energy_id in self.energy_stones.keys():
            return self.energy_stones[energy_id]

        return None

    def add_energy_stone(self, stone):
        self.energy_stones[self.entity_id] = stone
        stone.id = self.entity_id
        self.entity_id += 1

    def remove_energy_stone(self, stone):
        if stone in self.energy_stones.values():
            del self.energy_stones[stone.id]

    def min_guard_type(self):
        if self.guard_nums['red'] < self.guard_nums['green']:
            return 'red'

        return 'green'
