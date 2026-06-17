from game_logic import get_valid_sides, get_domino_vals

class DominoBot:
    def __init__(self, difficulty='greedy'):
        self.difficulty = difficulty
        self.player_missing_suits = set()

    def make_move(self, bot_hand, table_chain):
        # Анализирует руку бота и стол.
        # Возвращает кортеж: (индекс_фишки_в_руке, 'left' или 'right', флаг_переворота)
        # Если ходов нет, возвращает None (бот должен идти в базар).

        # Если стол пуст (бот ходит первым)
        if not table_chain:
            return self._first_move(bot_hand)

        # Собираем все легальные ходы
        valid_moves = []
        for i, domino in enumerate(bot_hand):
            sides = get_valid_sides(domino, table_chain)
            if 'left' in sides:
                valid_moves.append((i, 'left', sides['left']))
            if 'right' in sides:
                valid_moves.append((i, 'right', sides['right']))

        # Если подходящих фишек нет
        if not valid_moves:
            return None

        # Выбираем ход в зависимости от уровня сложности
        if self.difficulty == 'novice':
            import random
            if random.random() < 0.5:  # 50% шанс на случайный ход
                return random.choice(valid_moves)
            return self._greedy_choice(bot_hand, valid_moves)

        elif self.difficulty == 'tracker':
            # Подключаем твою новую функцию для уровня "Любитель"
            return self._sherlock_choice(bot_hand, valid_moves)
        elif self.difficulty == 'master':
            return self._master_choice(bot_hand, table_chain, valid_moves)

        else:
            # Для любых других уровней по умолчанию работает базовый алгоритм
            return self._greedy_choice(bot_hand, valid_moves)

    def _first_move(self, bot_hand):
        # Логика первого хода: скинуть самый большой дубль, иначе самую тяжелую костяшку
        best_index = 0
        best_weight = -1
        has_double = False

        for i, domino in enumerate(bot_hand):
            v1, v2 = get_domino_vals(domino)
            is_db = (v1 == v2)
            weight = v1 + v2

            if is_db and not has_double:
                has_double = True
                best_weight = weight
                best_index = i
            elif is_db and has_double and weight > best_weight:
                best_weight = weight
                best_index = i
            elif not has_double and weight > best_weight:
                best_weight = weight
                best_index = i

        # По умолчанию кладем вправо (для пустого стола неважно)
        return (best_index, 'right', False)

    def _greedy_choice(self, bot_hand, valid_moves):
        # Логика Уровня 1: Выбираем ход, который избавляет от самых тяжелых очков
        print("Работает простой алгоритм")
        best_move = None
        best_weight = -1
        has_double = False

        for move in valid_moves:
            index, side, flip = move
            domino = bot_hand[index]
            v1, v2 = get_domino_vals(domino)
            is_db = (v1 == v2)
            weight = v1 + v2

            # Дубли в абсолютном приоритете на сброс
            if is_db and not has_double:
                has_double = True
                best_weight = weight
                best_move = move
            elif is_db and has_double and weight > best_weight:
                best_weight = weight
                best_move = move
            elif not has_double and weight > best_weight:
                best_weight = weight
                best_move = move

        return best_move

    def record_player_pass(self, left_val, right_val):
        # Метод для Уровня 2: Бот фиксирует, что у тебя нет этих мастей
        self.player_missing_suits.add(left_val)
        self.player_missing_suits.add(right_val)
        print(f"ИИ заметил: у игрока нет цифр {left_val} и {right_val}")

    def _sherlock_choice(self, bot_hand, valid_moves):
        # Любитель анализирует свою руку и скидывает дубли
        print("Работает любительский алгоритм")
        import random
        # 1. Считаем, каких цифр в нашей руке больше всего
        suit_counts = {i: 0 for i in range(7)}
        for d in bot_hand:
            v1, v2 = get_domino_vals(d)
            suit_counts[v1] += 1
            suit_counts[v2] += 1

        best_move = None
        best_score = -100

        for move in valid_moves:
            index, side, flip = move
            d = bot_hand[index]
            v1, v2 = get_domino_vals(d)

            # Базовый счет = вес костяшки
            score = v1 + v2

            # Приоритет на избавление от дублей
            if v1 == v2:
                score += 20

                # Бонус за масть (сохраняем те цифры, которых у нас мало, скидываем те, которых много)
            score += (suit_counts[v1] + suit_counts[v2])

            # Щепотка случайности для непредсказуемости
            score += random.uniform(0, 0.5)

            if score > best_score:
                best_score = score
                best_move = move

        return best_move

    def _master_choice(self, bot_hand, table_chain, valid_moves):
        # Алгоритм 'Мастер': Статистический подсчет и теория вероятностей
        import random
        # 1. Вычисляем распределение: считаем ВСЕ видимые цифры
        visible_counts = {i: 0 for i in range(7)}
        for d in bot_hand:
            v1, v2 = get_domino_vals(d)
            visible_counts[v1] += 1
            visible_counts[v2] += 1
        for d in table_chain:
            v1, v2 = get_domino_vals(d)
            visible_counts[v1] += 1
            visible_counts[v2] += 1

        best_move = None
        best_score = -1000

        for move in valid_moves:
            index, side, flip = move
            d = bot_hand[index]
            v1, v2 = get_domino_vals(d)

            # Базовый вес и огромный приоритет сброса дублей
            score = v1 + v2
            if v1 == v2:
                score += 30

            # Если цифра уже выпадала 5-6 раз, шанс, что она есть у игрока, мал
            # Даем гигантский бонус за выставление на стол таких цифр,
            # чтобы заставить игрока тянуть из банка
            score += (visible_counts[v1] * 8)
            score += (visible_counts[v2] * 8)

            # Микро-дисперсия для непредсказуемости
            score += random.uniform(0, 0.5)

            if score > best_score:
                best_score = score
                best_move = move

        return best_move