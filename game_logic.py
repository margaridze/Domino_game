def get_domino_vals(domino):
    # Универсально достает два числа из костяшки домино
    try:
        return domino[0], domino[1]
    except TypeError:
        # Если это объект с кастомными атрибутами, попробуем стандартные варианты Дипсика
        if hasattr(domino, 'vals'): return domino.vals[0], domino.vals[1]
        if hasattr(domino, 'a'): return domino.a, domino.b
        if hasattr(domino, 'side1'): return domino.side1, domino.side2
    return 0, 0


def get_chain_ends(table_chain):
    # Возвращает текущие открытые числа на краях стола
    if not table_chain:
        return None, None

    # Берем первую и последнюю фишку на столе
    first_vals = get_domino_vals(table_chain[0])
    last_vals = get_domino_vals(table_chain[-1])

    # внешние края для базовой проверки
    left_end = first_vals[0]
    right_end = last_vals[1]
    return left_end, right_end


def check_available_moves(hand, table_chain):
    # Проверяет, есть ли в руке хотя бы одна фишка, которую можно выложить на стол.

    if not table_chain:
        return True  # На пустой стол можно ходить любой фишкой

    left_end, right_end = get_chain_ends(table_chain)

    for domino in hand:
        v1, v2 = get_domino_vals(domino)
        if v1 == left_end or v2 == left_end or v1 == right_end or v2 == right_end:
            return True  # Нашлась подходящая

    return False  # Ходов нет, нужно идти в банк


def get_valid_sides(domino, table_chain):
    # Определяет, на какие стороны стола можно положить фишку.
    # Возвращает словарь  {'left': need_flip, 'right': need_flip}

    if not table_chain:
        return {'left': False, 'right': False}  # На пустой стол можно любой стороной

    left_end, right_end = get_chain_ends(table_chain)
    v1, v2 = get_domino_vals(domino)

    available_sides = {}

    # Проверяем левый край стола (стыкуется с правой стороной новой фишки)
    if v2 == left_end:
        available_sides['left'] = False  # Подходит как есть
    elif v1 == left_end:
        available_sides['left'] = True  # Подходит, если перевернуть

    # Проверяем правый край стола (стыкуется с левой стороной новой фишки)
    if v1 == right_end:
        available_sides['right'] = False  # Подходит как есть
    elif v2 == right_end:
        available_sides['right'] = True  # Подходит, если перевернуть

    return available_sides