import heapq

TILE_SIZE = 25

def to_grid(pos):
    return (pos[0] // TILE_SIZE, pos[1] // TILE_SIZE)

def to_pixel(pos):
    return (pos[0] * TILE_SIZE, pos[1] * TILE_SIZE)

def heuristic(a, b):
    # Manhattan distance
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def astar(start_px, goal_px, obstacles_px, grid_width=800, grid_height=600):
    """
        a star algorithm which takes the start pixal, goal fixal, obstacle pixal, grid width, and gird height
        to calculate the path from the starting point to the goal by dodging the obstacles.
        Args:
          start_px (int,int): x,y coordinates of start
          goal_px (int,int): x,y coordinate of goal
          obstacles_px [(int,int)] : x,y coordinate of obstacles
      Returns:
        List: The list of tuples of the player coordinates to reach the destination
    
        A sample input for the function
        start = (50, 75)
        goal = (150, 125)

        obstacles = [
            (75, 75),
        (100, 75),
        (125, 75)
    ]
    
    """
    print(type(start_px))
    print((start_px))

    # start_px.split(",")[0]
    # start_px.split(",")[1]
    new_st = (int(start_px.split(",")[0]),int(start_px.split(",")[1]))
    new_goal = ( int(goal_px.split(",")[0]),int(goal_px.split(",")[1]))
    print(new_goal)
    print(new_st)
    start = to_grid(new_st)
    goal = to_grid(new_goal)
    print(obstacles_px)
    # obstacles = {to_grid(o) for o in obstacles_px}

    obstacles.append(to_grid((int(obstacles_px.split(",")[0]),int(obstacles_px.split(",")[1]))))

    print(obstacles)
    open_set = []
    heapq.heappush(open_set, (0, start))

    came_from = {}
    g_score = {start: 0}

    while open_set:
        _, current = heapq.heappop(open_set)

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



start = (50, 75)
goal = (150, 125)

obstacles = [
    (75, 75),
    (100, 75),
    (125, 75)
]

# path = astar(start, goal, obstacles, grid_width=20, grid_height=20)

# print(path)



######################################




# import heapq

# TILE_SIZE = 25

# DIRS = [
#     ("UP", (0, -1)),
#     ("LEFT", (-1, 0)),
#     ("RIGHT", (1, 0)),
#     ("DOWN", (0, 1)),
# ]

# def to_grid(pos):
#     """
#     Convert pixel coordinates into grid coordinates.

#     Example:
#         (50, 75) -> (2, 3)

#     Since each tile is 25 pixels wide/high:
#         x_grid = x_pixel // 25
#         y_grid = y_pixel // 25

#     Args:
#         pos (tuple):
#             Pixel coordinates (x, y)

#     Returns:
#         tuple:
#             Grid coordinates (grid_x, grid_y)
#     """
#     return (pos[0] // TILE_SIZE, pos[1] // TILE_SIZE)

# def astar_next_move(start_px, goal_px, obstacles_px,
#                     crops_px=None,
#                     grid_width=800,
#                     grid_height=600):
#     """
#     Compute the NEXT optimal movement step using A* pathfinding.

#     This function is designed for deterministic game-agent navigation.

#     ---------------------------------------------------------
#     MOVEMENT RULES
#     ---------------------------------------------------------
#     - Movement is restricted to:
#         UP, DOWN, LEFT, RIGHT

#     - No diagonal movement allowed.

#     - Each move traverses exactly one tile.

#     ---------------------------------------------------------
#     BLOCKED TILES
#     ---------------------------------------------------------
#     - Obstacles are always blocked.

#     - Crops are blocked UNLESS:
#         the crop tile is the goal tile.

#     - The agent cannot move outside the map.

#     ---------------------------------------------------------
#     DETERMINISM
#     ---------------------------------------------------------
#     If multiple shortest paths exist:
#         UP > LEFT > RIGHT > DOWN

#     This ensures stable and reproducible movement.

#     ---------------------------------------------------------
#     INPUT FORMAT
#     ---------------------------------------------------------

#     Pixel coordinates are expected.

#     Example:
#         start_px = (50, 75)
#         goal_px  = (150, 125)

#     Obstacles:
#         [
#             (75, 75),
#             (100, 75),
#             (125, 75)
#         ]

#     Crops:
#         [
#             (200, 100),
#             (225, 100)
#         ]

#     ---------------------------------------------------------
#     RETURNS
#     ---------------------------------------------------------

#     One of:
#         "UP"
#         "DOWN"
#         "LEFT"
#         "RIGHT"
#         "STUCK"

#     The function returns ONLY the next movement step,
#     not the full path.

#     ---------------------------------------------------------
#     WHY ONLY NEXT MOVE?
#     ---------------------------------------------------------

#     In real-time game agents:
#     - recalculating every frame is safer
#     - dynamic obstacles may appear
#     - world state may change

#     Returning only the next action keeps the system robust.

#     Args:
#         start_px (tuple):
#             Player pixel position (x, y)

#         goal_px (tuple):
#             Target pixel position (x, y)

#         obstacles_px (list):
#             List of obstacle pixel coordinates

#         crops_px (list | None):
#             List of crop pixel coordinates

#         grid_width (int):
#             World width in pixels

#         grid_height (int):
#             World height in pixels

#     Returns:
#         str:
#             UP / DOWN / LEFT / RIGHT / STUCK
#     """

#     start = to_grid(start_px)
#     goal = to_grid(goal_px)

#     obstacles = {to_grid(o) for o in obstacles_px}

#     crops = set()
#     if crops_px:
#         crops = {
#             to_grid(c)
#             for c in crops_px
#             if to_grid(c) != goal
#         }

#     blocked = obstacles | crops

#     grid_w = grid_width // TILE_SIZE
#     grid_h = grid_height // TILE_SIZE

#     open_set = []
#     counter = 0

#     heapq.heappush(open_set, (0, counter, start))

#     came_from = {}
#     g_score = {start: 0}

#     while open_set:
#         _, _, current = heapq.heappop(open_set)

#         if current == goal:
#             break

#         x, y = current

#         for _, (dx, dy) in DIRS:
#             nx, ny = x + dx, y + dy

#             if not (0 <= nx < grid_w and 0 <= ny < grid_h):
#                 continue

#             neighbor = (nx, ny)

#             if neighbor in blocked:
#                 continue

#             tentative = g_score[current] + 1

#             if tentative < g_score.get(neighbor, float("inf")):
#                 came_from[neighbor] = current
#                 g_score[neighbor] = tentative

#                 f = tentative + heuristic(neighbor, goal)

#                 counter += 1
#                 heapq.heappush(
#                     open_set,
#                     (f, counter, neighbor)
#                 )

#     if goal not in came_from and goal != start:
#         return "STUCK"

#     current = goal

#     while came_from.get(current) != start:
#         current = came_from[current]

#     dx = current[0] - start[0]
#     dy = current[1] - start[1]

#     if dy == -1:
#         return "UP"
#     if dx == -1:
#         return "LEFT"
#     if dx == 1:
#         return "RIGHT"
#     if dy == 1:
#         return "DOWN"

#     return "STUCK"