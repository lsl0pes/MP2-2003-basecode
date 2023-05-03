import sys
import json
import asyncio
import websockets
import getpass
import os
from mapa import Map
class Client:
    @staticmethod
    async def recv_game_properties(websocket,agent_name):
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))
        msg = await websocket.recv()
        game_properties = json.loads(msg)
        return msg, game_properties
    @staticmethod
    def create_map_representation(game_properties):
        return Map(size=game_properties["size"], mapa=game_properties["map"])
    @staticmethod
    async def recv_game_state(websocket):
        try:
            return json.loads(await websocket.recv())
        except websockets.exceptions.ConnectionClosedOK:
            print("Server has cleanly disconnected us")
            returnimport math
import sys
import json
import asyncio
import websockets
import getpass
import os
import time
import random
from destroy_wall import dest
from clients import Client
from agentai import AgentAI
from destroy_enemies import Destroy_enemies
async def agent_loop(server_address="localhost:8000", agent_name="84730"):
    async with websockets.connect(f"ws://{server_address}/player") as websocket:
        msg, game_properties = await Client.recv_game_properties(websocket, agent_name)
        current_level = None
        got_powerup = False
        bomb_range = 3
        bombs = 1
        detonator = False
        speed = 0
        powerup_last_pos = []
        lives = 3
        bomb_drop_location = []
        can_drop_bomb = False
        safe_position = []
        last_pos_with_bomb = []
        last_pos_with_bomb_counter = 0
        dodging_suicide = False
        enemy_id = ''
        last_enemy_direction = [0, 0]
        last_enemy_position = []
        enemy_is_boring_counter = 0
        pathing = []
        last_pos = []
        game_map = AgentAI.create_empty_2d_array(game_properties["size"][0], game_properties["size"][1])
        AgentAI.array_to_empty_map(game_map)
        while True:
            state = await Client.recv_game_state(websocket)
            if not state or lives == 0:
                break
            try:
                AgentAI.clear_map(game_map)
                AgentAI.fill_empty_map_with_walls(game_map, state["walls"])
                AgentAI.fill_empty_map_with_enemies(game_map, state["enemies"])
            except:
                break
            if current_level is None:
                current_level = state["level"]
            elif current_level < state["level"]:
                current_level = state["level"]
                got_powerup = False
                bomb_drop_location = []
                can_drop_bomb = False
                safe_position = []
                enemy_id = ''
                last_enemy_direction = [0, 0]
                last_enemy_position = []
                pathing = []
                last_pos = []
                powerup_last_pos = []
                enemy_is_boring_counter = 0
                last_pos_with_bomb = []
                last_pos_with_bomb_counter = 0
                dodging_suicide = False
            if state["level"] in [2, 3, 5, 6, 8, 11, 12, 13]:
                got_powerup = True
                if state["powerups"]:
                    game_map[state["powerups"][0][0][1]][state["powerups"][0][0][0]] = 4
            if not state["enemies"] and not got_powerup and state["exit"]:
                game_map[state["exit"][1]][state["exit"][0]] = 4
            if state["lives"] < lives:
                enemy_id = ''
                last_enemy_position = []
                last_enemy_direction = [0, 0]
                bomb_drop_location = []
                target = []
                can_drop_bomb = False
                safe_position = []
                pathing = []
                target_enemy = False
                last_pos_with_bomb = []
                last_pos_with_bomb_counter = 0
                dodging_suicide = False
            lives = state["lives"]
            if state['bombs']:
                exist_bomb = True
            else:
                exist_bomb = False
                safe_position = []
            closest_destructive_wall = Destroy_enemies.closest_wall(state["bomberman"], state["walls"])
            if state["bomberman"] == last_pos_with_bomb and exist_bomb:
                last_pos_with_bomb_counter += 1
            if last_pos_with_bomb_counter >= 2 and exist_bomb:
                target = AgentAI.get_safe_spot(state["bomberman"], state["bombs"][0],
                                                          state["bomberman"], bomb_range - last_pos_with_bomb_counter,
                                                          game_map,
                                                          safes=[])
                can_drop_bomb = False
                pathing = AgentAI.a_star_pathing(state["bomberman"], target, game_map, False)
                dodging_suicide = True
            if not dodging_suicide:
                if powerup_last_pos == state["bomberman"]:
                    got_powerup = True
                    if powerup == "Flames":
                        bomb_range += 1
                    elif powerup == "Bombs":
                        bombs += 1
                    elif powerup == "Detonator":
                        detonator = True
                    elif powerup == "Speed":
                        speed += 1
                if state["powerups"] and not got_powerup:
                    powerup = state["powerups"][0][1]
                    powerup_last_pos = state["powerups"][0][0]
                    target = powerup_last_pos
                elif len(state["enemies"]) > 0 and not exist_bomb:
                    dist = [dest.distance_points(state['bomberman'], enemy["pos"]) for enemy in state["enemies"]]
                    index = dest.close_position(dist)
                    target_enemy = state["enemies"][index]["pos"]
                    if enemy_id == state["enemies"][index]["id"]:
                        enemy_is_boring_counter += 1
                    else:
                        enemy_is_boring_counter = 0
                    if enemy_id != state["enemies"][index]["id"]:
                        last_enemy_position = []
                        last_enemy_direction = [0, 0]
                    if last_enemy_position:
                        direction = [target_enemy[0] - last_enemy_position[0],
                                     target_enemy[1] - last_enemy_position[1]]
                        if direction == [0, 0] or -1 <= direction[0] + direction[1] >= 1:  
                            if -1 <= last_enemy_direction[0] + last_enemy_direction[1] >= 1:
                                direction = [0, 0]
                            else:
                                direction = last_enemy_direction
                        bomb_drop_location, last_enemy_direction = Destroy_enemies.place_drop_bomb(target_enemy, game_map,
                                                                                                   direction, tmp=random.randint(2,3))
                    else:
                        bomb_drop_location, last_enemy_direction = Destroy_enemies.place_drop_bomb(target_enemy, game_map,
                                                                                                   [0, 0], tmp=random.randint(2,3))
                    if game_map[bomb_drop_location[1]][bomb_drop_location[0]] == 3:
                        if game_map[bomb_drop_location[1] + 1][bomb_drop_location[0]] == 2:
                            bomb_drop_location = [bomb_drop_location[0], bomb_drop_location[1] + 1]
                        elif game_map[bomb_drop_location[1]][bomb_drop_location[0] + 1] == 2:
                            bomb_drop_location = [bomb_drop_location[0] + 1, bomb_drop_location[1]]
                        elif game_map[bomb_drop_location[1] - 1][bomb_drop_location[0]] == 2:
                            bomb_drop_location = [bomb_drop_location[0], bomb_drop_location[1] - 1]
                        else:
                            bomb_drop_location = [bomb_drop_location[0] - 1, bomb_drop_location[1]]
                        can_drop_bomb = True
                    enemy_id = state["enemies"][index]["id"]
                    target = bomb_drop_location
                    last_enemy_position = target_enemy
                elif state["exit"] and not state["enemies"] and not exist_bomb and got_powerup:
                    target = state["exit"]
                elif Destroy_enemies.enemy_is_in_range(state["bomberman"], closest_destructive_wall,
                                                       1) and not exist_bomb:
                    tmp_safe_position = AgentAI.get_safe_spot(state["bomberman"], state["bomberman"],
                                                              closest_destructive_wall, bomb_range,
                                                              game_map,
                                                              safes=[])
                    if tmp_safe_position:
                        safe_position = tmp_safe_position
                        can_drop_bomb = True
                    else:
                        can_drop_bomb = False
                elif (not state['exit'] and not exist_bomb) or (
                        not got_powerup and not exist_bomb and not state["enemies"])\
                        or powerup_last_pos is not None\
                        or got_powerup and not state["exit"]:
                    target = closest_destructive_wall
                if enemy_is_boring_counter > 50:
                    target = closest_destructive_wall
                    enemy_is_boring_counter = 0
                if state["bomberman"] != target and not state['bombs']:
                    if len(pathing) == 0:
                        pathing = AgentAI.a_star_pathing(state["bomberman"], target, game_map, True)
                    if game_map[pathing[0][1]][pathing[0][0]] == 2:
                        tmp_safe_position = AgentAI.get_safe_spot(state["bomberman"], state["bomberman"],
                                                                  pathing[0], bomb_range,
                                                                  game_map,
                                                                  safes=[])
                        if tmp_safe_position:
                            safe_position = tmp_safe_position
                            can_drop_bomb = True
                        else:
                            can_drop_bomb = False
                if state['bombs'] and safe_position and state["bomberman"] != safe_position:
                    pathing = AgentAI.a_star_pathing(state["bomberman"], safe_position, game_map, False)
                if last_pos == state["bomberman"] and detonator and state["bombs"]:
                    key = "A"
                last_pos = state["bomberman"]
            dodging_suicide = False
            if len(pathing) == 0:
                if state["bomberman"] == bomb_drop_location and not state["bombs"]:
                    tmp_safe_position = AgentAI.get_safe_spot(state["bomberman"], bomb_drop_location, target_enemy,
                                                              bomb_range, game_map,
                                                              safes=[])
                    if tmp_safe_position:
                        safe_position = tmp_safe_position
                        key = "B"
                        last_enemy_position = []
                        last_enemy_direction = [0, 0]
                    else:
                        key = ""
                elif detonator and (
                        state["bomberman"][0] != state["bombs"][0][0] or state["bomberman"][1] != state["bombs"][0][1]):
                    key = "A"
                else:
                    key = ""
                pathing = []
                await websocket.send(
                    json.dumps({"cmd": "key", "key": key})
                )
            elif len(pathing) > 0:
                next_pos = pathing[0]
                if can_drop_bomb:
                    key = "B"
                    can_drop_bomb = False
                    breaking_walls = True
                elif state["bomberman"][1] - 1 == next_pos[1]:
                    key = "w"
                elif state["bomberman"][1] + 1 == next_pos[1]:
                    key = "s"
                elif state["bomberman"][0] - 1 == next_pos[0]:
                    key = "a"
                elif state["bomberman"][0] + 1 == next_pos[0]:
                    key = "d"
                else:
                    key = ""
                moving_adjacent_enemy = False
                if game_map[next_pos[1] - 1][next_pos[0]] == 3:
                    moving_adjacent_enemy = True
                if game_map[next_pos[1] + 1][next_pos[0]] == 3:
                    moving_adjacent_enemy = True
                if game_map[next_pos[1]][next_pos[0] - 1] == 3:
                    moving_adjacent_enemy = True
                if game_map[next_pos[1]][next_pos[0] + 1] == 3:
                    moving_adjacent_enemy = True
                if moving_adjacent_enemy and not state["bombs"]:
                    key = ''
                pathing = []
                await websocket.send(
                    json.dumps({"cmd": "key", "key": key})
                )
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))
import math
import random
from searchnode import SearchNode
class AgentAI:
    @staticmethod
    def closest_enemy(bomber_coords, enemies):
        if not enemies:
            return None
        elif len(enemies) == 1:
            return enemies[0]["pos"]
        elif len(enemies) == 2:
            if math.hypot(enemies[0]["pos"][0] - bomber_coords[0], enemies[0]["pos"][1] - bomber_coords[1]) \
                    < math.hypot(enemies[1]["pos"][0] - bomber_coords[0], enemies[1]["pos"][1] - bomber_coords[1]):
                return enemies[0]["pos"]
            else:
                return enemies[1]["pos"]
        else:
            if math.hypot(enemies[0]["pos"][0] - bomber_coords[0], enemies[0]["pos"][1] - bomber_coords[1]) \
                    < math.hypot(enemies[1]["pos"][0] - bomber_coords[0], enemies[1]["pos"][1] - bomber_coords[1]):
                return AgentAI.closest_enemy(bomber_coords, [enemies[0]] + enemies[2:])
            else:
                return AgentAI.closest_enemy(bomber_coords, [enemies[1]] + enemies[2:])
    @staticmethod
    def generate_cost_map(bomber_pos, bomb_radius, walls, map_width, map_height):
        cost_map = AgentAI.create_empty_2d_array(map_width, map_height)
        current_map = AgentAI.create_base_map(walls, map_width, map_height)
        cost_map = AgentAI.array_to_empty_cost_array(cost_map, map_width, map_height)
        AgentAI.fill_cost_map_rec(cost_map, current_map, bomb_radius, bomber_pos, move_cost=0)
        return cost_map
    @staticmethod
    def create_empty_2d_array(width, height):
        cost_map = []
        for i in range(0, height):
            tmp = []
            for j in range(0, width):
                tmp.append(None)
            cost_map.append(tmp)
        return cost_map
    @staticmethod
    def array_to_empty_map(in_map):
        for i in range(0, len(in_map)):
            for j in range(0, len(in_map[0])):
                if i == 0 or i == len(in_map) - 1 or j == 0 or j == len(in_map[0]) - 1:
                    in_map[i][j] = 1
                elif i % 2 == 0 and j % 2 == 0:
                    in_map[i][j] = 1
                else:
                    in_map[i][j] = 0
    @staticmethod
    def array_to_empty_cost_array(in_array, map_width, map_height):
        for i in range(0, len(in_array)):
            for j in range(0, len(in_array[0])):
                if i == 0 or i == len(in_array) - 1 or j == 0 or j == len(in_array[0]) - 1:
                    in_array[i][j] = (map_width + map_height - 2) * 23 + 1
                elif i % 2 == 0 and j % 2 == 0:
                    in_array[i][j] = (map_width + map_height - 2) * 23 + 1
                else:
                    in_array[i][j] = 0
    @staticmethod
    def fill_empty_map_with_walls(in_map, walls):
        for wall in walls:
            in_map[wall[1]][wall[0]] = 2
    @staticmethod
    def fill_empty_map_with_enemies(in_map, enemies):
        for enemy in enemies:
            in_map[enemy["pos"][1]][enemy["pos"][0]] = 3
    @staticmethod
    def clear_map(in_map):
        for i in range(0, len(in_map)):
            for j in range(0, len(in_map[i])):
                if in_map[i][j] == 2 or in_map[i][j] == 3 or in_map[i][j] == 4:
                    in_map[i][j] = 0
    @staticmethod
    def create_base_map(walls, enemies, map_width, map_height):
        tmp_map = AgentAI.create_empty_2d_array(map_width, map_height)
        AgentAI.array_to_empty_map(tmp_map)
        AgentAI.fill_empty_map_with_walls(tmp_map, walls)
        AgentAI.fill_empty_map_with_enemies(tmp_map, enemies)
        return tmp_map
    @staticmethod
    def fill_cost_map_rec(cost_map, game_map, bomb_radius, bomber_pos, move_cost):
        cost_map[bomber_pos[0]][bomber_pos[1]] = move_cost
        if game_map[bomber_pos[0] - 1][bomber_pos[1]] != 1:
            if cost_map[bomber_pos[0] - 1][bomber_pos[1]] is None \
                    or cost_map[bomber_pos[0] - 1][bomber_pos[1]] > move_cost:
                if game_map[bomber_pos[0] - 1][bomber_pos[1]] == 2:
                    AgentAI.fill_cost_map_rec(cost_map, game_map, bomb_radius, [bomber_pos[0] - 1, bomber_pos[1]],
                                              move_cost + 2 * bomb_radius + 11)
                elif game_map[bomber_pos[0] - 1][bomber_pos[1]] == 0:
                    AgentAI.fill_cost_map_rec(cost_map, game_map, bomb_radius, [bomber_pos[0] - 1, bomber_pos[1]],
                                              move_cost + 1)
        if bomber_pos[0] + 1 < len(game_map) and game_map[bomber_pos[0] + 1][bomber_pos[1]] != 1:
            if cost_map[bomber_pos[0] + 1][bomber_pos[1]] is None \
                    or cost_map[bomber_pos[0] + 1][bomber_pos[1]] > move_cost:
                if game_map[bomber_pos[0] + 1][bomber_pos[1]] == 2:
                    AgentAI.fill_cost_map_rec(cost_map, game_map, bomb_radius, [bomber_pos[0] + 1, bomber_pos[1]],
                                              move_cost + 2 * bomb_radius + 11)
                elif game_map[bomber_pos[0] + 1][bomber_pos[1]] == 0:
                    AgentAI.fill_cost_map_rec(cost_map, game_map, bomb_radius, [bomber_pos[0] + 1, bomber_pos[1]],
                                              move_cost + 1)
        if game_map[bomber_pos[0]][bomber_pos[1] - 1] != 1:
            if cost_map[bomber_pos[0]][bomber_pos[1] - 1] is None \
                    or cost_map[bomber_pos[0]][bomber_pos[1] - 1] > move_cost:
                if game_map[bomber_pos[0]][bomber_pos[1] - 1] == 2:
                    AgentAI.fill_cost_map_rec(cost_map, game_map, bomb_radius, [bomber_pos[0], bomber_pos[1] - 1],
                                              move_cost + 2 * bomb_radius + 11)
                elif game_map[bomber_pos[0]][bomber_pos[1] - 1] == 0:
                    AgentAI.fill_cost_map_rec(cost_map, game_map, bomb_radius, [bomber_pos[0], bomber_pos[1] - 1],
                                              move_cost + 1)
        if bomber_pos[1] + 1 < len(game_map[0]) and game_map[bomber_pos[0]][bomber_pos[1] + 1] != 1:
            if cost_map[bomber_pos[0]][bomber_pos[1] + 1] is None \
                    or cost_map[bomber_pos[0]][bomber_pos[1] + 1] > move_cost:
                if game_map[bomber_pos[0]][bomber_pos[1] + 1] == 2:
                    AgentAI.fill_cost_map_rec(cost_map, game_map, bomb_radius, [bomber_pos[0], bomber_pos[1] + 1],
                                              move_cost + 2 * bomb_radius + 11)
                elif game_map[bomber_pos[0]][bomber_pos[1] + 1] == 0:
                    AgentAI.fill_cost_map_rec(cost_map, game_map, bomb_radius, [bomber_pos[0], bomber_pos[1] + 1],
                                              move_cost + 1)
    @staticmethod
    def a_star_pathing(bomber_pos, objective_pos, game_map, pass_walls):
        open_list = []
        closed_list = []
        if game_map[objective_pos[1]][objective_pos[0]] == 3:
            return [bomber_pos]
        new_objective = AgentAI.adjust_objective(bomber_pos, objective_pos, game_map)
        open_list.append(SearchNode(None, bomber_pos))
        while open_list:
            current_node = AgentAI.get_lowest_f_value_node_in_list(open_list)
            open_list.remove(current_node)
            closed_list.append(current_node)
            if current_node.position == new_objective:
                tmp_node = current_node
                path = []
                while tmp_node.parent is not None:
                    path.append(tmp_node.position)
                    tmp_node = tmp_node.parent
                if path:
                    return [path[-1]]
            child_nodes = []
            if current_node.position[0] > 1 \
                    and game_map[current_node.position[1]][current_node.position[0] - 1] != 1 \
                    and game_map[current_node.position[1]][current_node.position[0] - 1] != 3 \
                    and game_map[current_node.position[1]][current_node.position[0] - 1] != 4 \
                    and current_node.position[0] + 2 >= objective_pos[0]:
                if pass_walls or game_map[current_node.position[1]][current_node.position[0] - 1] != 2 \
                        or [current_node.position[0] - 1, current_node.position[1]] == objective_pos:
                    child_nodes.append(SearchNode(current_node,
                                                  [current_node.position[0] - 1, current_node.position[1]]))
            if current_node.position[0] < len(game_map[0]) - 1 \
                    and game_map[current_node.position[1]][current_node.position[0] + 1] != 1 \
                    and game_map[current_node.position[1]][current_node.position[0] + 1] != 3 \
                    and game_map[current_node.position[1]][current_node.position[0] + 1] != 4 \
                    and current_node.position[0] - 2 <= objective_pos[0]:
                if pass_walls or game_map[current_node.position[1]][current_node.position[0] + 1] != 2 \
                        or [current_node.position[0] + 1, current_node.position[1]] == objective_pos:
                    child_nodes.append(SearchNode(current_node,
                                                  [current_node.position[0] + 1, current_node.position[1]]))
            if current_node.position[1] > 1 \
                    and game_map[current_node.position[1] - 1][current_node.position[0]] != 1 \
                    and game_map[current_node.position[1] - 1][current_node.position[0]] != 3 \
                    and game_map[current_node.position[1] - 1][current_node.position[0]] != 4 \
                    and current_node.position[1] + 2 >= objective_pos[1]:
                if pass_walls or game_map[current_node.position[1] - 1][current_node.position[0]] != 2 \
                        or [current_node.position[0], current_node.position[1] - 1] == objective_pos:
                    child_nodes.append(SearchNode(current_node,
                                                  [current_node.position[0], current_node.position[1] - 1]))
            if current_node.position[1] < len(game_map) - 1 \
                    and game_map[current_node.position[1] + 1][current_node.position[0]] != 1 \
                    and game_map[current_node.position[1] + 1][current_node.position[0]] != 3 \
                    and game_map[current_node.position[1] + 1][current_node.position[0]] != 4 \
                    and current_node.position[1] - 2 <= objective_pos[1]:
                if pass_walls or game_map[current_node.position[1] + 1][current_node.position[0]] != 2 \
                        or [current_node.position[0], current_node.position[1] + 1] == objective_pos:
                    child_nodes.append(SearchNode(current_node,
                                                  [current_node.position[0], current_node.position[1] + 1]))
            for child in child_nodes:
                if closed_list.__contains__(child):
                    continue
                child.gCost = current_node.gCost + 1
                child.hCost = math.hypot(bomber_pos[0] - child.position[0], bomber_pos[1] - child.position[1])
                child.fCost = child.gCost + child.hCost
                if AgentAI.is_node_cheaper_in_open_list(child, open_list):
                    continue
                open_list.append(child)
        return [bomber_pos]
    @staticmethod
    def get_lowest_f_value_node_in_list(node_list):
        best_node = None
        for node in node_list:
            if best_node is None:
                best_node = node
            elif node.fCost < best_node.fCost:
                best_node = node
        return best_node
    @staticmethod
    def is_node_cheaper_in_open_list(node, list):
        for tmp_node in list:
            if tmp_node == node and node.gCost <= tmp_node.gCost:
                return True
        return False
    @staticmethod
    def adjust_objective(bomber_pos, objective, game_map):
        center = [int((len(game_map[0]) - 2) / 2) + 1, int((len(game_map) - 2) / 2) + 1]
        new_objective = []
        if bomber_pos[0] < objective[0]:
            if bomber_pos[0] < center[0] <= objective[0]:
                new_objective.append(center[0])
            else:
                new_objective.append(objective[0])
        elif bomber_pos[0] > objective[0]:
            if bomber_pos[0] > center[0] >= objective[0]:
                new_objective.append(center[0])
            else:
                new_objective.append(objective[0])
        else:
            new_objective.append(bomber_pos[0])
        if bomber_pos[1] < objective[1]:
            if bomber_pos[1] < center[1] <= objective[1]:
                new_objective.append(center[1])
            else:
                new_objective.append(objective[1])
        elif bomber_pos[1] > objective[1]:
            if bomber_pos[1] > center[1] >= objective[1]:
                new_objective.append(center[1])
            else:
                new_objective.append(objective[1])
        else:
            new_objective.append(bomber_pos[1])
        return new_objective
    @staticmethod
    def get_safe_position_list(bomber_pos, bomb_pos, bomb_radius, in_map, parent=[0, 0], safes=[]):
        tmp_safes = []
        if bomb_radius < 0 or (bomber_pos[0] != bomb_pos[0] and bomber_pos[1] != bomb_pos[1]):
            tmp_safes.append(bomber_pos)
        else:
            if in_map[bomber_pos[1]][bomber_pos[0] - 1] == 0 and [bomber_pos[0] - 1, bomber_pos[1]] != parent:
                AgentAI.get_safe_position_list([bomber_pos[0] - 1, bomber_pos[1]], bomb_pos, bomb_radius - 1,
                                               in_map, bomber_pos, safes)
            if in_map[bomber_pos[1]][bomber_pos[0] + 1] == 0 and [bomber_pos[0] + 1, bomber_pos[1]] != parent:
                AgentAI.get_safe_position_list([bomber_pos[0] + 1, bomber_pos[1]], bomb_pos, bomb_radius - 1,
                                               in_map, bomber_pos, safes)
            if in_map[bomber_pos[1] - 1][bomber_pos[0]] == 0 and [bomber_pos[0], bomber_pos[1] - 1] != parent:
                AgentAI.get_safe_position_list([bomber_pos[0], bomber_pos[1] - 1], bomb_pos, bomb_radius - 1,
                                               in_map, bomber_pos, safes)
            if in_map[bomber_pos[1] + 1][bomber_pos[0]] == 0 and [bomber_pos[0], bomber_pos[1] + 1] != parent:
                AgentAI.get_safe_position_list([bomber_pos[0], bomber_pos[1] + 1], bomb_pos, bomb_radius - 1,
                                               in_map, bomber_pos, safes)
        if tmp_safes:
            for safe in tmp_safes:
                if AgentAI.spot_is_safe(safe, bomb_pos, bomb_radius):
                    safes.append(safe)
    @staticmethod
    def get_safe_spot(bomber_pos, bomb_pos, closest_enemy, bomb_radius, in_map, parent=[0, 0], safes=[]):
        AgentAI.get_safe_position_list(bomber_pos, bomb_pos, bomb_radius, in_map, safes=safes)
        tmp_safes = safes.copy()
        if closest_enemy is not None:
            tmp_safes = AgentAI.filter_safes_by_closest_enemy(bomber_pos, safes, closest_enemy)
        if tmp_safes:
            return random.choice(tmp_safes)
        elif safes:
            return random.choice(safes)
        else:
            return [1, 1]
    @staticmethod
    def spot_is_safe(spot, bomb_pos, bomb_radius):
        if spot[0] < bomb_pos[0] - bomb_radius \
                or spot[0] > bomb_pos[0] + bomb_radius \
                or spot[1] < bomb_pos[1] - bomb_radius \
                or spot[1] > bomb_pos[1] + bomb_radius \
                or (spot[0] != bomb_pos[0] and spot[1] != bomb_pos[1]):
            return True
        else:
            return False
    @staticmethod
    def filter_safes_by_closest_enemy(bomber_pos, safes, closest_enemy):
        tmp_safes = []
        for safe in safes:
            if safe[0] <= bomber_pos[0] < closest_enemy[0] \
                    or safe[1] <= bomber_pos[1] < closest_enemy[1] \
                    or closest_enemy[0] < bomber_pos[0] <= safe[0] \
                    or closest_enemy[1] < bomber_pos[1] <= safe[1]:
                tmp_safes.append(safe)
        return tmp_safes
