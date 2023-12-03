import logging

from app import create_app

format = '%(asctime)s [%(levelname)s]:%(message)s'
logging.basicConfig(format=format, encoding='utf-8', level=logging.ERROR)

logger = logging.getLogger('azure')
logger.setLevel(logging.ERROR)

app = create_app()
