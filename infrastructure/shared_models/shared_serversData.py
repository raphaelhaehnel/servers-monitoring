from PySide6.QtCore import QObject, Signal, Property

from models.serversData import ServersData


class SharedServersData(QObject):
    dataChanged = Signal()

    def __init__(self, initial: ServersData):
        super().__init__()
        self._data = initial

    def _get_data(self):
        return self._data

    def _set_data(self, new):
        print("Setting shared server data...")
        self._data = new
        self.dataChanged.emit()

    data: ServersData = Property(object, _get_data, _set_data, notify=dataChanged)

    @property
    def typed_data(self) -> ServersData:
        return self._data