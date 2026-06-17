import tkinter as tk
from settings import DOMINO_WIDTH, DOMINO_HEIGHT, DOUBLE_WIDTH, DOUBLE_HEIGHT

def draw_domino(canvas, x, y, domino, orientation="horizontal", domino_color="#FDF8E2", pip_color="#504E76"):
    if orientation == "horizontal":
        w, h = DOMINO_WIDTH, DOMINO_HEIGHT
    else:
        w, h = DOUBLE_WIDTH, DOUBLE_HEIGHT

    rect_id = canvas.create_rectangle(x, y, x+w, y+h, fill=domino_color, outline=pip_color, width=2)

    if orientation == "horizontal":
        mid_x = x + w//2
        canvas.create_line(mid_x, y, mid_x, y+h, fill=pip_color, width=2)
        left_center = (x + w//4, y + h//2)
        right_center = (x + 3*w//4, y + h//2)
        draw_pips(canvas, left_center[0], left_center[1], domino.a, pip_color)
        draw_pips(canvas, right_center[0], right_center[1], domino.b, pip_color)
    else:
        mid_y = y + h//2
        canvas.create_line(x, mid_y, x+w, mid_y, fill=pip_color, width=2)
        top_center = (x + w//2, y + h//4)
        bottom_center = (x + w//2, y + 3*h//4)
        draw_pips(canvas, top_center[0], top_center[1], domino.a, pip_color)
        draw_pips(canvas, bottom_center[0], bottom_center[1], domino.b, pip_color)

    return rect_id

def draw_pips(canvas, cx, cy, count, color):
    if count == 0:
        return
    r = 4
    patterns = {
        1: [(0, 0)],
        2: [(-12, -12), (12, 12)],
        3: [(-12, -12), (0, 0), (12, 12)],
        4: [(-12, -12), (12, -12), (-12, 12), (12, 12)],
        5: [(-12, -12), (12, -12), (0, 0), (-12, 12), (12, 12)],
        6: [(-12, -12), (12, -12), (-12, 0), (12, 0), (-12, 12), (12, 12)]
    }
    for dx, dy in patterns[count]:
        canvas.create_oval(cx+dx - r, cy+dy - r, cx+dx + r, cy+dy + r, fill=color, outline=color)