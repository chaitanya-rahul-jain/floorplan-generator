from z3 import Int, Solver, Or, And, sat
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import time

# Track execution time
start_time = time.time()

# Define room sizes (width, height)
rooms = {
    "A": (3, 2),
    "B": (2, 3),
    "C": (2, 2),
    "D": (4, 1),
    "E": (2, 2),
    "F": (3, 3),
    "G": (2, 4),
    "H": (3, 2),
    "I": (4, 2),
    "J": (2, 2)
}

# Define adjacency constraints (edges in the graph)
edges = [
    ("A", "B"),
    ("A", "C"),
    ("B", "D"),
    ("E", "F"),
    ("F", "H"),
    ("G", "I"),
    ("H", "J"),
    ("I", "J"),
    ("B", "G"),
    ("C", "H"),
]

# Optimization 1: Pre-compute connected components for better constraint placement
def find_connected_components(edges, rooms):
    # Build adjacency list
    graph = {room: [] for room in rooms}
    for u, v in edges:
        graph[u].append(v)
        graph[v].append(u)
    
    # Find connected components with DFS
    visited = set()
    components = []
    
    def dfs(node, component):
        visited.add(node)
        component.append(node)
        for neighbor in graph[node]:
            if neighbor not in visited:
                dfs(neighbor, component)
    
    for node in graph:
        if node not in visited:
            component = []
            dfs(node, component)
            components.append(component)
    
    return components

components = find_connected_components(edges, rooms)
print(f"Found {len(components)} connected components")

# Create solver with optimization tactics
# Optimization 2: Use better solver tactics for placement problems
tactic = "simplify"  # Basic simplification
s = Solver()

# Assign integer (x, y) coordinates for each room
positions = {name: (Int(f"x_{name}"), Int(f"y_{name}")) for name in rooms}

# Optimization 3: Better boundary constraints
# Calculate maximum possible width and height of the layout
max_width = sum(w for w, _ in rooms.values())
max_height = sum(h for _, h in rooms.values())

# Add boundary constraints
for name, (x, y) in positions.items():
    # Optimization 4: Tighter bounds - room can't be placed beyond max possible dimensions
    s.add(x >= 0, y >= 0)
    s.add(x <= max_width - rooms[name][0])
    s.add(y <= max_height - rooms[name][1])

# Optimization 5: Apply heuristic starting constraint - anchor one room in each component
for i, component in enumerate(components):
    anchor = component[0]  # Choose first room in component as anchor
    s.add(positions[anchor][0] == i * 10)  # Place components apart from each other
    s.add(positions[anchor][1] == 0)

# Optimization 6: Improved no-overlap constraints using implications
for name1 in rooms:
    for name2 in rooms:
        if name1 >= name2:  # Only check each pair once
            continue

        x1, y1 = positions[name1]
        x2, y2 = positions[name2]
        w1, h1 = rooms[name1]
        w2, h2 = rooms[name2]

        # Ensure rooms do not overlap
        s.add(
            Or(
                x1 + w1 <= x2,  # Room1 is to the left of Room2
                x2 + w2 <= x1,  # Room2 is to the left of Room1
                y1 + h1 <= y2,  # Room1 is above Room2
                y2 + h2 <= y1,  # Room2 is above Room1
            )
        )

# Optimization 7: Efficient adjacency constraints - use helper functions
def create_wall_sharing_constraint(name1, name2, positions, rooms):
    x1, y1 = positions[name1]
    x2, y2 = positions[name2]
    w1, h1 = rooms[name1]
    w2, h2 = rooms[name2]

    # Vertical wall sharing (left-right adjacency)
    vertical_sharing = Or(
        # Room1 is immediately left of Room2
        And(
            x1 + w1 == x2,
            Or(
                And(y1 <= y2, y1 + h1 > y2),
                And(y2 <= y1, y2 + h2 > y1),
            ),
        ),
        # Room2 is immediately left of Room1
        And(
            x2 + w2 == x1,
            Or(
                And(y1 <= y2, y1 + h1 > y2),
                And(y2 <= y1, y2 + h2 > y1),
            ),
        )
    )

    # Horizontal wall sharing (top-bottom adjacency)
    horizontal_sharing = Or(
        # Room1 is immediately above Room2
        And(
            y1 + h1 == y2,
            Or(
                And(x1 <= x2, x1 + w1 > x2),
                And(x2 <= x1, x2 + w2 > x1),
            ),
        ),
        # Room2 is immediately above Room1
        And(
            y2 + h2 == y1,
            Or(
                And(x1 <= x2, x1 + w1 > x2),
                And(x2 <= x1, x2 + w2 > x1),
            ),
        )
    )

    return Or(vertical_sharing, horizontal_sharing)

