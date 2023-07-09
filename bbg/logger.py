import logging


def default_setup():
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,  # fixes issue with config set up after loading loggers
        'formatters': {
            'standard': {'format': '%(asctime)s [%(level_name)s] %(name)s: %(message)s'},
        },
        'handlers': {
            'default': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'standard'
            },
        },
        'loggers': {
            '': {
                'handlers': ['default'],
                'level': 'INFO',
                'propagate': True
            }
        }
    })


def get_logger(name, level=None):
    logger = logging.getLogger(name)
    level is not None and logger.setLevel(level)
    return logger


def class_logger(cls, level=None):
    l_name = cls.__module__ + "." + cls.__name__
    return get_logger(l_name, level)


def instance_logger(name, instance, level=None):
    l_name = "%s.%s.%s" % (instance.__class__.__module__, instance.__class__.__name__, name)
    return get_logger(l_name, level)


LOGGER = get_logger(__name__)
