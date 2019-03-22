from functools import reduce
import math


class State:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.direction = direction


class Action:
    def __init__(self, command, steps):
        self.command = command
        self.steps = steps

    def __str__(self):
        return self.command + " - " + str(self.steps)


class Tower:
    def __init__(self, x, y, damage, attack_range, locked):
        self.x = x
        self.y = y
        self.damage = damage
        self.attack_range = attack_range
        self.locked = locked


class Alien:
    def __init__(self, x, y, health, speed, spawn_time, dead):
        self.x = x
        self.y = y
        self.health = health
        self.speed = speed
        self.spawn_time = spawn_time
        self.dead = dead


def apply_action(state, action, bounds):
    new_state = State(state.x, state.y, state.direction)
    if action.command == 'F':
        if state.direction == 0:
            new_state.y -= action.steps
        elif state.direction == 1:
            new_state.x += action.steps
        elif state.direction == 2:
            new_state.y += action.steps
        elif state.direction == 3:
            new_state.x -= action.steps
    else:
        new_state.direction = (new_state.direction + action.steps) % 4

    new_state.x = max(min(bounds[0], new_state.x), 0)
    new_state.y = max(min(bounds[1], new_state.y), 0)

    return new_state


def break_action(action):
    actions = []

    if(action.command == 'F'):
        for _ in range(action.steps):
            actions.append(Action(action.command, 1))
    else:
        actions.append(action)

    return actions


def parse_input_file(in_file):
    actions = []
    bounds = ()
    initial_state = None
    aliens = []
    towers = []
    with open(in_file, "r") as f:
        actions = []
        lines = f.readlines()
        bounds = (int(lines[0].split()[0]), int(lines[0].split()[1]))
        initial_state = State(
            int(lines[1].split()[0]), int(lines[1].split()[1]), 1)
        actions_str = lines[2].split()
        commands_str = actions_str[0::2]
        steps_str = actions_str[1::2]

        for act_cmd, act_step in zip(commands_str, steps_str):
            actions.append(Action(act_cmd, int(act_step)))

        health, speed = (float(lines[3].split()[0]),
                         float(lines[3].split()[1]))

        n_aliens = int(lines[4])

        aliens = [Alien(initial_state.x, initial_state.y, health, speed, int(spawn_time), False)
                  for spawn_time in lines[5: 5 + n_aliens]]

        tower_damage, tower_range, tower_cost = (
            float(lines[5 + n_aliens].split()[0]), float(lines[5 + n_aliens].split()[1]), int(lines[5+n_aliens].split()[2]))

        gold = int(lines[5 + n_aliens + 1])

    return bounds, initial_state, actions, aliens, tower_damage, tower_range, tower_cost, gold


def compute_path(bounds, initial_state, actions):
    final_state = State(initial_state.x, initial_state.y,
                        initial_state.direction)

    new_actions = reduce(lambda l1, l2: l1 + l2,
                         [break_action(a) for a in actions])

    path = []
    path.append([final_state.x, final_state.y])

    for a in new_actions:
        final_state = apply_action(final_state, a, bounds)
        if a.command == 'F':
            path.append([final_state.x, final_state.y])

    return path


def compute_alien_position(path, tick, alien):
    if tick < alien.spawn_time:
        return -2, -2

    position_idx = min(len(path), math.floor(
        max((tick - alien.spawn_time), 0) * alien.speed))

    return path[position_idx][0], path[position_idx][1]


def euclidian_distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1)*(x2-x1) + (y2 - y1)*(y2-y1))


def lock_tower_target(tower, aliens):
    if tower.locked > -1:
        alien = aliens[tower.locked]
        if euclidian_distance(tower.x, tower.y, alien.x, alien.y) <= tower.attack_range and not alien.dead:
            # return for valid target
            return

    # no target
    tower.locked = -1
    min_alien_distance = euclidian_distance(
        tower.x, tower.y, aliens[0].x, aliens[0].y) + 1

    # find target
    for a, i in zip(aliens, range(len(aliens))):
        distance = euclidian_distance(tower.x, tower.y, a.x, a.y)
        if not a.dead and distance < min_alien_distance and distance <= tower.attack_range:
            min_alien_distance = distance
            tower.locked = i


def shoot_aliens(towers, aliens):
    for t in towers:
        if t.locked > -1:
            aliens[t.locked].health -= t.damage

    for a in aliens:
        if a.health <= 0:
            a.dead = True


def update_alien_positions(aliens, path):
    for a in aliens:
        if a.dead:
            continue
        alien_x, alien_y = compute_alien_position(path, tick, a)
        a.x = alien_x
        a.y = alien_y
        if a.x == a.y == -1:
            return "LOSS"

    return "PENDING"


def compute_path_points_in_range(pos, path, tower_range):
    count = 0
    for path_point in path:
        if (euclidian_distance(pos[0], pos[1], path_point[0], path_point[1])) <= tower_range:
            count += 1

    return count


def compute_towers(bounds, path, tower_damage, tower_range, tower_cost, gold):
    empty_positions = [[True for _ in range(bounds[0])]
                       for _ in range(bounds[1])]

    empty_positions_list = []

    for p in path:
        empty_positions[p[0]][p[1]] = False

    for x in range(bounds[0]):
        for y in range(bounds[1]):
            if empty_positions[x][y]:
                empty_positions_list.append([x, y])

    number_of_towers = math.floor(gold/tower_cost)

    for pos in empty_positions_list:
        pos.append(compute_path_points_in_range(pos, path, tower_range))

    positions = sorted(empty_positions_list,
                       key=lambda x: -x[2])[0:number_of_towers]

    towers = []
    for p in positions:
        towers.append(Tower(p[0], p[1], tower_damage, tower_range, False))

    return towers


if __name__ == "__main__":
    in_file = 'level5_5.in'
    out_file = 'level5_5.out'

    bounds, initial_state, actions, aliens, tower_damage, tower_range, tower_cost, gold = parse_input_file(
        in_file)

    path = compute_path(bounds, initial_state, actions)
    path.append([-1, -1])

    towers = compute_towers(bounds, path, tower_damage,
                            tower_range, tower_cost, gold)

    tick = -1
    result = "PENDING"
    while True:
        tick += 1
        result = update_alien_positions(aliens, path)
        if result == "LOSS":
            break
        for t in towers:
            lock_tower_target(t, aliens)

        if tick > 0:
            shoot_aliens(towers, aliens)

        if reduce(lambda x, y: x and y, [a.dead for a in aliens]):
            result = "WIN"
            break

    print(result)

    with open(out_file, "w") as f:
        for t in towers:
            f.write(str(t.x) + " " + str(t.y) + '\n')
