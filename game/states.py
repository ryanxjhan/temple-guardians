from random import randint

from gameobjects.vector2 import Vector2

from settings import game_settings


class State(object):
    def __init__(self, name):
        self.name = name

    def do_actions(self):
        pass

    def check_conditions(self):
        pass

    def entry_actions(self):
        pass

    def exit_actions(self):
        pass

    def __unicode__(self):
        return self.name

    __str__ = __unicode__


class StateMachine(object):
    def __init__(self):
        self.states = {}
        self.active_state = None

    def add_state(self, state):
        self.states[state.name] = state

    def think(self):
        if self.active_state is None:
            return

        self.active_state.do_actions()
        new_state_name = self.active_state.check_conditions()

        if new_state_name is not None:
            self.set_state(new_state_name)

    def set_state(self, new_state_name):
        if self.active_state is not None:
            self.active_state.exit_actions()

        self.active_state = self.states[new_state_name]
        self.active_state.entry_actions()


GUARD_STATES = (
    'exploring',
    'seeking',
    'fighting',
    'delivering'
)


class GuardStateExploring(State):
    def __init__(self, guard):
        State.__init__(self, GUARD_STATES[0])
        self.guard = guard

    def random_destination(self):
        w, h = game_settings.SCREEN_SIZE
        self.guard.destination = Vector2(randint(60, w - 60), randint(60, h - 60))

    def do_actions(self):
        if randint(1, 20) == 1:
            self.random_destination()

    def check_conditions(self):
        location = self.guard.location
        world = self.guard.world

        enemy_type = self.guard.get_enemy_type()
        enemy = world.get_close_entity(
            enemy_type,
            location,
            game_settings.DEFAULT_SEARCH_RANGE,
        )

        # exploring --> fighting
        if enemy is not None and location.get_distance_to(enemy.location) < 100.:
            self.guard.enemy_id = enemy.id
            return GUARD_STATES[2]

        energy_stone = world.get_close_energy(self.guard.location)

        # exploring --> seeking
        if energy_stone is not None:
            self.guard.energy_id = energy_stone.id
            return GUARD_STATES[1]

        return None

    def entry_actions(self):
        self.guard.speed = 120. + randint(-30, 30)
        self.random_destination()


class GuardStateSeeking(State):
    def __init__(self, guard):
        State.__init__(self, GUARD_STATES[1])
        self.guard = guard
        self.energy_id = None

    def check_conditions(self):
        world = self.guard.world
        location = self.guard.location
        energy_stone = world.get_energy_stone(self.guard.energy_id)

        if energy_stone is None:
            return GUARD_STATES[0]

        if location.get_distance_to(energy_stone.location) < 5.0:
            self.guard.carry(energy_stone.image)
            self.guard.world.remove_energy_stone(energy_stone)
            return GUARD_STATES[3]

        self.guard.destination = energy_stone.location
        return None

    def entry_actions(self):
        energy_stone = self.guard.world.get(self.guard.energy_id)
        if energy_stone is not None:
            self.guard.destination = energy_stone.location
            self.guard.speed = 160. + randint(-20, 20)


class GuardStateDelivering(State):
    def __init__(self, guard):
        State.__init__(self, GUARD_STATES[3])
        self.guard = guard

    def check_conditions(self):
        location = self.guard.location
        world = self.guard.world
        home_location = Vector2(*self.guard.get_home_location())
        distance_to_home = home_location.get_distance_to(location)

        if distance_to_home < game_settings.DROP_RANGE or not self.guard.in_center():
            if randint(1, 10) == 1:
                self.guard.drop(world.background_layer)
                self.guard.add_energy_score()
                return GUARD_STATES[0]

        return None

    def entry_actions(self):
        home_location = Vector2(*self.guard.get_home_location())
        self.guard.speed = 60.0
        random_offset = Vector2(randint(-20, 20), randint(-20, 20))
        self.guard.destination = home_location + random_offset


class GuardStateFighting(State):
    def __init__(self, guard):
        State.__init__(self, GUARD_STATES[2])
        self.guard = guard
        self.got_kill = False

    def do_actions(self):
        world = self.guard.world
        enemy = world.get(self.guard.enemy_id)
        if enemy is None:
            return

        self.guard.destination = enemy.location
        offset = self.guard.location.get_distance_to(enemy.location) < 15.
        random_seed = randint(1, 5) == 1

        if offset and random_seed:
            enemy.bitten()
            if enemy.health <= 0:
                enemy.dead()
                world.remove_entity(enemy)
                self.got_kill = True

    def check_conditions(self):
        if self.got_kill:
            return GUARD_STATES[3]

        enemy = self.guard.world.get(self.guard.enemy_id)

        if enemy is None:
            return GUARD_STATES[0]

        if self.guard.health < 2 / 3 * game_settings.MAX_HEALTH:
            self.guard.destination = self.guard.get_home_location()
            return GUARD_STATES[0]

        return None

    def entry_actions(self):
        self.speed = 160. + randint(0, 50)

    def exit_actions(self):
        self.got_kill = False
