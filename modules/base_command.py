from modules.text_utils import contains_phrase


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

    def matches(self, text):
        """¿Este comando debe atender la frase? Por defecto: alguna keyword como palabra completa."""
        return contains_phrase(text, self.keywords)

    def execute(self, text, actions_manager):
        raise NotImplementedError

    def handle_key(self, key):
        pass
