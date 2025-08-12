# -*- coding: utf-8 -*-
# 
# Copyright (c) 2025~2999 - Cologler <skyoflw@gmail.com>
# ----------
# 
# ----------

from logging import Logger


class LoggerDependentClass:
    def __init__(self, logger: Logger) -> None:
        self.logger = logger


def loggerDependentFunc(logger: Logger) -> Logger:
    return logger
