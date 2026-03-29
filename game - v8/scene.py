from game import Game
class Scene:
    def __init__(self, game):
        self.game: Game = game
    
    def handle_event(self, event):
        pass

    def update(self):
        pass

    def render(self):
        pass
    def handle_resize(self):
        pass