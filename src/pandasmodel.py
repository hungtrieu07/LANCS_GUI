from __future__ import annotations

import datetime
from typing import Any, Literal

import pandas as pd
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QModelIndex, QObject, Qt
from PyQt5.QtWidgets import QStyleOptionViewItem, QWidget


class PandasModel(QtCore.QAbstractTableModel):
    def __init__(
        self,
        df: pd.DataFrame,
        editable: bool = False,
        exclude_col: list[int] | None = None,
        parent: Any | None = None,
    ) -> None:
        super().__init__(parent)
        self.p = parent
        self._df = df
        self.editable = editable
        self.exclude_col = exclude_col or []

    @property
    def dataframe(self) -> None:
        return self._df

    @dataframe.getter
    def dataframe(self) -> pd.DataFrame:
        """Get dataframe"""
        return self._df

    def update_data(self, row: int, col: int, value: Any) -> None:
        if not value and not isinstance(value, list):
            return
        self.setData(self.index(row, col), value)

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role=Qt.ItemDataRole.DisplayRole,
    ) -> QtCore.QVariant | Any | None:
        """Header of table"""
        if role != Qt.ItemDataRole.DisplayRole:
            return QtCore.QVariant()

            # Define a mapping of original column names to new column names
        column_mapping = {
            "Average": "Trung bình",
            "Date": "Ngày",
            "Time": "Giờ",
            "Total": "Tổng số",
            "CAM NAME": "Tên CAMERA",
            "COORD": "Toạ độ",
            "STATUS": "Trạng thái"
            # Add more mappings as needed
        }

        if orientation == Qt.Orientation.Horizontal:
            try:
                # Get the original column name
                original_column_name = self._df.columns.tolist()[section]

                # Check if the column name is in the mapping dictionary
                if original_column_name in column_mapping:
                    return column_mapping[original_column_name]

                # If the column name is not in the mapping, return the original column name
                return original_column_name

            except IndexError:
                return QtCore.QVariant()

        elif orientation == Qt.Orientation.Vertical:
            try:
                return self._df.index.tolist()[section]
            except IndexError:
                return QtCore.QVariant()

    def rowCount(self, parent=QtCore.QModelIndex()) -> int:
        """Number of row"""
        return self._df.shape[0]

    def columnCount(self, parent=QtCore.QModelIndex()) -> int:
        """Number of column"""
        return self._df.shape[1]

    def data(
        self, index: QtCore.QModelIndex, role: int = Qt.ItemDataRole.DisplayRole
    ) -> QtCore.QVariant:
        """Return data from dataframe to table view"""
        if role == Qt.ItemDataRole.DisplayRole:
            return QtCore.QVariant(str(self._df.iloc[index.row(), index.column()]))
        if not index.isValid():
            return QtCore.QVariant()
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignCenter
        return QtCore.QVariant()

    def setData(
        self,
        index: QtCore.QModelIndex,
        value: Any,
        role: int = Qt.ItemDataRole.EditRole,
    ) -> Literal[False] | None:
        if role == QtCore.Qt.EditRole:
            # Handle setting data for EditRole (when the user edits the cell)
            self._df.iat[index.row(), index.column()] = value
            self.dataChanged.emit(index, index, [role])
            return True
        return super().setData(index, value, role)

    def insertRows(
        self,
        row: int,
        count: int,
        init_data: pd.DataFrame | None = None,
        parent: QModelIndex = ...,
    ) -> bool:
        if not self.editable:
            return False
        self.beginInsertRows(QtCore.QModelIndex(), row, row + count - 1)
        if init_data is None:
            init_data = pd.DataFrame([{key: None for key in self._df.columns}])
        self._df = pd.concat(
            [self._df.iloc[:row], init_data, self._df.iloc[row:]],
            ignore_index=True,
            axis=0,
        )
        self.endInsertRows()
        return True

    def removeRows(
        self, rows: list[int], count: int, parent: QModelIndex = ...
    ) -> bool:
        if count <= 0:
            return False
        # for row in rows:
        self.beginResetModel()
        self.beginRemoveRows(QtCore.QModelIndex(), rows[0], rows[-1])
        self._df.drop(labels=rows, axis=0, inplace=True)
        self._df.reset_index(inplace=True, drop=True)
        self.endRemoveRows()
        self.endResetModel()
        return True

    def flags(self, index: QtCore.QModelIndex) -> Qt.ItemFlag:
        """If editible is True, column index in exclude_col will be set to uneditable.
        In the other hand, if editable is False, column index in exclude_col will be set to editable
        """
        flag: Qt.ItemFlags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        flag_edit: Qt.ItemFlags = Qt.ItemIsEditable

        if len(self.exclude_col) > 0:
            if index.column() in self.exclude_col:
                return flag if self.editable else flag | flag_edit

        return flag if not self.editable else flag | flag_edit


