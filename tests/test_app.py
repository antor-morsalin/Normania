"""Exercise the real Tk callback logic without requiring a desktop or camera."""
from types import SimpleNamespace
import pytest
from App.app import TangibleProgrammingApp


class Widget:
    def __init__(self):
        self.options = {}
    def configure(self, **options):
        self.options.update(options)


def app_with(callback):
    app = SimpleNamespace(capture_callback=callback, capture_button=Widget(), capture_status=Widget(),
                          root=SimpleNamespace(update_idletasks=lambda: None))
    app.code = 'old code'
    app.output = 'old output'
    app.set_python_code = lambda code: setattr(app, 'code', code)
    app.set_output = lambda output: setattr(app, 'output', output)
    return app


def test_callback_shows_error_and_allows_retry_without_traceback():
    def fail():
        raise ValueError('Row 3: SHOW needs a value block.')
    app = app_with(fail)
    TangibleProgrammingApp.handle_capture(app)
    assert app.code == ''
    assert app.output == 'Board Error:\nRow 3: SHOW needs a value block.'
    assert app.capture_button.options['state'] == 'normal'
    app.capture_callback = lambda: True
    TangibleProgrammingApp.handle_capture(app)
    assert app.capture_status.options['text'] == 'Capture complete!'


@pytest.mark.parametrize('result,status', [(False,'Capture cancelled.'),
    ('program_error','Board read. Check the program message below.'), (True,'Capture complete!')])
def test_cancel_runtime_error_and_success_states(result,status):
    app = app_with(lambda: result)
    TangibleProgrammingApp.handle_capture(app)
    assert app.capture_button.options['state'] == 'normal'
    assert app.capture_status.options['text'] == status
    assert app.output == 'old output'
