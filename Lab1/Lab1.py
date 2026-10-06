from fractions import Fraction

def format_number(value):
    """Красивый вывод целых чисел и дробей."""
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def print_tableau(tableau, basis, variables, title="Симплекс-таблица"):
    """Выводит текущую симплекс-таблицу."""
    print("\n" + title)

    header = ["Базис"] + variables + ["b"]
    widths = [10] + [8] * (len(variables) + 1)

    for name, width in zip(header, widths):
        print(f"{name:>{width}}", end="")
    print()

    for i in range(len(basis)):
        print(f"{basis[i]:>10}", end="")
        for value in tableau[i]:
            print(f"{format_number(value):>8}", end="")
        print()

    print(f"{'c':>10}", end="")
    for value in tableau[-1]:
        print(f"{format_number(value):>8}", end="")
    print("\n")


def choose_pivot_column(tableau):
    """Выбирает разрешающий столбец по наиболее отрицательной оценке."""
    objective_row = tableau[-1][:-1]
    min_value = min(objective_row)

    if min_value >= 0:
        return None

    candidates = [j for j, value in enumerate(objective_row) if value == min_value]
    return candidates[-1]


def choose_pivot_row(tableau, pivot_col):
    """Выбирает разрешающую строку по правилу минимального отношения b / a_ij."""
    ratios = []

    for i in range(len(tableau) - 1):
        coefficient = tableau[i][pivot_col]
        b = tableau[i][-1]

        if coefficient > 0:
            ratios.append((b / coefficient, i))

    if not ratios:
        return None

    return min(ratios, key=lambda x: x[0])[1]


def pivot(tableau, pivot_row, pivot_col):
    """Выполняет пересчёт симплекс-таблицы по разрешающему элементу."""
    pivot_value = tableau[pivot_row][pivot_col]
    tableau[pivot_row] = [value / pivot_value for value in tableau[pivot_row]]

    for i in range(len(tableau)):
        if i == pivot_row:
            continue

        factor = tableau[i][pivot_col]

        if factor == 0:
            continue

        tableau[i] = [
            tableau[i][j] - factor * tableau[pivot_row][j]
            for j in range(len(tableau[i]))
        ]


def simplex(tableau, basis, variables, phase_name):
    """Решает текущую задачу симплекс-методом."""
    iteration = 1

    while True:
        print_tableau(tableau, basis, variables, f"{phase_name}. Итерация {iteration}")

        pivot_col = choose_pivot_column(tableau)

        if pivot_col is None:
            print("Отрицательных оценок больше нет.")
            print("Оптимальное решение данного этапа найдено.")
            break

        entering_variable = variables[pivot_col]
        print(f"В базис входит переменная {entering_variable}.")

        pivot_row = choose_pivot_row(tableau, pivot_col)

        if pivot_row is None:
            raise ValueError("Целевая функция не ограничена.")

        leaving_variable = basis[pivot_row]
        print(f"Из базиса выходит переменная {leaving_variable}.")

        pivot_value = tableau[pivot_row][pivot_col]
        print("Разрешающий элемент:", format_number(pivot_value))

        pivot(tableau, pivot_row, pivot_col)
        basis[pivot_row] = entering_variable
        iteration += 1

    return tableau, basis


def build_objective_row(rows, basis, variables, costs):
    """Строит строку оценок для заданной целевой функции."""
    objective = [Fraction(cost) for cost in costs] + [Fraction(0)]

    for i, basic_variable in enumerate(basis):
        basic_col = variables.index(basic_variable)
        factor = objective[basic_col]

        if factor != 0:
            objective = [
                objective[j] - factor * rows[i][j]
                for j in range(len(objective))
            ]

    return objective


print("ФАЗА I. РЕШЕНИЕ ВСПОМОГАТЕЛЬНОЙ ЗАДАЧИ")

# После перехода к каноническому виду:
# x1 + 2*x2 + x3 + x5 = 7
# x2 + x3 + x4 + x7 = 6
# x1 + x4 - x6 + x8 = 2
# x7 и x8 являются искусственными переменными.

