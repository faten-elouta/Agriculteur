from ui.step_nav import render_step_indicator


def test_render_step_indicator_marks_done_active_todo():
    out = render_step_indicator(2, ["A", "B", "C"])
    assert out.count("step-item") == 3
    assert 'step-item done' in out
    assert 'step-item active' in out
    assert 'step-item todo' in out


def test_render_step_indicator_escapes_labels():
    out = render_step_indicator(1, ["<x>"])
    assert "<x>" not in out
    assert "&lt;x&gt;" in out
