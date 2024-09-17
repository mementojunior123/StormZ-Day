from utils.my_timer import Timer
from typing import Callable
from utils.helpers import Task

class TaskScheduler:
    def __init__(self) -> None:
        self.scheduled_tasks : dict[Task, Timer] = {}
        self.continous_tasks : dict[Task, Timer] = {}

    def schedule_task(self, time : float|tuple[float, Callable[[], float], float], callback : Callable, *args, **kwargs):
        new_task = Task(callback, *args, **kwargs)
        t = type(time)
        if (t == int) or t == (float):
            self.scheduled_tasks[new_task] = Timer(time)
        else:
            self.scheduled_tasks[new_task] = Timer(time[0], time[1], time[2])
        return new_task
    
    def schedule_continuous_task(self, time : float|tuple[float, Callable[[], float], float], callback : Callable, *args, **kwargs):
        new_task = Task(callback, *args, **kwargs)
        t = type(time)
        if t == int or float:
            self.continous_tasks[new_task] = Timer(time)
        else:
            self.continous_tasks[new_task] = Timer(time[0], time[1], time[2])
        return new_task
    
    def update(self):
        to_remove = []
        for task in self.scheduled_tasks:
            if self.scheduled_tasks[task].isover():
                task.execute()
                to_remove.append(task)
        
        for task in to_remove:
            self.scheduled_tasks.pop(task)

        to_remove.clear()

        for task in self.continous_tasks:
            task.execute()
            if self.continous_tasks[task].isover():
                to_remove

        for task in to_remove:
            self.continous_tasks.pop(task)