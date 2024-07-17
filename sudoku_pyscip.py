import pandas as pd
from pyscipopt import Model, quicksum, SCIP_PARAMSETTING
import matplotlib.pyplot as plt

# Read and store initial numbers
try:
    df = pd.read_csv("Sudoku_9x9_test.csv", header=None, sep=';')
    #df = pd.read_csv("Sudoku_9x9_test2.csv", header=None, sep=', ')
    df = df.fillna(0).astype(int)
    #print(df.head())  # Überprüfe die ersten Zeilen der Datei
except Exception as e:
    print(f"Fehler beim Einlesen der CSV-Datei: {e}")
    exit()

# Prüfen, ob die eingelesenen Daten die erwartete Struktur haben
if df.shape != (9, 9):
    print(f"Die Datei hat nicht die erwartete Größe von 9x9, sondern: {df.shape}")
    exit()

# Konvertiere die DataFrame in ein Dictionary von Initialwerten
init_vals = {}
for r in range(9):
    for c in range(9):
        value = df.iat[r, c]
        if value != 0:  # Nur nicht-leere Werte berücksichtigen
            init_vals[(r + 1, c + 1)] = value

# Funktion zur Erstellung des Modells
def create_model(init_vals, exclude_solutions):
    m = Model("Sudoku")
    m.setPresolve(SCIP_PARAMSETTING.OFF)

    # Decision variables
    y = {
        (r, c, v): m.addVar(vtype="B", name=f"y_{r}_{c}_{v}")
        for r in range(1, 10)
        for c in range(1, 10)
        for v in range(1, 10)
    }

    # Constraints
    # Respect initial values
    for ((r, c), v) in init_vals.items():
        m.addCons(y[r, c, v] == 1)

    # One entry per cell
    for r in range(1, 10):
        for c in range(1, 10):
            m.addCons(quicksum(y[r, c, v] for v in range(1, 10)) == 1)

    # Unique value per row
    for r in range(1, 10):
        for v in range(1, 10):
            m.addCons(quicksum(y[r, c, v] for c in range(1, 10)) == 1)

    # Unique value per column
    for c in range(1, 10):
        for v in range(1, 10):
            m.addCons(quicksum(y[r, c, v] for r in range(1, 10)) == 1)

    # Unique value per box
    boxes = [
        [(3 * i + k, 3 * j + l) for k in range(1, 4) for l in range(1, 4)]
        for i in range(3)
        for j in range(3)
    ]
    for box in boxes:
        for v in range(1, 10):
            m.addCons(quicksum(y[r, c, v] for (r, c) in box) == 1)

    # Add constraints to exclude already found solutions
    for solution in exclude_solutions:
        m.addCons(quicksum(y[k] for k in solution) <= len(solution) - 1)

    return m, y

# Variable to count solutions
solution_count = 0


# Function to print the Sudoku grid
def print_sudoku(solution):
    result_grid = [[0 for _ in range(9)] for _ in range(9)]
    for (r, c, v) in solution:
        result_grid[r-1][c-1] = v

    print(f"Gefundene Lösung {solution_count}:")
    for i, row in enumerate(result_grid):
        if i % 3 == 0 and i != 0:
            print("-"*21)
        print(" ".join(str(val) if (j + 1) % 3 != 0 else str(val) + " |" for j, val in enumerate(row)))

    # Plot the resulting Sudoku grid
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.imshow([[0]*9]*9, cmap='Pastel1', extent=[0, 9, 0, 9])

    for i in range(10):
        lw = 2 if i % 3 == 0 else 1
        ax.axhline(i, color='black', linewidth=lw)
        ax.axvline(i, color='black', linewidth=lw)

    for r in range(9):
        for c in range(9):
            ax.text(c + 0.5, 8.5 - r, str(result_grid[r][c]), va='center', ha='center', fontsize=16)

    # Remove axis labels and ticks
    ax.axis('off')
    plt.show()

# List to store already found solutions
exclude_solutions = []

while True:
    # Create the model
    m, y = create_model(init_vals, exclude_solutions)
    m.optimize()

    # Check the optimization status
    if m.getStatus() != 'optimal':
        print(f"Gesamtanzahl der gefundenen Lösungen: {solution_count}")
        break

    # Collect indices from solution
    I = [k for k in y if m.getVal(y[k]) > 0.99]

    # Increment the solution count
    solution_count += 1

    # Print the current solution
    print_sudoku(I)

    # Add the current solution to the list of excluded solutions
    exclude_solutions.append(I)

    # Prompt user for next solution
    user_input = input(
        "Weitere Lösung anzeigen? (drücken Sie Enter für Ja, geben Sie 'n' ein und drücken Sie Enter für Nein): ")
    if user_input.lower() == 'n':
        break
