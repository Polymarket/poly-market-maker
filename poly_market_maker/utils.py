import logging

def setup_logging():
    logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s',
                        level=(logging.DEBUG))