import math
class Destroy_enemies:
    @staticmethod
    def dist_cal(x,y):
        return math.hypot(x[0] - y[0], x[1] - y[1])
    @staticmethod
    def closest_wall(player, walls):
        dist = float("inf")
        closest_wall = []
        for wall in walls:
            new_dist = Destroy_enemies.dist_cal(player, wall)
            if new_dist < dist:
                dist = new_dist
                closest_wall = wall
        return closest_wall
    @staticmethod
    def enemy_is_in_range(player, enemy_pos, rang=1):
        if not enemy_pos:
            return False
        if player[1] % 2 != 0:
            if math.fabs(player[0] - enemy_pos[0]) <= rang and player[1] == enemy_pos[1]:
                return True
        if player[0] % 2 != 0:
            if math.fabs(player[1] - enemy_pos[1]) <= rang and player[0] == enemy_pos[0]:
                return True
        else:
            return False
    @staticmethod
    def place_drop_bomb(drop_bomb_place, game_map, direction, tmp=1):
        n_target = drop_bomb_place
        ciclo = 0
        while tmp != 0:
            n_target = [n_target[0] + direction[0], n_target[1] + direction[1]]
            if 31 <= n_target[0] <= 0 or 51 <= n_target[1] <= 0:
                break
            if game_map[n_target[1]][n_target[0]] > 0:
                if direction == [0, -1]:
                    direction = [-1, 0]
                elif direction == [-1, 0]:
                    direction = [0, 1]
                elif direction == [0, 1]:
                    direction = [1, 0]
                else:
                    direction = [0, -1]
                ciclo += 1
                if ciclo == 5:
                    break
                n_target = drop_bomb_place
            else:
                tmp -= 1
                drop_bomb_place = n_target
        return drop_bomb_place, direction
import math
class dest:
    @staticmethod
    def distance_points(point1, point2):
        return math.sqrt((point2[0] - point1[0]) ** 2 + (point2[1] - point1[1]) ** 2)
    @staticmethod
    def close_position(distances):
        small = distances[0]
        index = 0
        for ind, dist in enumerate(distances):
            if dist < small:
                small = dist
                index = ind
        return index
class SearchNode:
    def __init__(self,parent=None,position=None):
        self.parent = parent
        self.position = position
        self.gCost = 0
        self.hCost = 0
        self.fCost = 0
    def __eq__(self, other):
        return self.position == other.position
