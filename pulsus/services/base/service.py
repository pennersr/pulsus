from abc import ABCMeta, abstractmethod


class BaseService(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self, timeout):
        pass

    @abstractmethod
    def queue_notification(self, notification):
        pass

    @abstractmethod
    def get_feedback(self, block):
        """
        Get the next feedback message.

        Each feedback message is a 2-tuple of (timestamp, device_token).
        """
        pass
