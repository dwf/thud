import urwid
import datetime


class UpCountingTimer(object):
    def __init__(self):
        self.record = []
        self.reset()

    def reset(self):
        self._accumulated = datetime.timedelta(0)
        self._last_started = None
        old_record = list(self.record)
        self.record.clear()
        return old_record

    def start(self):
        self._last_started = datetime.datetime.now()
        self.record.append(('start', self._last_started))

    def pause(self):
        if self._last_started is None:
            raise ValueError('timer not running')
        pause_time = datetime.datetime.now()
        self.record.append(('pause', pause_time))
        self._accumulated += (pause_time - self._last_started)
        self._last_started = None

    def toggle(self):
        if self._last_started is None:
            self.start()
        else:
            self.pause()

    @property
    def current(self):
        if self._last_started is None:
            return self._accumulated
        else:
            current = datetime.datetime.now() - self._last_started
            return self._accumulated + current

    def __str__(self):
        return '\n'.join('%5s %s' % data for data in self.record)


class TaskEdit(urwid.Edit):
    def __init__(self, ui, *args, **kwargs):
        self.ui = ui
        super().__init__(*args, **kwargs)

    def keypress(self, size, key):
        if key == 'enter':
            self.ui.edit_box_enter_callback()
        else:
            return super().keypress(size, key)


class DisableToggle(urwid.WidgetWrap):
    def disable(self):
        self._original = self._w
        self._w = urwid.WidgetDisable(self._w)

    def enable(self):
        self._w = self._original

    def toggle(self):
        if isinstance(self._w, urwid.WidgetDisable):
            self.enable()
        else:
            self.disable()


class UserInterface(urwid.MainLoop):
    def __init__(self):
        self.timer = UpCountingTimer()
        self.edit = TaskEdit(self)
        self.edit_container = DisableToggle(self.edit)
        self.text = urwid.Text(self.time_display)
        widget = urwid.ListBox([
            urwid.Columns([
                ('pack', urwid.Text(' ')),
                self.edit_container,
                ('pack', self.text)
            ], dividechars=1)])
        super().__init__(widget, unhandled_input=self.unhandled_input)
        self.alarm = self.set_alarm_in(0.1, self._update_callback)

    @property
    def time_display(self):
        return str(self.timer.current).split('.')[0]

    def unhandled_input(self, key):
        if key == ' ':
            self.timer.toggle()
        elif key == 'enter':
            self.new_task()
        elif key.lower() == 'q':
            raise urwid.ExitMainLoop

    def new_task(self):
        if getattr(self, '_new_task_wait', False):
            return

        def callback(_, __):
            self.edit_container.enable()
            self.edit.edit_text = ''
            self.timer.reset()
            self._new_task_wait = False

        self.timer.toggle()
        self._new_task_wait = True
        self.set_alarm_in(2, callback)

    def edit_box_enter_callback(self):
        self.timer.start()
        self.edit_container.toggle()

    def _update_callback(self, _, __):
        self.text.set_text(self.time_display)
        self.alarm = self.set_alarm_in(0.1, self._update_callback)

if __name__ == "__main__":
    UserInterface().run()
