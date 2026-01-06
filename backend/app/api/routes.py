"""API routes (placeholders)."""


def register_routes(app):
    @app.route('/')
    def index():
        return {'status': 'ok'}
