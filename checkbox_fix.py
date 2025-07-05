# 1) Remember the last‐emitted state
# In your FilterControls class, store the last FilterState you emitted:

class FilterControls(QHBoxLayout):
    filters_changed = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_filters = FilterState(
            available=False, busy=False, operational=False, type="All", env="All"
        )
        self._last_emitted = None

        # your checkbox + combo setup…

# 2) Only emit when the state really differs
# Change your _on_any_change to compare against _last_emitted:

def _on_any_change(self, *_):
    new_state = FilterState(available=self.checkbox_available.isChecked(), busy=self.checkbox_busy.isChecked(),
        operational=self.checkbox_operational.isChecked(), type=self.combo_type.currentText(),
        env=self.combo_env.currentText()
    )
    # If nothing actually changed, bail out
    if new_state == self._last_emitted:
        return

    self._last_emitted = new_state
    self.filters_changed.emit(new_state)

# Now even if Qt fires toggled(True) then immediately toggled(False), your code won’t re‑emit the same filter state and
# your UI logic downstream won’t see a phantom “uncheck.”