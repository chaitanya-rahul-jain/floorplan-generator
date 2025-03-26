from z3 import Int, Solver, Or, And, sat
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import time

# Track execution time
start_time = time.time()


# Function to get boundary definition from user
def get_user_boundary():
    print("Define your boundary:")
    print("1. Enter outer boundary dimensions as 'width height'")
    outer_width, outer_height = map(
        int, input("Outer boundary (width height): ").split()
    )

    # Get the number of "holes" in the boundary
    num_holes = int(input("Number of forbidden regions (holes): "))

    # Get the coordinates and dimensions of each hole
    holes = []
    for i in range(num_holes):
        print(f"For hole #{i+1}, enter 'x y width height':")
        x, y, width, height = map(int, input().split())
        holes.append((x, y, width, height))

    return outer_width, outer_height, holes


def visualize_boundary(ax, outer_width, outer_height, holes):
    # Draw outer boundary
    outer_rect = patches.Rectangle(
        (0, 0),
        outer_width,
        outer_height,
        linewidth=2,
        edgecolor="blue",
        facecolor="none",
        linestyle="-",
        alpha=0.7,
    )
    ax.add_patch(outer_rect)

    # Draw holes (forbidden regions)
    for i, (x, y, width, height) in enumerate(holes):
        hole_rect = patches.Rectangle(
            (x, y),
            width,
            height,
            linewidth=2,
            edgecolor="red",
            facecolor="red",
            alpha=0.3,
        )
        ax.add_patch(hole_rect)


def is_point_in_boundary(x, y, outer_width, outer_height, holes):
    """Check if a point is within the boundary (outside of all holes)"""
    # Check if point is within outer boundary
    if x < 0 or y < 0 or x >= outer_width or y >= outer_height:
        return False

    # Check if point is within any hole
    for hole_x, hole_y, hole_width, hole_height in holes:
        if hole_x <= x < hole_x + hole_width and hole_y <= y < hole_y + hole_height:
            return False

    return True


def main():
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
        "J": (2, 2),
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

    # Get boundary definition from user
    # For testing, uncomment this line and comment out the get_user_boundary() call
    # outer_width, outer_height, holes = 15, 15, [(5, 5, 5, 5)]  # Example: O-shaped boundary
    outer_width, outer_height, holes = get_user_boundary()

    s = Solver()

    # Assign integer (x, y) coordinates for each room
    # Initialize positions dictionary to store coordinate variables for each room


    positions = {}
    for name in rooms:
        x_coordinate = Int(f"x_{name}")  # Create a Z3 integer variable for x coordinate
        y_coordinate = Int(f"y_{name}")  # Create a Z3 integer variable for y coordinate
        positions[name] = (x_coordinate, y_coordinate)

    # Ensure all coordinates are positive
    for name, (x, y) in positions.items():
        s.add(x >= 0, y >= 0)

    # Custom boundary constraints
    for name, (x, y) in positions.items():
        w, h = rooms[name]

        # Room must be within the outer boundary
        s.add(x + w <= outer_width)
        s.add(y + h <= outer_height)

        # Room must not overlap with any of the holes
        for hole_x, hole_y, hole_width, hole_height in holes:
            # We ensure the room and hole don't overlap using the same logic as room-room non-overlap
            s.add(
                Or(
                    x + w <= hole_x,  # Room is to the left of hole
                    x >= hole_x + hole_width,  # Room is to the right of hole
                    y + h <= hole_y,  # Room is below hole
                    y >= hole_y + hole_height,  # Room is above hole
                )
            )

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

        # Visualize the boundary
        visualize_boundary(ax, outer_width, outer_height, holes)

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
        ax.set_xlim(-0.5, outer_width + 0.5)
        ax.set_ylim(-0.5, outer_height + 0.5)

        # Set title and labels
        ax.set_title("Room Layout with Custom Boundary")
        ax.set_xlabel("X-coordinate")
        ax.set_ylabel("Y-coordinate")

        # Add labels for coordinates
        for i in range(outer_width + 1):
            ax.text(i, -0.25, str(i), ha="center")
        for i in range(outer_height + 1):
            ax.text(-0.25, i, str(i), va="center")

        plt.tight_layout()

        execution_time = time.time() - start_time
        print(f"Total execution time: {execution_time:.2f} seconds")

        plt.show()
    else:
        print("No valid layout found.")
        
if __name__ == "__main__":
    main()