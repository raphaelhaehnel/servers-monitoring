from PySide6.QtCore import QObject, Signal, Property

from models.clusterView import ClusterView


class SharedClusterView(QObject):
    dataChanged = Signal()

    def __init__(self, initial: ClusterView):
        super().__init__()
        self._data = initial

    def _get_data(self):
        return self._data

    def _set_data(self, new):
        self._data = new
        self.dataChanged.emit()

    data = Property(object, _get_data, _set_data, notify=dataChanged)