variables_phase1 = ["x1", "x2", "x3", "x4", "x5", "x6", "x7", "x8"]
basis_phase1 = ["x5", "x7", "x8"]

rows_phase1 = [
    [1, 2, 1, 0, 1, 0, 0, 0, 7],
    [0, 1, 1, 1, 0, 0, 1, 0, 6],
    [1, 0, 0, 1, 0, -1, 0, 1, 2]
]

# Используем Fraction, чтобы избежать ошибок округления.
rows_phase1 = [[Fraction(value) for value in row] for row in rows_phase1]

# Вспомогательная целевая функция: Q = x7 + x8 -> min.
costs_phase1 = [0, 0, 0, 0, 0, 0, 1, 1]

objective_phase1 = build_objective_row(
    rows_phase1,
    basis_phase1,
    variables_phase1,
    costs_phase1
)

tableau_phase1 = rows_phase1 + [objective_phase1]

tableau_phase1, basis_phase1 = simplex(
    tableau_phase1,
    basis_phase1,
    variables_phase1,
    "Фаза I"
)

# В правом нижнем углу таблицы находится значение -Q.
minus_q = tableau_phase1[-1][-1]
q_min = -minus_q

print("\nРезультат вспомогательной задачи:")
print("Q_min =", format_number(q_min))

if q_min > 0:
    print("Q_min > 0, поэтому исходная задача не имеет допустимых решений.")
    raise SystemExit

print("Q_min = 0, поэтому исходная задача имеет допустимые решения.")
print("Искусственные переменные можно удалить.")


print("\nФАЗА II. РЕШЕНИЕ ИСХОДНОЙ ЗАДАЧИ")

# Искусственные переменные x7 и x8 удаляются.
variables_phase2 = ["x1", "x2", "x3", "x4", "x5", "x6"]

keep_columns = [
    variables_phase1.index(variable)
    for variable in variables_phase2
]

rows_phase2 = []

for row in tableau_phase1[:-1]:
    new_row = [row[j] for j in keep_columns]
    new_row.append(row[-1])
    rows_phase2.append(new_row)

basis_phase2 = basis_phase1.copy()

# Исходная целевая функция: F = x1 + 2*x2 + 3*x3 + x4 -> min.
costs_phase2 = [1, 2, 3, 1, 0, 0]

objective_phase2 = build_objective_row(
    rows_phase2,
    basis_phase2,
    variables_phase2,
    costs_phase2
)

tableau_phase2 = rows_phase2 + [objective_phase2]

tableau_phase2, basis_phase2 = simplex(
    tableau_phase2,
    basis_phase2,
    variables_phase2,
    "Фаза II"
)

solution = {variable: Fraction(0) for variable in variables_phase2}

for i, basic_variable in enumerate(basis_phase2):
    solution[basic_variable] = tableau_phase2[i][-1]

original_variables = ["x1", "x2", "x3", "x4"]

print("\nОПТИМАЛЬНОЕ РЕШЕНИЕ")

for variable in original_variables:
    print(f"{variable} = {format_number(solution[variable])}")

# В правом нижнем углу таблицы находится значение -F.
minus_f = tableau_phase2[-1][-1]
f_min = -minus_f

print("\nМинимальное значение целевой функции:")
print("F_min =", format_number(f_min))

x1 = solution["x1"]
x2 = solution["x2"]
x3 = solution["x3"]
x4 = solution["x4"]

constraint_1 = x1 + 2 * x2 + x3
constraint_2 = x2 + x3 + x4
constraint_3 = x1 + x4

print("\nПроверка ограничений:")
print(f"x1 + 2*x2 + x3 = {format_number(constraint_1)} <= 7")
print(f"x2 + x3 + x4 = {format_number(constraint_2)} = 6")
print(f"x1 + x4 = {format_number(constraint_3)} >= 2")

print("\nИтог:")
print(
    "x* = ("
    + "; ".join(format_number(solution[v]) for v in original_variables)
    + ")"
)
print("F_min =", format_number(f_min))