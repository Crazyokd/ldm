class Base:
    def __init__(self):
        pass

    def __str__(self):
        return '; '.join(f'{k}: {v}' for k, v in self.__dict__.items() if not isinstance(v, list))
