from flask import Flask

def create_app():
    app = Flask(__name__)
    
    # Configurações do app (opcional)
    app.config["SECRET_KEY"] = "sua_chave_secreta"

    # Registra as rotas (importe aqui para evitar circular imports)
    from api.routes import main_routes
    app.register_blueprint(main_routes)

    return app