class SetupTableModel(PandasModel):
    def __init__(
        self,
        df: pd.DataFrame,
        editable: bool = False,
        exclude_col: list[int] | None = None,
        parent: Any | None = None,
    ):
        super().__init__(df, editable, exclude_col, parent)

    def setData(
        self,
        index: QtCore.QModelIndex,
        value: Any,
        role: int = Qt.ItemDataRole.EditRole,
    ) -> Literal[False] | None:
        """Allow edit cell in table, also overwrite new value in dataframe"""
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            if not value and not isinstance(value, list):
                return False
            if (
                (value in self._df["CAM NAME"].unique())
                and index.column() == 0
                and value != self._df.iat[index.row(), index.column()]
            ):
                QtWidgets.QMessageBox.warning(
                    self.p,
                    "WARNING",
                    "Giá trị: %s đã tồn tại trong CAM NAME. CAM NAME phải là độc nhất."
                    % value,
                )
                return False
            self._df.iat[index.row(), index.column()] = value
            self.dataChanged.emit(index, index, (Qt.DisplayRole,))
        elif role == QtCore.Qt.TextAlignmentRole:
            return QtCore.Qt.AlignCenter
        return True

    def data(
        self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole
    ) -> QtCore.QVariant:
        """Return data from dataframe to table view"""
        if not index.isValid():
            return QtCore.QVariant()
        if role == Qt.ItemDataRole.DecorationRole:
            if index.column() == 4:
                val = str(index.data(Qt.ItemDataRole.DisplayRole))
                if val == "Online":
                    color = QtGui.QColor(0, 255, 0)
                else:
                    color = QtGui.QColor(255, 0, 0)
                return QtCore.QVariant(color)
        elif role == Qt.ItemDataRole.TextColorRole and index.column() == 3:
            lst_coords = self._df.iloc[index.row(), index.column()]
            if len(lst_coords) <= 0:
                color = QtGui.QColor(156, 31, 17)
            else:
                color = QtGui.QColor(50, 194, 25)
            return QtCore.QVariant(color)
        elif role == Qt.ItemDataRole.DisplayRole:
            if index.column() == 3:
                lst_coords = self._df.iloc[index.row(), index.column()]
                if len(lst_coords) <= 0:
                    return QtCore.QVariant("Vùng ROI chưa được khoanh!")
                else:
                    return QtCore.QVariant("Vùng ROI đã được khoanh.")
            else:
                return QtCore.QVariant(str(self._df.iloc[index.row(), index.column()]))
        return QtCore.QVariant()

    def insertRows(
        self,
        row: int,
        count: int,
        init_data: pd.DataFrame | None = None,
        parent: QModelIndex = ...,
    ) -> bool:
        if not self.editable:
            return False
        self.beginInsertRows(QtCore.QModelIndex(), row, row + count - 1)
        if init_data is None:
            init_data = pd.DataFrame([{key: None for key in self._df.columns}])

        self._df = pd.concat(
            [self._df.iloc[:row], init_data, self._df.iloc[row:]],
            ignore_index=True,
            axis=0,
        )
        self.endInsertRows()
        return True


