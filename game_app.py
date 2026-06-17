import tkinter as tk
from settings import *
from domino import Domino
from render import draw_domino
from game_logic import get_domino_vals, check_available_moves, get_valid_sides
from tkinter import messagebox
from bot_logic import DominoBot

# метод для рисования скруглённого прямоугольника
def _create_rounded_rectangle(self, x1, y1, x2, y2, radius=25, **kwargs):
    points = []
    for x, y in [(x1+radius, y1), (x2-radius, y1),
                 (x2, y1+radius), (x2, y2-radius),
                 (x2-radius, y2), (x1+radius, y2),
                 (x1, y2-radius), (x1, y1+radius)]:
        points.extend([x, y])
    return self.create_polygon(points, smooth=True, **kwargs)

tk.Canvas.create_rounded_rectangle = _create_rounded_rectangle

class DominoGame:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Домино")
        self.root.geometry(f"{WIDTH}x{HEIGHT}")
        self.root.configure(bg=COLOR_BG)

        self.welcome_frame = tk.Frame(self.root, bg=COLOR_BG)
        self.game_frame = tk.Frame(self.root, bg=COLOR_BG)

        self.is_bank_flashing = False
        self.pending_domino_index = None

        self.show_welcome()
        self.root.mainloop()

    # ---------- ПРИВЕТСТВЕННЫЙ ЭКРАН ----------
    def show_welcome(self):
        for widget in self.welcome_frame.winfo_children():
            widget.destroy()
        self.game_frame.pack_forget()
        self.welcome_frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(self.welcome_frame, bg=COLOR_BG, highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True, padx=50, pady=50)

        def on_resize(event):
            canvas.delete("frame_border")
            canvas.create_rounded_rectangle(10, 10, event.width-10, event.height-10,
                                            radius=30, fill=COLOR_BG, outline=COLOR_DARK,
                                            width=5, tags="frame_border")
        canvas.bind("<Configure>", on_resize)

        # Надпись "Домино"
        shadow = tk.Label(canvas, text="Домино", font=FONT_TITLE, bg=COLOR_BG, fg=COLOR_DARK)
        shadow.place(relx=0.5, rely=0.4, anchor="center", x=3, y=3)
        title = tk.Label(canvas, text="Домино", font=FONT_TITLE, bg=COLOR_BG, fg=COLOR_DARK)
        title.place(relx=0.5, rely=0.4, anchor="center")

        # КНОПКИ ВЫБОРА СЛОЖНОСТИ
        # Функция для красивого нажатия и старта
        def on_click(level):
            self.show_game(difficulty=level)

        # 1. Новичок (Зеленый)
        btn_novice = tk.Canvas(canvas, width=220, height=60, bg=COLOR_BG, highlightthickness=0)
        btn_novice.place(relx=0.5, rely=0.55, anchor="center")
        btn_novice.create_rounded_rectangle(5, 5, 215, 55, radius=15, fill="#A3B565", outline=COLOR_DARK, width=3,
                                            tags="btn")
        btn_novice.create_text(110, 30, text="Новичок", font=FONT_BUTTON, fill=COLOR_DARK, tags="btn")
        btn_novice.tag_bind("btn", "<ButtonRelease-1>", lambda e: on_click('novice'))

        # 2. Любитель (Желтый)
        btn_sherlock = tk.Canvas(canvas, width=220, height=60, bg=COLOR_BG, highlightthickness=0)
        btn_sherlock.place(relx=0.5, rely=0.67, anchor="center")
        btn_sherlock.create_rounded_rectangle(5, 5, 215, 55, radius=15, fill="#FCDD9D", outline=COLOR_DARK, width=3,
                                              tags="btn")
        btn_sherlock.create_text(110, 30, text="Любитель", font=FONT_BUTTON, fill=COLOR_DARK, tags="btn")
        btn_sherlock.tag_bind("btn", "<ButtonRelease-1>", lambda e: on_click('tracker'))

        # 3. Мастер (Красный)
        btn_master = tk.Canvas(canvas, width=220, height=60, bg=COLOR_BG, highlightthickness=0)
        btn_master.place(relx=0.5, rely=0.79, anchor="center")
        btn_master.create_rounded_rectangle(5, 5, 215, 55, radius=15, fill="#F1642E", outline=COLOR_DARK, width=3,
                                            tags="btn")
        btn_master.create_text(110, 30, text="Мастер", font=FONT_BUTTON, fill=COLOR_DARK, tags="btn")
        btn_master.tag_bind("btn", "<ButtonRelease-1>", lambda e: on_click('master'))

    # ---------- ИГРОВОЙ ЭКРАН ----------
    def show_game(self, difficulty='novice'):

        # 1.  создаем все переменные сессии игры в первую очередь
        self.player_score = getattr(self, 'player_score', 0)
        self.bot_score = getattr(self, 'bot_score', 0)
        self.is_first_round = getattr(self, 'is_first_round', True)
        self.round_winner = getattr(self, 'round_winner', None)

        # 2. Безопасно очищаем старые виджеты
        for widget in self.game_frame.winfo_children():
            widget.destroy()

        # 3. И только после этого прячем приветственное окно
        self.welcome_frame.pack_forget()
        self.game_frame.pack(fill=tk.BOTH, expand=True)

        # ПОДКЛЮЧАЕМ ИИ ТУТ:
        self.bot = DominoBot(difficulty=difficulty)

        # -------------- ВЕРХНЯЯ ЗОНА (противник) ---------------
        self.top_canvas = tk.Canvas(self.game_frame, bg=COLOR_BG, highlightthickness=0, height=150)
        self.top_canvas.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        self.top_canvas.pack_propagate(False)

        def draw_top(event=None):
            self.top_canvas.delete("top_all")
            w = event.width if event else self.top_canvas.winfo_width()
            if w < 10: w = WIDTH
            h = 150

            self.top_canvas.create_rounded_rectangle(0, 0, w, h, radius=20,
                                                     fill=COLOR_PLAYER_AREA, outline=COLOR_DARK,
                                                     width=5, tags="top_all")

            self.top_canvas.create_text(25, 15, text="Костяшки противника", font=FONT_LABEL,
                                        fill=COLOR_DARK, anchor="nw", tags="top_all")

            # рубашки фишек противника
            tile_w, tile_h = 40, 70
            start_x = 25
            y = 55

            num_tiles = len(self.bot_hand) if hasattr(self, 'bot_hand') else 7
            for i in range(num_tiles):
                x = start_x + i * (tile_w + 10)
                self.top_canvas.create_rectangle(x, y, x + tile_w, y + tile_h,
                                                 fill=COLOR_DOMINO, outline=COLOR_DARK, width=2, tags="top_all")
                # Горизонтальная разделительная линия для вертикальной рубашки
                self.top_canvas.create_line(x, y + tile_h // 2, x + tile_w, y + tile_h // 2,
                                            fill=COLOR_DARK, width=2, tags="top_all")

            # круглый счет
            circle_size = 80
            center_x = w - CIRCLE_RIGHT_OFFSET
            center_y = h // 2
            self.top_canvas.create_oval(center_x - circle_size // 2, center_y - circle_size // 2,
                                        center_x + circle_size // 2, center_y + circle_size // 2,
                                        outline=COLOR_DARK, width=3, fill=COLOR_BG, tags="top_all")
            self.top_canvas.create_text(center_x, center_y - 12, text="Счёт", font=FONT_LABEL,
                                        fill=COLOR_DARK, tags="top_all")
            self.top_canvas.create_text(center_x, center_y + 15, text=f"{self.player_score} : {self.bot_score}",
                                        font=FONT_SCORE, fill=COLOR_DARK, tags="top_all")

        self.top_canvas.bind("<Configure>", draw_top)
        self.refresh_top = draw_top

        # ------------- СРЕДНЯЯ ЗОНА (игровое поле) -----------------

        middle_frame = tk.Frame(self.game_frame, bg=COLOR_BG)
        middle_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.chain_canvas = tk.Canvas(middle_frame, bg=COLOR_BG, highlightthickness=0)
        self.chain_canvas.pack(fill=tk.BOTH, expand=True)
        self.chain_canvas.bind("<Button-1>", self.on_table_click)

        # Кнопка "Банк"
        self.bank_canvas = tk.Canvas(self.chain_canvas, width=80, height=80, bg=COLOR_BG, highlightthickness=0)
        self.bank_canvas.place(relx = 1.0, rely = 1.0, anchor = "se", x = -20, y=-20)

        # Теги для Банка (чтобы текст не блокировал клик мышки)
        self.bank_oval = self.bank_canvas.create_oval(5, 5, 75, 75, outline=COLOR_DARK, width=3, fill=COLOR_PLAYER_AREA,
                                                      tags="bank_btn")
        self.bank_canvas.create_text(40, 40, text="Банк", font=FONT_BUTTON, fill=COLOR_DARK, tags="bank_btn")
        self.bank_canvas.tag_bind("bank_btn", "<Button-1>", self.bank_press)
        self.bank_canvas.tag_bind("bank_btn", "<ButtonRelease-1>", self.bank_release)

        # ------------------ НИЖНЯЯ ЗОНА (мои фишки) --------------
        bottom_canvas = tk.Canvas(self.game_frame, bg=COLOR_BG, highlightthickness=0, height=200)
        bottom_canvas.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        bottom_canvas.pack_propagate(False)

        # холст для руки
        self.hand_canvas = tk.Canvas(bottom_canvas, bg=COLOR_PLAYER_AREA, height=120, highlightthickness=0)
        self.hand_canvas.place(x=10, y=50, relwidth=0.8, height=120)
        self.hand_canvas.bind("<Button-1>", self.on_hand_click)

        def draw_bottom(event):
            bottom_canvas.delete("bottom_all")
            w = event.width
            h = 200
            bottom_canvas.create_rounded_rectangle(0, 0, w, h, radius=20,
                                                   fill=COLOR_PLAYER_AREA, outline=COLOR_DARK,
                                                   width=5, tags="bottom_all")
            bottom_canvas.create_text(20, 20, text="Мои костяшки", font=FONT_LABEL,
                                      fill=COLOR_DARK, anchor="nw", tags="bottom_all")
            if hasattr(self, 'current_hand'):
                self.draw_hand(self.current_hand)

        bottom_canvas.bind("<Configure>", draw_bottom)

        # Кнопка "Пауза"
        pause_frame = tk.Frame(bottom_canvas, bg=COLOR_PLAYER_AREA)
        pause_frame.place(relx=1.0, rely=0.5, anchor="e", x=-20, y=0)
        self.pause_canvas = tk.Canvas(pause_frame, width=80, height=80, bg=COLOR_PLAYER_AREA, highlightthickness=0)
        self.pause_canvas.pack()

        # еги для Паузы (чтобы палочки не блокировали клик)
        self.pause_oval = self.pause_canvas.create_oval(5, 5, 75, 75, outline=COLOR_DARK, width=3, fill=COLOR_BG,
                                                        tags="pause_btn")
        self.pause_canvas.create_rectangle(30, 25, 35, 55, fill=COLOR_DOMINO, outline=COLOR_DOMINO, tags="pause_btn")
        self.pause_canvas.create_rectangle(45, 25, 50, 55, fill=COLOR_DOMINO, outline=COLOR_DOMINO, tags="pause_btn")
        self.pause_canvas.tag_bind("pause_btn", "<Button-1>", self.pause_press)
        self.pause_canvas.tag_bind("pause_btn", "<ButtonRelease-1>", self.pause_release)

        # ---------- ИНИЦИАЛИЗАЦИЯ ИГРОВОГО ПУЛА ----------
        import random
        self.bazaar = []
        for i in range(7):
            for j in range(i, 7):
                self.bazaar.append(Domino(i, j))
        random.shuffle(self.bazaar)

        # Раздаем 7 фишек игроку
        self.current_hand = [self.bazaar.pop() for _ in range(7)]
        self.table_chain = []  # Стол в начале игры должен быть пуст!

        # Раздаем 7 фишек боту
        self.bot_hand = [self.bazaar.pop() for _ in range(7)]
        self.current_turn = 'player' #устанавливаем чей ход

        # первоначальная отрисовка рук и стола
        self.draw_hand(self.current_hand)
        if hasattr(self, 'refresh_top'):
            self.refresh_top()
        self.draw_table()

        # автоматическое определение первого хода
        self.root.after(500, self.determine_first_turn)

    def draw_hand(self, hand):
        if not hasattr(self, 'hand_canvas') or self.hand_canvas is None or not self.hand_canvas.winfo_exists():
            return
        self.hand_canvas.delete("all")
        self.current_hand = hand
        x = 20
        y = 20
        for domino in hand:
            orient = "vertical"
            draw_domino(self.hand_canvas, x, y, domino, orient, domino_color=COLOR_DOMINO, pip_color=COLOR_DARK)
            x += DOUBLE_WIDTH + 10

    def draw_bot_hand(self):
        # Отрисовывает закрытые фишки противника
        if not hasattr(self, 'bot_hand_canvas') or self.bot_hand_canvas is None:
            return
        self.bot_hand_canvas.delete("all")
        x = 20
        y = 10
        for _ in self.bot_hand:
            self.bot_hand_canvas.create_rounded_rectangle(x, y, x + 40, y + 80, radius=5, fill=COLOR_DOMINO,
                                                          outline=COLOR_DARK, width=2)
            self.bot_hand_canvas.create_line(x + 5, y + 5, x + 35, y + 75, fill=COLOR_DARK, width=2)
            x += 50

    def on_hand_click(self, event):
        # 1. Защита от ходов вне очереди
        if getattr(self, 'current_turn', 'player') != 'player':
            self.show_status_message("⏳ Сейчас ход противника! Пожалуйста, подождите.")
            self.root.after(1500, lambda: self.chain_canvas.delete("status_msg"))
            return

        if getattr(self, 'pending_domino_index', None) is not None:
            return  # Замораживаем клики, если ждем выбор стороны поля

        click_x = event.x
        current_x = 20
        for index, domino in enumerate(self.current_hand):
            width = DOUBLE_WIDTH
            if current_x <= click_x <= current_x + width:
                # Передаем индекс в метод обработки хода
                self.try_player_move(index)
                break
            current_x += width + 10

    def try_player_move(self, index):
        if getattr(self, 'pending_domino_index', None) is not None:
            return

        domino = self.current_hand[index]

        # ограничение не первый ход
        if not self.table_chain and getattr(self, 'is_first_round', True):
            if hasattr(self, 'required_first_domino') and domino != self.required_first_domino:
                v1, v2 = get_domino_vals(self.required_first_domino)
                messagebox.showwarning("Неверный ход", f"По правилам первый ход нужно сделать с костяшки [{v1}-{v2}]!")
                return

        # Если стол пуст — выкладываем первую фишку без лишних вопросов
        if not self.table_chain:
            self.current_hand.pop(index)
            self.table_chain.append(domino)
            self.finish_move()
            return

        # Дальнейшая проверка для обычной игры
        sides = get_valid_sides(domino, self.table_chain)
        if not sides:
            print("Эта костяшка не подходит ни к одному краю стола!")
            return

        if 'left' in sides and 'right' in sides:
            self.pending_domino_index = index
            self.pending_sides = sides
            self.draw_table()
            return
        elif 'left' in sides:
            self.current_hand.pop(index)
            self.place_left(domino, sides['left'])
        elif 'right' in sides:
            self.current_hand.pop(index)
            self.place_right(domino, sides['right'])

    def on_table_click(self, event):
        # Обработка клика по полю для выбора стороны цепочки
        # Если мы не находимся в режиме ожидания выбора стороны - игнорируем клик
        if getattr(self, 'pending_domino_index', None) is None:
            return

        canvas_width = self.chain_canvas.winfo_width()
        index = self.pending_domino_index
        sides = self.pending_sides
        domino = self.current_hand[index]

        # Извлекаем фишку из руки и сбрасываем режим ожидания
        self.current_hand.pop(index)
        self.pending_domino_index = None

        # Определяем, куда кликнул игрок
        if event.x < canvas_width / 2:
            self.place_left(domino, sides['left'])
        else:
            self.place_right(domino, sides['right'])

    def place_left(self, domino, flip):
        if flip:
            v1, v2 = get_domino_vals(domino)
            domino = Domino(v2, v1)  # Создаем развернутую копию фишки
        self.table_chain.insert(0, domino)  # Добавляем в начало списка (левый край)
        self.finish_move()

    def place_right(self, domino, flip):
        if flip:
            v1, v2 = get_domino_vals(domino)
            domino = Domino(v2, v1)  # Создаем развернутую копию фишки
        self.table_chain.append(domino)  # Добавляем в конец списка (правый край)
        self.finish_move()

    def draw_table(self):
        # Отрисовывает фишки на игровом поле с двойным заворотом и заморозкой центра
        if not hasattr(self, 'chain_canvas') or self.chain_canvas is None:
            return

        self.chain_canvas.delete("all")
        if not self.table_chain:
            return

        canvas_width = self.chain_canvas.winfo_width()
        canvas_height = self.chain_canvas.winfo_height()
        if canvas_width < 10: canvas_width = WIDTH - 100
        if canvas_height < 10: canvas_height = 250

        # Внутренние константы геометрии
        DOM_W, DOM_H = 80, 40
        DBL_W, DBL_H = 40, 80
        GAP = 5
        MAX_TOP_DIST = 8  # По 8 фишек от корня = 17 фишек наверху
        MAX_LEG_COUNT = 3  # 3 фишки вниз перед заворотом внутрь

        def get_dim(is_db, state):
            # Определяет габариты и ориентацию в зависимости от направления роста
            if state in ('RIGHT', 'LEFT', 'LEFT_INWARD', 'RIGHT_INWARD'):
                w = DBL_W if is_db else DOM_W
                h = DBL_H if is_db else DOM_H
                orient = "vertical" if is_db else "horizontal"
            else:
                w = DOM_W if is_db else DBL_W
                h = DOM_H if is_db else DBL_H
                orient = "horizontal" if is_db else "vertical"
            return w, h, orient

        # 1. Ищем изначальную центральную фишку по её ID в памяти
        if not hasattr(self, 'root_id') or len(self.table_chain) <= 1:
            self.root_id = getattr(self.table_chain[0], 'id', id(self.table_chain[0])) if self.table_chain else None

        c = 0  # Индекс корня
        for i, t in enumerate(self.table_chain):
            if getattr(t, 'id', id(t)) == self.root_id:
                c = i
                break

        positions = []
        top_row_x_min = 0
        top_row_x_max = 0

        # --- ОТРИСОВКА КОРНЯ ---
        dom_c = self.table_chain[c]
        try:
            is_db_c = dom_c.is_double()
        except AttributeError:
            v1, v2 = get_domino_vals(dom_c)
            is_db_c = (v1 == v2)

        w_c, h_c, orient_c = get_dim(is_db_c, 'RIGHT')
        x_c, y_c = 0, 30 - (20 if is_db_c else 0)
        positions.append((dom_c, x_c, y_c, orient_c, False))
        top_row_x_min = x_c
        top_row_x_max = x_c + w_c

        # --- СТРОИМ ПРАВУЮ ВЕТВЬ ---
        px, py, pw, ph, p_is_db = x_c, y_c, w_c, h_c, is_db_c
        state = 'RIGHT'
        leg_count = 0

        for i in range(c + 1, len(self.table_chain)):
            domino = self.table_chain[i]
            try:
                is_db = domino.is_double()
            except AttributeError:
                v1, v2 = get_domino_vals(domino)
                is_db = (v1 == v2)

            dist = i - c

            # Стейт-машина правой ветви
            if state == 'RIGHT':
                if dist <= MAX_TOP_DIST or (dist == MAX_TOP_DIST + 1 and is_db):
                    pass
                else:
                    state = 'DOWN'
                    leg_count = 0
            elif state == 'DOWN':
                if leg_count < MAX_LEG_COUNT or (leg_count == MAX_LEG_COUNT and is_db):
                    pass
                else:
                    state = 'LEFT_INWARD'
                    leg_count = 0

            w, h, orient = get_dim(is_db, state)
            visual_flip = False

            if state == 'RIGHT':
                x = px + pw + GAP
                y = 30 - (20 if is_db else 0)
                top_row_x_max = x + w
            elif state == 'DOWN':
                leg_count += 1
                if leg_count == 1:  # Угловой стык
                    x = px + (pw - w) // 2 if p_is_db else px + pw -w
                else:  # Продолжение ножки
                    x = px + (pw - w) // 2
                y = py + ph + GAP
            elif state == 'LEFT_INWARD':
                leg_count += 1
                if leg_count == 1:  # Угловой стык внутрь
                    y = py + (ph - h) // 2 if p_is_db else py + 40 - (20 if is_db else 0)
                else:
                    y = py + (ph - h) // 2
                x = px - w - GAP
                visual_flip = True  # Цифры перевернуты из-за роста влево

            positions.append((domino, x, y, orient, visual_flip))
            px, py, pw, ph, p_is_db = x, y, w, h, is_db

        # --- СТРОИМ ЛЕВУЮ ВЕТВЬ ---
        px, py, pw, ph, p_is_db = x_c, y_c, w_c, h_c, is_db_c
        state = 'LEFT'
        leg_count = 0

        for i in range(c - 1, -1, -1):
            domino = self.table_chain[i]
            try:
                is_db = domino.is_double()
            except AttributeError:
                v1, v2 = get_domino_vals(domino)
                is_db = (v1 == v2)

            dist = c - i

            # Стейт-машина левой ветви
            if state == 'LEFT':
                if dist <= MAX_TOP_DIST or (dist == MAX_TOP_DIST + 1 and is_db):
                    pass
                else:
                    state = 'DOWN'
                    leg_count = 0
            elif state == 'DOWN':
                if leg_count < MAX_LEG_COUNT or (leg_count == MAX_LEG_COUNT and is_db):
                    pass
                else:
                    state = 'RIGHT_INWARD'
                    leg_count = 0

            w, h, orient = get_dim(is_db, state)
            visual_flip = False

            if state == 'LEFT':
                x = px - w - GAP
                y = 30 - (20 if is_db else 0)
                top_row_x_min = x
            elif state == 'DOWN':
                leg_count += 1
                if leg_count == 1:
                    x = px + (pw - w) // 2 if p_is_db else px
                else:
                    x = px + (pw - w) // 2
                y = py + ph + GAP
                visual_flip = True  # Цифры перевернуты из-за роста вниз левой ветви
            elif state == 'RIGHT_INWARD':
                leg_count += 1
                if leg_count == 1:
                    y = py + (ph - h) // 2 if p_is_db else py + 40 - (20 if is_db else 0)
                else:
                    y = py + (ph - h) // 2
                x = px + pw + GAP
                visual_flip = True

            positions.append((domino, x, y, orient, visual_flip))
            px, py, pw, ph, p_is_db = x, y, w, h, is_db

        # 2. ФИНАЛЬНЫЙ РЕНДЕР И ЯКОРЬ
        # Центрируем всю фигуру исключительно по габаритам верхнего ряда!
        top_w = top_row_x_max - top_row_x_min
        shift_x = (canvas_width - top_w) // 2 - top_row_x_min

        for item in positions:
            domino, x, y, orient, visual_flip = item

            # Переворачиваем цифры фишки только для отрисовки, чтобы сохранить стыки
            if visual_flip:
                try:
                    v1, v2 = get_domino_vals(domino)
                    draw_d = Domino(v2, v1)
                except Exception:
                    draw_d = domino
            else:
                draw_d = domino

            draw_domino(self.chain_canvas, x + shift_x, y, draw_d, orient, domino_color=COLOR_DOMINO,
                        pip_color=COLOR_DARK)

        # ----------------- ВЫВОД НАДПИСЕЙ ВНИЗУ ЭКРАНА ---------------
        canvas_width = self.chain_canvas.winfo_width()
        canvas_height = self.chain_canvas.winfo_height()
        if canvas_width < 10: canvas_width = WIDTH - 100
        if canvas_height < 10: canvas_height = 250

        # 1. Если игрок выбрал фишку и мы ждем клика по краю поля
        if getattr(self, 'pending_domino_index', None) is not None:
            self.chain_canvas.create_text(
                canvas_width // 2, canvas_height - 30,
                text="← Кликните в ЛЕВОЙ или ПРАВОЙ половине поля, чтобы выложить фишку →",
                font=FONT_LABEL, fill="#504E76"
            )
        # 2. Если есть статус от ИИ (например Противник обдумывает ход...)
        elif getattr(self, 'status_msg', ""):
            self.chain_canvas.create_text(
                canvas_width // 2, canvas_height - 30,
                text=self.status_msg, font=("Arial", 12, "bold"),
                fill=COLOR_DARK if 'COLOR_DARK' in globals() else "black"
            )
        # 3. Если сейчас мой ход и включена фаза мигания
        elif getattr(self, 'current_turn', 'player') == 'player':
            self.chain_canvas.create_text(
                canvas_width // 2, canvas_height - 30,
                text="★ ВАШ ХОД ★", font=("Arial", 14, "bold"), fill="#504E76"
            )

    def start_bank_flashing(self):
        # запускает мигание Банка
        if getattr(self, 'flash_id', None) is None:
            self.flash_bank_step(True)

    def flash_bank_step(self, is_dark):
        # Шаг анимации мигания
        if not hasattr(self, 'bank_canvas') or not hasattr(self, 'bank_oval'):
            return

        # Если ход не мой — мгновенно выключаем мигание
        if getattr(self, 'current_turn', 'player') != 'player':
            self.bank_canvas.itemconfig(self.bank_oval, fill=COLOR_PLAYER_AREA)
            self.flash_id = None
            return

        color = "#A24A4A" if is_dark else COLOR_PLAYER_AREA
        self.bank_canvas.itemconfig(self.bank_oval, fill=color)
        self.flash_id = self.root.after(500, lambda: self.flash_bank_step(not is_dark))

    def stop_bank_flashing(self):
        if hasattr(self, 'flash_id') and self.flash_id:
            self.root.after_cancel(self.flash_id)
            self.flash_id = None
        if hasattr(self, 'bank_canvas') and hasattr(self, 'bank_oval'):
            self.bank_canvas.itemconfig(self.bank_oval, fill=COLOR_PLAYER_AREA)

    def check_bank_highlight(self):
        # Управляет подсветкой банка и автопасом игрока
        if not self.current_hand:
            self.stop_bank_flashing()
            return

        if getattr(self, 'current_turn', 'player') != 'player':
            self.stop_bank_flashing()
            return

        if self.is_fish_situation():
            self.stop_bank_flashing()
            self.end_round("fish", None)
            return

        if not check_available_moves(self.current_hand, self.table_chain):
            if hasattr(self, 'bazaar') and len(self.bazaar) > 0:
                self.start_bank_flashing()
            else:
                self.stop_bank_flashing()
                messagebox.showinfo("Пас", "У вас нет доступных ходов, и Банк пуст. Вы пропускаете ход.")
                self.current_turn = 'bot'
                self.status_msg = "Противник обдумывает ход..."
                self.draw_table()
                self.bot_timer_id = self.root.after(2000, self.bot_turn)
        else:
            self.stop_bank_flashing()

    def bank_press(self, event):
        # Красим овал, чтобы надпись не исчезала
        self.bank_canvas.itemconfig(self.bank_oval, fill="#8B9B4A")

    def bank_release(self, event):
        if getattr(self, 'current_turn', 'player') != 'player':
            return
        self.bank_canvas.itemconfig(self.bank_oval, fill=COLOR_PLAYER_AREA)
        self.take_from_bazaar()

    def take_from_bazaar(self):
        # Берет фишку из реального пула
        if hasattr(self, 'bazaar') and len(self.bazaar) > 0:
            new_domino = self.bazaar.pop()
            self.current_hand.append(new_domino)
            self.draw_hand(self.current_hand)
            print(f"Вы взяли из банка фишку. Осталось: {len(self.bazaar)}")
            self.check_bank_highlight()
        else:
            print("Банк пуст!")
            self.stop_bank_flashing()

    def pause_press(self, event):
        self.pause_canvas.itemconfig(self.pause_oval, fill="#B0AEC8")
        self.pause_canvas.update()

    def pause_release(self, event):
        self.pause_canvas.itemconfig(self.pause_oval, fill=COLOR_BG)
        if messagebox.askyesno("Выход", "Вы уверены что хотите выйти?\nТекущая игра будет сброшена."):
            self.reset_entire_game()
            self.return_to_welcome()

    def clear_all_timers(self):
        # Полностью отменяет все фоновые задержки и таймеры мигания
        if hasattr(self, 'bot_timer_id') and self.bot_timer_id:
            self.root.after_cancel(self.bot_timer_id)
            self.bot_timer_id = None
        if hasattr(self, 'flash_id') and self.flash_id:
            self.root.after_cancel(self.flash_id)
            self.flash_id = None

    def is_fish_situation(self):
        # Проверяет, заблокирована ли игра (Рыба) при пустом Банке
        if hasattr(self, 'bazaar') and len(self.bazaar) > 0:
            return False
        p_blocked = not check_available_moves(self.current_hand, self.table_chain)
        b_blocked = not check_available_moves(self.bot_hand, self.table_chain)
        return p_blocked and b_blocked

    def show_status_message(self, text, color="#504E76"):

        # обновляет центральный статус игры и перерисовывает стол
        self.status_msg = text
        self.draw_table()

    def finish_move(self):
        # Вызывается, когда игрок успешно положил фишку на стол
        self.draw_hand(self.current_hand)
        self.draw_table()

        if not self.current_hand:
            self.end_round("normal", "player")
            return

        self.stop_bank_flashing()

        # Передаем ход боту и включаем статус размышления
        self.current_turn = 'bot'
        self.status_msg = "Противник обдумывает ход..."
        self.draw_table()
        self.root.after(2000, self.bot_turn)


    def bot_turn(self):
        # Логика выполнения хода противника
        if getattr(self, 'current_turn', 'player') != 'bot' or not self.bot_hand:
            return

        if self.is_fish_situation():
            self.end_round("fish", None)
            return

        if not self.table_chain and getattr(self, 'is_first_round', True) and hasattr(self, 'required_first_domino'):
            if self.required_first_domino in self.bot_hand:
                index = self.bot_hand.index(self.required_first_domino)
                move = (index, 'right', False)
            else:
                move = self.bot.make_move(self.bot_hand, self.table_chain)
        else:
            move = self.bot.make_move(self.bot_hand, self.table_chain)

        if move is not None:
            index, side, flip = move
            domino = self.bot_hand.pop(index)

            if flip:
                v1, v2 = get_domino_vals(domino)
                domino = Domino(v2, v1)

            if side == 'left':
                self.table_chain.insert(0, domino)
            else:
                self.table_chain.append(domino)

            self.status_msg = ""
            self.draw_table()
            if hasattr(self, 'refresh_top'): self.refresh_top()

            if not self.bot_hand:
                self.end_round("normal", "bot")
                return

            self.current_turn = 'player'
            self.check_bank_highlight()
            self.draw_table()
        else:
            if len(self.bazaar) > 0:
                new_domino = self.bazaar.pop()
                self.bot_hand.append(new_domino)
                self.status_msg = "Противник берет костяшку из Банка..."
                if hasattr(self, 'refresh_top'): self.refresh_top()
                self.bot_timer_id = self.root.after(1500, self.bot_turn)
            else:
                if self.is_fish_situation():
                    self.end_round("fish", None)
                    return
                messagebox.showinfo("Пас", "Противнику нечем ходить, а Банк пуст. Он пасует.")
                self.status_msg = ""
                self.current_turn = 'player'
                self.check_bank_highlight()
                self.draw_table()

    def determine_first_turn(self):
        # Определяет очередность ходов
        if not getattr(self, 'is_first_round', True) and getattr(self, 'round_winner', None) is not None:
            self.current_turn = self.round_winner
            who = "Вы" if self.round_winner == 'player' else "Противник"
            messagebox.showinfo("Следующий раунд", f"Победитель предыдущего раунда — {who}. {who} ходит первым!")

            self.status_msg = "" if self.current_turn == 'player' else "Противник обдумывает ход..."
            self.draw_table()
            if self.current_turn == 'player':
                self.check_bank_highlight()
            else:
                self.bot_timer_id = self.root.after(2000, self.bot_turn)
            return

        player_dbs = []
        bot_dbs = []
        for d in self.current_hand:
            v1, v2 = get_domino_vals(d)
            if v1 == v2: player_dbs.append((v1, d))
        for d in self.bot_hand:
            v1, v2 = get_domino_vals(d)
            if v1 == v2: bot_dbs.append((v1, d))

        if player_dbs or bot_dbs:
            all_dbs = [(v, 'player', d) for v, d in player_dbs] + [(v, 'bot', d) for v, d in bot_dbs]
            val, owner, domino_obj = min(all_dbs, key=lambda x: x[0])
            self.required_first_domino = domino_obj

            if owner == 'player':
                self.current_turn = 'player'
                messagebox.showinfo("Первый ход", f"У вас минимальный дубль ({val}-{val}). Вы ходите первым!")
                self.check_bank_highlight()
                self.draw_table()
            else:
                self.current_turn = 'bot'
                messagebox.showinfo("Первый ход",
                                    f"У противника минимальный дубль ({val}-{val}). Противник ходит первым!")
                self.status_msg = "Противник обдумывает ход..."
                self.draw_table()
                self.bot_timer_id = self.root.after(2000, self.bot_turn)
        else:
            p_max = max([(get_domino_vals(d)[0] + get_domino_vals(d)[1], d) for d in self.current_hand],
                        key=lambda x: x[0])
            b_max = max([(get_domino_vals(d)[0] + get_domino_vals(d)[1], d) for d in self.bot_hand], key=lambda x: x[0])

            if p_max[0] >= b_max[0]:
                self.current_turn = 'player'
                self.required_first_domino = p_max[1]
                messagebox.showinfo("Первый ход", "Дублей нет. У вас старшая костяшка. Ваш ход первый!")
                self.check_bank_highlight()
                self.draw_table()
            else:
                self.current_turn = 'bot'
                self.required_first_domino = b_max[1]
                messagebox.showinfo("Первый ход", "Дублей нет. У противника старшая костяшка. Противник ходит первым!")
                self.status_msg = "Противник обдумывает ход..."
                self.draw_table()
                self.bot_timer_id = self.root.after(2000, self.bot_turn)

    def end_round(self, reason, winner_side):
        # Начисляет очки по строгим правилам и готовит следующий раунд
        self.clear_all_timers()
        self.status_msg = ""

        def get_points(hand):
            if len(hand) == 1 and get_domino_vals(hand[0]) == (0, 0):
                return 12
            return sum(get_domino_vals(d)[0]+get_domino_vals(d)[1] for d in hand)
        p_points = get_points(self.current_hand)
        b_points = get_points(self.bot_hand)

        if reason == "normal":
            if winner_side == "player":
                self.player_score += b_points
                msg = f"Вы выиграли раунд! Вам начислено {b_points} очков противника."
                self.round_winner = 'player'
            else:
                self.bot_score += p_points
                msg = f"Противник выиграл раунд. Ему начислено {p_points} ваших очков."
                self.round_winner = 'bot'
        elif reason == "fish":
            msg = f"Рыба! Игра заблокирована.\nВаши очки: {p_points}\nОчки противника: {b_points}\n"
            if p_points < b_points:
                self.player_score += b_points
                msg += f"Вы победили по правилу Рыбы и получаете {b_points} очков противника!"
                self.round_winner = 'player'
            elif b_points < p_points:
                self.bot_score += p_points
                msg += f"Противник победил по правилу Рыбы и получает {p_points} ваших очков!"
                self.round_winner = 'bot'
            else:
                msg += "Ничья по очкам! Баллы в этом раунде никто не получает."
                self.round_winner = 'player'

        if hasattr(self, 'refresh_top'): self.refresh_top()
        messagebox.showinfo("Раунд завершен", msg)

        self.is_first_round = False

        if self.player_score >= 51:
            messagebox.showinfo("МАТЧ ОКОНЧЕН", f"Ура! Вы набрали {self.player_score} очков и победили в игре!")
            self.reset_entire_game()
        elif self.bot_score >= 51:
            messagebox.showinfo("МАТЧ ОКОНЧЕН",
                                f"Бот набрал {self.bot_score} очков и выиграл матч. Попробуйте снова!")
            self.reset_entire_game()
        else:
            self.start_next_round()

    def start_next_round(self):
        # Стирает игровое поле и собирает чистую колоду для нового раунда
        import random
        from domino import Domino

        self.clear_all_timers()

        self.bazaar = [Domino(i, j) for i in range(7) for j in range(i, 7)]
        random.shuffle(self.bazaar)

        self.current_hand = [self.bazaar.pop() for _ in range(7)]
        self.bot_hand = [self.bazaar.pop() for _ in range(7)]
        self.table_chain = []
        self.status_msg = ""

        if hasattr(self, 'root_id'):
            delattr(self, 'root_id')

        self.draw_hand(self.current_hand)
        self.draw_table()
        if hasattr(self, 'refresh_top'): self.refresh_top()

        self.root.after(500, self.determine_first_turn)

    def reset_entire_game(self):
        # Полностью обнуляет очки матча при выходе в меню
        self.clear_all_timers()
        self.player_score = 0
        self.bot_score = 0
        self.is_first_round = True
        self.round_winner = None
        self.status_msg = ""
        if hasattr(self, 'required_first_domino'):
            delattr(self, 'required_first_domino')

        for widget in self.game_frame.winfo_children():
            widget.destroy()
        self.game_frame.pack_forget()
        self.welcome_frame.pack(fill=tk.BOTH, expand=True)
        self.show_welcome()

    def return_to_welcome(self):
        self.stop_bank_flashing()
        self.pending_domino_index = None #сброс ожидания хода
        self.show_welcome()
