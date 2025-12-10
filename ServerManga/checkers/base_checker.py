from abc import ABC, abstractmethod

class BaseChecker(ABC):
    @staticmethod
    @abstractmethod
    def check_single(manga_data, mode_debug=False, logger=None):
        """
        return: {
            'manga_id': int,
            'title': str,
            'has_new': bool,
            'new_chapters_count': int,
            'last_checked_chapter': str,
            'current_chapter': str
        }
        """
        pass

    @staticmethod
    @abstractmethod
    def check_batch(manga_list, mode_debug=True, logger=None):
        """
        return: list[dict] (mismo formato que check_single)
        """
        pass