class SettingTableModel(PandasModel):
    def __init__(
        self,
        df: pd.DataFrame,
        editable: bool = False,
        exclude_col: list[int] | None = None,
        parent: Any | None = None,
    ):
        super().__init__(df, editable, exclude_col, parent)

    def set_data(self, df: pd.DataFrame):
        self.beginResetModel()
        self._df = df
        self.endResetModel()

    def setData(
        self,
        index: QtCore.QModelIndex,
        value: Any,
        role: int = Qt.ItemDataRole.EditRole,
    ) -> Literal[False] | None:
        """Allow edit cell in table, also overwrite new value in dataframe"""
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            if not value:
                return False
            if (
                (value in self._df["CAM NAME"].unique())
                and index.column() == 0
                and value != self._df.iat[index.row(), index.column()]
            ):
                QtWidgets.QMessageBox.warning(
                    self.p,
                    "WARNING",
                    "Value: %s already existed in CAM NAME. CAM NAME should be unique."
                    % value,
                )
                return False
            self._df.iat[index.row(), index.column()] = value
            self.dataChanged.emit(index, index, (Qt.DisplayRole,))
        elif role == QtCore.Qt.TextAlignmentRole:
            return QtCore.Qt.AlignCenter
        return True

    def data(
        self, index: QtCore.QModelIndex, role: int = Qt.ItemDataRole.DisplayRole
    ) -> QtCore.QVariant:
        """Return data from dataframe to table view"""
        if role == Qt.ItemDataRole.DisplayRole:
            return QtCore.QVariant(str(self._df.iloc[index.row(), index.column()]))
        if not index.isValid():
            return QtCore.QVariant()
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignCenter
        return QtCore.QVariant()

    def insertRows(
        self,
        row: int,
        count: int,
        init_data: pd.DataFrame | None = None,
        parent: QModelIndex = ...,
    ) -> bool:
        if not self.editable:
            return False
        self.beginInsertRows(QtCore.QModelIndex(), row, row + count - 1)
        if init_data is None:
            init_data = pd.DataFrame([{key: None for key in self._df.columns}])

        init_data["LANE_NUMBER"] = 0
        init_data["HEIGHT"] = 10
        init_data["FOCAL_LENGTH"] = 0.3

        self._df = pd.concat(
            [self._df.iloc[:row], init_data, self._df.iloc[row:]],
            ignore_index=True,
            axis=0,
        )
        self.endInsertRows()
        return True


