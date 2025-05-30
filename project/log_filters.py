from logging import Filter


class SkipStaticFilter(Filter):
    """Logging filter to skip logging of staticfiles"""

    def filter(self, record) -> bool:
        return record.getMessage().find("GET /static/") == -1


class StaticFilter(Filter):
    """Logging filter to log only staticfiles"""

    def filter(self, record) -> bool:
        return record.getMessage().startswith("GET /static/")
