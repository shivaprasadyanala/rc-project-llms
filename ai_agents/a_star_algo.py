import heapq
import time

TILE_SIZE = 25

def to_grid(pos):
    return (pos[0] // TILE_SIZE, pos[1] // TILE_SIZE)

def to_pixel(pos):
    return (pos[0] * TILE_SIZE, pos[1] * TILE_SIZE)

def heuristic(a, b):
    # Manhattan distance
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def astar(start_px: tuple[int, int], goal_px: tuple[int, int], obstacles_px:list[tuple[int, int]], grid_width=32, grid_height=24)->str:
    """
        a star algorithm which takes the start pixal, goal fixal, obstacle pixal, grid width, and grid height
        to calculate the path from the starting point to the goal by dodging the obstacles.
        And should not include goal in obstacles list
        Args:
          start_px int,int: x,y coordinates of start
          goal_px int,int: x,y coordinate of goal
          obstacles_px [(int,int)] : x,y coordinate of obstacles
      Returns:
        List: The list of tuples of the player coordinates to reach the destination
    
        A sample input for the function
        start_px = (50,75)
        goal_px = (150,125)

        obstacles = [
            (75, 75),
        (100, 75),
        (125, 75)
    ]
    
    """
    # print(type(start_px))
    # print((start_px))
    # print((goal_px))
    # print(obstacles_px)
    
    try:
        print("astar called")
        new_st = (int(start_px[0]),int(start_px[1]))
        new_goal = ( int(goal_px[0]),int(goal_px[1]))
        # print(new_goal)
        # print(new_st)
        start = to_grid(new_st)
        goal = to_grid(new_goal)

        if all(isinstance(x, tuple) for x in obstacles_px):
            if tuple(goal_px) in obstacles_px:
                return "goal cannot be an obstacle. please pass the correct arguments."
        else:
            if list(goal_px) in obstacles_px:
                 return "goal cannot be an obstacle. please pass the correct arguments."


        # Early validation: Check if start or goal are inherently out of bounds
        if start[0] < 0 or start[1] < 0 or start[0] >= int(grid_width) or start[1] >= int(grid_height):
            return "None (Start coordinate is out of bounds)"
        if goal[0] < 0 or goal[1] < 0 or goal[0] >= int(grid_width) or goal[1] >= int(grid_height):
            return "None (Goal coordinate is out of bounds)"
        
        obstacles =set()
        for obstacle in obstacles_px:
            # obstacle_tuple = (obstacle[0],obstacle[1])
            obstacles.add(to_grid((obstacle[0],obstacle[1])))

        # print(obstacles)
        open_set = []
        heapq.heappush(open_set, (0, start))

        came_from = {}
        g_score = {start: 0}

        while open_set:
            _, current = heapq.heappop(open_set)
            # print(current,goal)
            if current == goal:
                # reconstruct path
                path = []
                while current in came_from:
                    path.append(to_pixel(current))
                    current = came_from[current]
                path.append(to_pixel(start))
                path.reverse()
                return f"path from start to destination is: {path}"
                # return path

            x, y = current

            neighbors = [
                (x+1, y),
                (x-1, y),
                (x, y+1),
                (x, y-1),
            ]

            for nx, ny in neighbors:
                neighbor = (nx, ny)

                # bounds check
                if nx < 0 or ny < 0 or nx >= int(grid_width) or ny >= int(grid_height):
                    continue

                # obstacle check
                if neighbor in obstacles:
                    continue

                tentative_g = g_score[current] + 1

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score, neighbor))

        return None  # no path found
    except Exception as e:
        return "pass correct argument to the tool."



start = [200, 100]
goal = [75, 250]

# goals = [[300, 275],[600, 275],[200, 375],[500, 225],[250, 250],[100, 75],[450, 155],[600, 175],[300, 575]]

# obstacles = [
#     (75, 75),
#     (100, 75),
#     (125, 75),
#     (200,100),
#     (75,250)
# ]

obstacles = [
    [125, 75],
    [200,100],
    [75,250]
]
# print(astar(start, goal, obstacles, grid_width=32, grid_height=24))

# path = (astar(start[3], goal[3], obstacles, grid_width=32, grid_height=24))
# print(path)
# print(len(path))

# st_time = time.time()
# for goal in goals:
#     print(goal)
#     path = astar(start, goal, obstacles, grid_width=32, grid_height=24)
#     print(path)
# end_time = time.time()

# print("time taken:")
# print(st_time)
# print(end_time)
# print(end_time-st_time)

# print(path)



