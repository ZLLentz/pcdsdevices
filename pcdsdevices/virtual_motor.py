import time
from threading import Thread

from pcdsdevices.interface import FltMvInterface
from ophyd.positioner import SoftPositioner
from ophyd.device import Device

import numpy as np


class VirtualMotor(FltMvInterface, SoftPositioner, Device):
    def __init__(self, move, position, *, name):
        super().__init__(name=name, source='virtual_motor')
        self._move_func = move
        self._position_func = position
        self._goal = self._position

    def _setup_move(self, position, status):
        self._run_subs(sub_type=self.SUB_START, timestamp=time.time())
        self._started_moving = True
        self._moving = True
        self._goal = position
        self._move_func(position)
        self._start_update_thread()

    @property
    def position(self):
        self._update_position()
        return self._position

    def _update_position(self):
        self._set_position(self._position_func())
        self._run_subs(sub_type=self.SUB_READBACK,
                       value=self._position,
                       timestamp=time.time())
        if self.moving and np.isclose(self._goal, self._position):
            self._done_moving(success=True)

    def _update_thread(self):
        while self.moving:
            self._update_position()
            time.sleep(1)

    def _start_update_thread(self):
        thread = Thread(target=self._update_thread)
        thread.start()

    def _done_moving(self, **kwargs):
        self._moving = False
        super()._done_moving(**kwargs)


_my_position = 0
def _get_my_position():
    return _my_position

def _move_to_position(position):
    global _my_position
    _my_position = position

tst_virtual_motor = VirtualMotor(move=_move_to_position,
                                 position=_get_my_position,
                                 name='tst_virtual_motor')
