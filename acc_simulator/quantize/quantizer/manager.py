import importlib
import logging

logger = logging.getLogger(__name__)


class KernelManager:
    _autotune_is_enabled = False

    @classmethod
    def enable_autotune(cls):
        cls._autotune_is_enabled = True
        cls._reload_all_modules()
        logger.info("Autotune enabled")

    @classmethod
    def disable_autotune(cls):
        cls._autotune_is_enabled = False
        cls._reload_all_modules()
        logger.info("Autotune disabled")

    @classmethod
    def autotune_is_enabled(cls):
        return cls._autotune_is_enabled

    @staticmethod
    def _reload_all_modules():
        from .minifloat.kernels import cast as minifloat_cast
        from .mxfp.kernels import cast as mxfp_cast

        importlib.reload(minifloat_cast)
        importlib.reload(mxfp_cast)
