try:
    from .plugin import Plugin
    plugin = Plugin()
    plugin.register()
except Exception as e:
    import logging
    import traceback
    logger = logging.getLogger()
    logger.debug(repr(e))
    logger.debug(traceback.format_exc())
