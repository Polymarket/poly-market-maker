import logging
import os
import yaml
from logging import config

def setup_logging(default_path='logging.yaml', default_level=logging.INFO, env_key='LOGGING_CONFIG_FILE'):
    """
    :param default_path: 
    :param default_level: 
    :param env_key: 
    :return: 
    """
    log_path = default_path
    log_value = os.getenv(env_key, None)
    if log_value:
        log_path = log_value
    if os.path.exists(log_path):
        with open(log_path) as fh:
            config.dictConfig(yaml.safe_load(fh.read()))
        logging.getLogger(__name__).info("Logging configured with config file!")
    else:
        logging.basicConfig(format='%(asctime)-15s %(levelname)-4s %(threadName)s %(message)s',
                        level=(default_level))
        logging.getLogger(__name__).info("Logging configured with default attributes!")