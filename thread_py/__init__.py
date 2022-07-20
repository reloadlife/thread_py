
import ctypes
import threading
import time
import multiprocessing
from typing import Generator
from typing import List
from typing import Tuple
from typing import Union


__all__ = ["ThreadPy"]


class ThreadPy:
    # list to hold all Thread Objects
    threads = []

    class Process(multiprocessing.Process):
        ...
        # to be implemented

    """
    Overriding the threading.Thread class to add
    a kill method and a few other extra required methods and values.
    """
    class Thread(
        threading.Thread
    ):
        def __init__(
            self,
            *args,
            **keywords
        ):
            threading.Thread.__init__(
                self,
                *args,
                **keywords
            )
            self.killed = False
            self.time_started = time.time()

        def start(self):
            self.__run_backup = self.run
            self.run = self.__run
            threading.Thread.start(self)

        def __run(self):
            self.__run_backup()
            self.run = self.__run_backup

        def globaltrace(self, frame, why, arg):
            if why == 'call':
                return self.localtrace
            else:
                return None

        def localtrace(self, frame, why, arg):
            if self.killed:
                if why == 'line':
                    raise SystemExit()
            return self.localtrace

        def get_id(self):
            if hasattr(self, '_thread_id'):
                return self._thread_id
            for id, thread in threading._active.items():
                if thread is self:
                    return id

        def raise_exception(self):
            thread_id = self.get_id()
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
                thread_id,
                ctypes.py_object(SystemExit)
            )
            if res > 1:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
                print('Exception raise failure')

        def kill(self):
            self.killed = True

    @classmethod
    def get_threads(cls) -> List["ThreadPy.Thread"]:
        return cls.threads

    @classmethod
    def create_thread(
        cls,
        *args,
        **kwargs
    ) -> "ThreadPy.Thread":
        thread = cls.Thread(*args, **kwargs)
        cls.threads.append(thread)
        return thread

    @classmethod
    def create_and_start_thread(
        cls,
        name,
        *args,
        **kwargs
    ) -> "ThreadPy.Thread":
        thread = cls.create_thread(*args, **kwargs)
        thread.name = name
        thread.start()
        return thread

    @staticmethod
    def get_thread_count() -> int:
        return len(threading.enumerate())

    @classmethod
    def get_thread_count_without_main(cls) -> int:
        return len(list(cls.get_threads_without_main_thread()))

    @classmethod
    def kill_thread(cls, thread: "ThreadPy.Thread") -> bool:
        thread.kill()
        thread.join()
        if thread in cls.threads:
            cls.threads.remove(thread)
        return True

    @staticmethod
    def kill_these_threads(
        threads: List["ThreadPy.Thread"]
    ) -> Tuple[bool, int]:
        i = 0
        for th in threads:
            th.kill()
            i += 1

        return True, i

    @classmethod
    def kill_threads(cls) -> Tuple[bool, int]:
        i = 0
        for th in cls.get_threads():
            th.kill()
            i += 1

        return True, i

    @classmethod
    def kill_all_threads(cls) -> Tuple[bool, int, int]:
        i = 0
        j = 0
        for th in cls.get_threads_without_main_thread():
            th.kill()
            th.raise_exception()  # force kill
            if th.is_alive():
                th.join()
                j += 1
            i += 1

        return True, i, j

    @staticmethod
    def force_kill_all_threads_except_this() -> bool:
        for thread in threading.enumerate():
            if thread == threading.current_thread():
                continue

            if thread.is_alive():
                if hasattr(thread, 'kill'):
                    thread.kill()
                    thread.join()

        return True

    @staticmethod
    def kill_all_threads_except_this() -> bool:
        for thread in threading.enumerate():
            if thread == threading.current_thread():
                continue

            if thread.is_alive():
                thread.join()

        return True

    @staticmethod
    def get_alive_thread_count() -> int:
        i = 0
        for thread in threading.enumerate():
            if thread == threading.current_thread():
                continue

            if thread.is_alive():
                i += 1

        return i + 1

    @staticmethod
    def thread_count() -> int:
        i = 0
        for _ in threading.enumerate():
            i += 1

        return i + 1

    @classmethod
    def get_threads_without_main_thread(
        cls
    ) -> Union[List[Thread], Generator["ThreadPy.Thread"]]:
        for th in threading.enumerate():
            if type(th) != cls:
                continue

            if th not in cls.threads:
                cls.threads.append(th)

            yield th

    @classmethod
    def wait_for_threads_to_end(cls, __threads):
        alive_threads = []

        while len(alive_threads) > 0:
            time.sleep(0.01)
            for thread in __threads:
                if thread.is_alive():
                    alive_threads.append(thread)

                if not thread.is_alive():
                    cls.kill_thread(thread)

        if len(alive_threads) > 0:
            cls.wait_for_threads_to_end(alive_threads)

    @classmethod
    def kill_all_threads_on_exit(cls):
        if threading.current_thread() is threading.main_thread():
            cls.kill_all_threads_except_this()
