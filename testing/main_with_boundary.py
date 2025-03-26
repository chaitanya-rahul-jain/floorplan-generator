from z3 import Int, Solver, Or, And, sat, Not
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import time

# Track execution time
start_time = time.time()

# Define boundary parameters
outer_square_size = 12
inner_square_start = 4
inner_square_size = 4 

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

s = Solver()

# Assign integer (x, y) coordinates for each room
positions = {name: (Int(f"x_{name}"), Int(f"y_{name}")) for name in rooms}

# Ensure all coordinates are positive
for name, (x, y) in positions.items():
    s.add(x >= 0, y >= 0)

# O-shaped boundary constraints
for name, (x, y) in positions.items():
    w, h = rooms[name]
    
    # Room must be within the outer square boundary
    s.add(x + w <= outer_square_size)
    s.add(y + h <= outer_square_size)
    
    # Room must not overlap with the inner square
    # We need to ensure either:
    # 1. Room is completely to the left of inner square, OR
    # 2. Room is completely to the right of inner square, OR
    # 3. Room is completely above inner square, OR
    # 4. Room is completely below inner square
    inner_x_end = inner_square_start + inner_square_size
    inner_y_end = inner_square_start + inner_square_size
    
    s.add(Or(
        x + w <= inner_square_start,              # Room is to the left of inner square
        x >= inner_x_end,                         # Room is to the right of inner square
        y + h <= inner_square_start,              # Room is below inner square
        y >= inner_y_end                          # Room is above inner square
    ))

# No overlap constraint between rooms
for name1 in rooms:
    for name2 in rooms:
        if name1 >= name2:  # Only check each pair once (and skip self-checks)
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

# Adjacency constraints (force rooms to share walls)
for name1, name2 in edges:
    x1, y1 = positions[name1]
    x2, y2 = positions[name2]
    w1, h1 = rooms[name1]
    w2, h2 = rooms[name2]

    # Room1 is immediately left of Room2
    left_of = And(
        x1 + w1 == x2,
        Or(
            And(y1 <= y2, y1 + h1 > y2),  # Partial overlap
            And(y2 <= y1, y2 + h2 > y1),  # Partial overlap
        ),
    )

    # Room2 is immediately left of Room1
    right_of = And(
        x2 + w2 == x1,
        Or(
            And(y1 <= y2, y1 + h1 > y2),  # Partial overlap
            And(y2 <= y1, y2 + h2 > y1),  # Partial overlap
        ),
    )

    # Room1 is immediately above Room2
    above = And(
        y1 + h1 == y2,
        Or(
            And(x1 <= x2, x1 + w1 > x2),  # Partial overlap
            And(x2 <= x1, x2 + w2 > x1),  # Partial overlap
        ),
    )

    # Room2 is immediately above Room1
    below = And(
        y2 + h2 == y1,
        Or(
            And(x1 <= x2, x1 + w1 > x2),  # Partial overlap
            And(x2 <= x1, x2 + w2 > x1),  # Partial overlap
        ),
    )

    # One of these conditions must be true
    s.add(Or(left_of, right_of, above, below))

# Solve the constraints
if s.check() == sat:
    model = s.model()
    layout = {
        name: (model[x].as_long(), model[y].as_long())
        for name, (x, y) in positions.items()
    }
    print("Room Layout:", layout)

    # Visualization with matplotlib
    fig, ax = plt.subplots(figsize=(10, 8))

    # Define colors for rooms
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

    # Plot the boundary
    # Outer square
    outer_rect = patches.Rectangle(
        (0, 0),
        outer_square_size,
        outer_square_size,
        linewidth=2,
        edgecolor="blue",
        facecolor="none",
        linestyle='-',
        alpha=0.7
    )
    ax.add_patch(outer_rect)
    
    # Inner square (the hole)
    inner_rect = patches.Rectangle(
        (inner_square_start, inner_square_start),
        inner_square_size,
        inner_square_size,
        linewidth=2,
        edgecolor="red",
        facecolor="red",
        alpha=0.3
    )
    ax.add_patch(inner_rect)

    # Plot each room
    for i, (name, (x, y)) in enumerate(layout.items()):
        w, h = rooms[name]
        rect = patches.Rectangle(
            (x, y),
            w,
            h,
            linewidth=2,
            edgecolor="black",
            facecolor=colors[i % len(colors)],
        )
        ax.add_patch(rect)

        # Add room label in the center
        ax.text(
            x + w / 2,
            y + h / 2,
            name,
            ha="center",
            va="center",
            fontsize=12,
            fontweight="bold",
        )

    # Add grid lines
    ax.grid(True, linestyle="--", alpha=0.7)

    # Set equal aspect ratio so squares look like squares
    ax.set_aspect("equal")

    # Set axis limits with some padding
    ax.set_xlim(-0.5, outer_square_size + 0.5)
    ax.set_ylim(-0.5, outer_square_size + 0.5)

    # Set title and labels
    ax.set_title("Room Layout in O-shaped Boundary")
    ax.set_xlabel("X-coordinate")
    ax.set_ylabel("Y-coordinate")

    # Add labels for coordinates
    for i in range(outer_square_size + 1):
        ax.text(i, -0.25, str(i), ha="center")
    for i in range(outer_square_size + 1):
        ax.text(-0.25, i, str(i), va="center")

    plt.tight_layout()

    execution_time = time.time() - start_time
    print(f"Total execution time: {execution_time:.2f} seconds")
    
    plt.show()
else:
    print("No valid layout found.")