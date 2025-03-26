from z3 import Int, Solver, Or, And, sat, Not
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.gridspec as gridspec

# Define room sizes (width, height)
rooms = {"A": (3, 2), "B": (2, 3), "C": (2, 2), "D": (4, 1), "E": (2, 2), "F": (5, 6)}

# Define adjacency constraints (edges in the graph)
edges = [("A", "B"), ("A", "C"), ("B", "D"), ("C", "E"), ("E", "F")]

# Function to create a solver with all constraints
def create_solver():
    s = Solver()
    
    # Assign integer (x, y) coordinates for each room
    positions = {name: (Int(f"x_{name}"), Int(f"y_{name}")) for name in rooms}
    
    # Optional: Add boundary constraints to keep coordinates positive
    for name, (x, y) in positions.items():
        s.add(x >= 0, y >= 0)
    
    # No overlap constraint
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
    
    return s, positions

# Function to visualize a layout
def visualize_layout(layout, ax, title="Room Layout"):
    # Define colors for rooms
    colors = [
        "lightblue", "lightgreen", "lightcoral", "lightyellow", 
        "lightpink", "lightgrey", "lightsalmon", "lightcyan", 
        "lightseagreen", "lightsteelblue"
    ]
    
    # Calculate boundaries for plot
    max_x = max(layout[name][0] + rooms[name][0] for name in rooms)
    max_y = max(layout[name][1] + rooms[name][1] for name in rooms)
    
    # Set axis limits with some padding
    ax.set_xlim(-0.5, max_x + 0.5)
    ax.set_ylim(-0.5, max_y + 0.5)
    
    # Plot each room
    for i, (name, (x, y)) in enumerate(layout.items()):
        w, h = rooms[name]
        rect = patches.Rectangle(
            (x, y), w, h, linewidth=2, edgecolor="black", facecolor=colors[i % len(colors)]
        )
        ax.add_patch(rect)
        
        # Add room label in the center
        ax.text(
            x + w / 2, y + h / 2, name, ha="center", va="center", fontsize=12, fontweight="bold"
        )
    
    # Add grid lines
    ax.grid(True, linestyle="--", alpha=0.7)
    
    # Set equal aspect ratio so squares look like squares
    ax.set_aspect("equal")
    
    # Set title
    ax.set_title(title)
    
    # Add labels for coordinates
    for i in range(max_x + 1):
        ax.text(i, -0.25, str(i), ha="center")
    for i in range(max_y + 1):
        ax.text(-0.25, i, str(i), va="center")

# Find multiple solutions
num_solutions = 10
solutions = []

s, positions = create_solver()
for i in range(num_solutions):
    if s.check() == sat:
        model = s.model()
        layout = {
            name: (model[x].as_long(), model[y].as_long())
            for name, (x, y) in positions.items()
        }
        solutions.append(layout)
        print(f"Solution {i+1}:", layout)
        
        # Add a constraint to exclude this solution
        # Create a constraint that at least one room must be in a different position
        block_constraint = []
        for name, (x, y) in positions.items():
            block_constraint.append(
                Or(
                    x != model[x],
                    y != model[y]
                )
            )
        s.add(Or(block_constraint))
    else:
        print(f"Found {len(solutions)} solutions. No more solutions exist.")
        break

# Visualize all solutions
if solutions:
    # Calculate grid size
    cols = min(3, len(solutions))
    rows = (len(solutions) + cols - 1) // cols
    
    fig = plt.figure(figsize=(5*cols, 4*rows))
    gs = gridspec.GridSpec(rows, cols)
    
    for i, layout in enumerate(solutions):
        ax = plt.subplot(gs[i // cols, i % cols])
        visualize_layout(layout, ax, f"Solution {i+1}")
    
    plt.tight_layout()
    plt.show()
else:
    print("No valid layout found.")