# 📁 strategy_modules/base_strategy.py
from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    @abstractmethod
    def should_enter_position(self, df, **kwargs):
        pass

    @abstractmethod
    def should_exit_position(self, df, **kwargs):
        pass

    @abstractmethod
    def get_features(self, df, **kwargs):
        pass

    @property
    @abstractmethod
    def name(self):
        pass
