from z3 import Int, Solver, Or, And, sat
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import time


# take the input for the user boundary
def get_user_boundary():
    print("Define your boundary:")
    print("1. Enter outer boundary dimensions as 'width height'")
    outer_width, outer_height = map(
        int, input("Outer boundary (width height): ").split()
    )

    num_holes = int(input("Number of forbidden regions (holes): "))

    holes = []
    for i in range(num_holes):
        print(f"For hole #{i+1}, enter 'x y width height':")
        x, y, width, height = map(int, input().split())
        holes.append((x, y, width, height))

    return outer_width, outer_height, holes


# draws the boundary
def visualize_boundary(ax, outer_width, outer_height, holes):
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


def main():

    # Define the rooms
    rooms = {
        "A": (3, 2),
        "B": (2, 3),
        "C": (2, 2),
        "D": (1, 3),
        "E": (2, 2),
        "F": (3, 3),
        "G": (2, 4),
        "H": (3, 2),
        "I": (4, 2),
        "J": (2, 2),
    }

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
        ("A", "G"),
        ("A", "D"),
        ("A", "J"),
    ]

    # get the user boundary
    outer_width, outer_height, holes = get_user_boundary()

    # create the solver
    s = Solver()

    # create the variables
    positions = {}
    for name in rooms:
        x_coordinate = Int(f"x_{name}")
        y_coordinate = Int(f"y_{name}")
        positions[name] = (x_coordinate, y_coordinate)

    # first constraint - room can't be placed beyond max possible dimensions
    for name, (x, y) in positions.items():
        s.add(x >= 0, y >= 0)

    for name, (x, y) in positions.items():
        w, h = rooms[name]

        s.add(x + w <= outer_width)
        s.add(y + h <= outer_height)

        for hole_x, hole_y, hole_width, hole_height in holes:
            s.add(
                Or(
                    x + w <= hole_x,
                    x >= hole_x + hole_width,
                    y + h <= hole_y,
                    y >= hole_y + hole_height,
                )
            )

    # second constraint - rooms can't overlap
    for name1 in rooms:
        for name2 in rooms:
            if name1 >= name2:
                continue

            x1, y1 = positions[name1]
            x2, y2 = positions[name2]
            w1, h1 = rooms[name1]
            w2, h2 = rooms[name2]

            s.add(
                Or(
                    x1 + w1 <= x2,
                    x2 + w2 <= x1,
                    y1 + h1 <= y2,
                    y2 + h2 <= y1,
                )
            )

    # third constraint - rooms are adjacent
    for name1, name2 in edges:
        x1, y1 = positions[name1]
        x2, y2 = positions[name2]
        w1, h1 = rooms[name1]
        w2, h2 = rooms[name2]

        left_of = And(
            x1 + w1 == x2,
            Or(
                And(y1 <= y2, y1 + h1 > y2),
                And(y2 <= y1, y2 + h2 > y1),
            ),
        )

        right_of = And(
            x2 + w2 == x1,
            Or(
                And(y1 <= y2, y1 + h1 > y2),
                And(y2 <= y1, y2 + h2 > y1),
            ),
        )

        above = And(
            y1 + h1 == y2,
            Or(
                And(x1 <= x2, x1 + w1 > x2),
                And(x2 <= x1, x2 + w2 > x1),
            ),
        )

        below = And(
            y2 + h2 == y1,
            Or(
                And(x1 <= x2, x1 + w1 > x2),
                And(x2 <= x1, x2 + w2 > x1),
            ),
        )

        s.add(Or(left_of, right_of, above, below))

    solution_start = time.time()
    if s.check() == sat:
        model = s.model()
        layout = {
            name: (model[x].as_long(), model[y].as_long())
            for name, (x, y) in positions.items()
        }
        solution_end = time.time()

        print("Solution found in", solution_end - solution_start, "seconds")

        print("Room Layout:", layout)

        fig, ax = plt.subplots(figsize=(10, 8))

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

        visualize_boundary(ax, outer_width, outer_height, holes)

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

            ax.text(
                x + w / 2,
                y + h / 2,
                name,
                ha="center",
                va="center",
                fontsize=12,
                fontweight="bold",
            )

        ax.grid(True, linestyle="--", alpha=0.7)
        ax.set_aspect("equal")
        ax.set_xlim(-0.5, outer_width + 0.5)
        ax.set_ylim(-0.5, outer_height + 0.5)
        ax.set_title("Room Layout with Custom Boundary")
        ax.set_xlabel("X-coordinate")
        ax.set_ylabel("Y-coordinate")

        for i in range(outer_width + 1):
            ax.text(i, -0.25, str(i), ha="center")
        for i in range(outer_height + 1):
            ax.text(-0.25, i, str(i), va="center")

        plt.tight_layout()

        plt.show()
    else:
        print("No valid layout found.")


if __name__ == "__main__":
    main()