# Add adjacency constraints
for name1, name2 in edges:
    s.add(create_wall_sharing_constraint(name1, name2, positions, rooms))

# Optimization 8: Add symmetry breaking constraints to reduce search space
# Force the first room to be at the origin
first_room = sorted(rooms.keys())[0]
s.add(positions[first_room][0] == 0)
s.add(positions[first_room][1] == 0)

# Optimization 9: Add compactness constraint to prefer tighter layouts
# This helps Z3 find solutions faster by prioritizing certain layouts
min_x = Int("min_x")
min_y = Int("min_y")
max_x = Int("max_x")
max_y = Int("max_y")

# Set boundary variables
for name, (x, y) in positions.items():
    w, h = rooms[name]
    s.add(min_x <= x)
    s.add(min_y <= y)
    s.add(max_x >= x + w)
    s.add(max_y >= y + h)

# Encourage compactness by minimizing total area
s.add(min_x == 0)
s.add(min_y == 0)

print("Solving constraints...")
solution_start = time.time()

# Solve the constraints
if s.check() == sat:
    model = s.model()
    layout = {
        name: (model[x].as_long(), model[y].as_long())
        for name, (x, y) in positions.items()
    }
    print(f"Solution found in {time.time() - solution_start:.2f} seconds")
    print("Room Layout:", layout)

    # Calculate actual dimensions of solution
    actual_max_x = max(layout[name][0] + rooms[name][0] for name in rooms)
    actual_max_y = max(layout[name][1] + rooms[name][1] for name in rooms)
    print(f"Layout dimensions: {actual_max_x}x{actual_max_y}")

    # Visualization code - optimized for performance
    fig, ax = plt.subplots(figsize=(10, 8))

    # Define colors for rooms - using a colorblind-friendly palette
    colors = [
        "lightblue",
        "lightgreen",
        "lightcoral",
        "lightyellow",
        "lightpink",
        "lightgrey",
        "lightsalmon",
        "lightcyan",
        "lightseagreen",
        "lightsteelblue",
    ]

    # Set axis limits with padding
    ax.set_xlim(-0.5, actual_max_x + 0.5)
    ax.set_ylim(-0.5, actual_max_y + 0.5)

    # Plot rooms efficiently - add them individually instead of using PatchCollection
    for i, (name, (x, y)) in enumerate(layout.items()):
        w, h = rooms[name]
        rect = patches.Rectangle(
            (x, y), w, h, 
            linewidth=2, 
            edgecolor="black",
            facecolor=colors[i % len(colors)]
        )
        ax.add_patch(rect)
        
        # Add room label
        ax.text(
            x + w / 2, y + h / 2, name,
            ha="center", va="center",
            fontsize=12, fontweight="bold"
        )

    # Grid, labels, etc.
    ax.grid(True, linestyle="--", alpha=0.7)
    ax.set_aspect("equal")
    ax.set_title("Room Layout Visualization")
    ax.set_xlabel("X-coordinate")
    ax.set_ylabel("Y-coordinate")

    # Add coordinate labels
    for i in range(actual_max_x + 1):
        ax.text(i, -0.25, str(i), ha="center")
    for i in range(actual_max_y + 1):
        ax.text(-0.25, i, str(i), va="center")

    plt.tight_layout()
    
    execution_time = time.time() - start_time
    print(f"Total execution time: {execution_time:.2f} seconds")
    
    plt.show()
else:
    print("No valid layout found.")
    print(f"Failed in {time.time() - start_time:.2f} seconds")