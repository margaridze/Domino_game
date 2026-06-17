class Domino:
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def has_number(self, num):
        return self.a == num or self.b == num

    def other_number(self, num):
        return self.b if self.a == num else self.a

    def is_double(self):
        return self.a == self.b

    def sum(self):
        return self.a + self.b

    def __repr__(self):
        return f"[{self.a}|{self.b}]"