class ViolationTableModel(QtCore.QAbstractTableModel):

    ROW_BATCH_COUNT = 100

    def __init__(
        self,
        df: pd.DataFrame,
        editable: bool = False,
        exclude_col: list[int] | None = None,
        parent: Any | None = None,
    ) -> None:
        super().__init__(parent)
        self.p = parent
        self._df = df
        self.editable = editable
        self.exclude_col = exclude_col or []

        # Create the icons_mapping dictionary
        icons_mapping = {
            "Sử dụng điện thoại": ":/Using_Phone/icons/using-phone.png",
            "Ngủ gật": ":/Sleep/icons/sleep.png",
        }
        self.icons_mapping = (
            icons_mapping  # Dictionary mapping violation type to icon paths
        )

        # Populate the "Loại vi phạm" column with icons
        if "type" in self._df.columns:
            self._df["type"] = self._df["type"].apply(
                lambda x: self.icons_mapping.get(x, "")
            )

        self.rowsLoaded = ViolationTableModel.ROW_BATCH_COUNT

        self.display_item_count = 200

        self.current_top_index = 0

    @property
    def dataframe(self) -> None:
        return self._df

    @dataframe.getter
    def dataframe(self) -> pd.DataFrame:
        """Get dataframe"""
        return self._df

    def update_data(self, row: int, col: int, value: Any) -> None:
        if not value and not isinstance(value, list):
            return
        self.setData(self.index(row, col), value)

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role=Qt.ItemDataRole.DisplayRole,
    ) -> QtCore.QVariant | Any | None:
        # Define a mapping of original column names to new column names
        self.column_mapping = {
            "type": "Loại vi phạm",
            "path": "Ảnh vi phạm",
            "time": "Thời gian vi phạm",
            "location": "Địa điểm"
            # Add more mappings as needed
        }

        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            try:
                original_column_name = self._df.columns[section]

                if original_column_name in self.column_mapping:
                    return self.column_mapping[original_column_name]
                else:
                    return original_column_name
            except IndexError:
                return None
        return super().headerData(section, orientation, role)

    """ Fetch data for efficiency """

    def canFetchMore(self, index: QtCore.QModelIndex):
        if self._df.shape[0] > self.rowsLoaded:
            return True
        else:
            return False

    def fetchMore(self, index: QtCore.QModelIndex):
        remainder = self._df.shape[0] - self.rowsLoaded
        itemToFetch = min(remainder, ViolationTableModel.ROW_BATCH_COUNT)
        self.beginInsertRows(QtCore.QModelIndex(
        ), self.rowsLoaded, self.rowsLoaded + itemToFetch - 1)
        self.rowsLoaded += itemToFetch
        self.endInsertRows()

    """ Standard method for custom table model"""

    def rowCount(self, parent=QtCore.QModelIndex()) -> int:
        """Number of row"""
        return min(self.rowsLoaded, self._df.shape[0])

    def columnCount(self, parent=QtCore.QModelIndex()) -> int:
        """Number of column"""
        return self._df.shape[1]

    def data(
        self, index: QtCore.QModelIndex, role: int = Qt.ItemDataRole.DisplayRole
    ) -> QtCore.QVariant:
        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() == 0:
                violation_str = self._df.iloc[index.row(), index.column()]
                if violation_str in self.icons_mapping.values():
                    matching_key = next(
                        key
                        for key, value in self.icons_mapping.items()
                        if value == violation_str
                    )
                    return QtCore.QVariant(matching_key)
            elif (
                index.column() == 3
            ):  # Assuming the column index for "Thời gian vi phạm"
                dt_str = self._df.iloc[index.row(), index.column()]
                dt = datetime.datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S.%f")
                formatted_datetime = dt.strftime("%d/%m/%Y %H:%M:%S")
                return QtCore.QVariant(formatted_datetime)
            elif index.column() == 1:  # Assuming the 2nd column is "Xem ảnh"
                return QtCore.QVariant("Xem ảnh")
            else:
                return QtCore.QVariant(str(self._df.iloc[index.row(), index.column()]))
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignCenter
        elif role == Qt.ItemDataRole.DecorationRole:
            if index.column() == 0:  # Assuming the column index for "Loại vi phạm"
                icon_path = str(self._df.iloc[index.row(), index.column()])
                if icon_path in self.icons_mapping.values():
                    icon = QtGui.QIcon()
                    icon.addPixmap(
                        QtGui.QPixmap(
                            icon_path), QtGui.QIcon.Normal, QtGui.QIcon.Off
                    )
                    return QtCore.QVariant(icon)

        return QtCore.QVariant()

    def setData(
        self,
        index: QtCore.QModelIndex,
        value: Any,
        role: int = Qt.ItemDataRole.EditRole,
    ) -> Literal[False] | None:
        if role in [QtCore.Qt.EditRole, QtCore.Qt.DisplayRole]:
            if index.column() == 0:
                self._df.iat[index.row(), index.column()] = value
            self.dataChanged.emit(index, index, [QtCore.Qt.DisplayRole])
            return True
        return super().setData(index, value, role)

    def flags(self, index: QtCore.QModelIndex):
        """If editible is True, column index in exclude_col will be set to uneditable.
        In the other hand, if editable is False, column index in exclude_col will be set to editable
        """
        flag = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        flag_edit = Qt.ItemIsEditable

        if len(self.exclude_col) > 0:
            if index.column() in self.exclude_col:
                return flag if self.editable else flag | flag_edit

        return flag if not self.editable else flag | flag_edit


class ViolationModel(ViolationTableModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def flags(self, index: QtCore.QModelIndex):
        """If editible is True, column index in exclude_col will be set to uneditable.
        In the other hand, if editable is False, column index in exclude_col will be set to editable
        """
        if index.column() == 1:
            return Qt.DecorationRole
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable


class InLineEditDelegate(QtWidgets.QItemDelegate):
    """
    Delegate is important for inline editing of cells
    """

    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ) -> QWidget:
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor: QWidget, index: QModelIndex) -> None:
        text = index.data(Qt.EditRole) or index.data(Qt.DisplayRole)
        editor.setText(str(text))


class SetupTableDelegate(InLineEditDelegate):
    ...


class SettingTableDelegate(InLineEditDelegate):
    ...


class ViolationTableDelegate(QtWidgets.QStyledItemDelegate):
    ...
