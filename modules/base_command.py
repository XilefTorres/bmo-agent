class BaseCommand:
    def __init__(self, face, bmo_brain):
        self.face = face
        self.bmo_brain = bmo_brain

    @property
    def keywords(self):
        return []

    @property
    def threaded(self):
        return False

    def execute(self, text, actions_manager):
        raise NotImplementedError