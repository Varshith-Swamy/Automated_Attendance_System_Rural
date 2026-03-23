import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR = os.path.join(BASE_DIR, 'data')
EMBEDDINGS_DIR = os.path.join(DATA_DIR, 'embeddings')
MODELS_DIR = os.path.join(BASE_DIR, 'models')

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(EMBEDDINGS_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'rural-attendance-secret-key-2024')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f'sqlite:///{os.path.join(DATA_DIR, "attendance.db")}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-rural-secret-2024')
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    FACE_DETECTION_CONFIDENCE = 0.5
    FACE_RECOGNITION_THRESHOLD = 0.6
    MIN_FACE_SAMPLES = 3
    MAX_FACE_SAMPLES = 10
    LIVENESS_FRAME_COUNT = 3
    EMBEDDINGS_DIR = EMBEDDINGS_DIR
    MODELS_DIR = MODELS_DIR


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
}
