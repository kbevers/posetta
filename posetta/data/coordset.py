"""Coordinate dataset

Description:
------------

The CoordSet is a data structure that is used internally when translating between
different coordinate data formats.

"""

# Standard library imports
from collections import namedtuple
from typing import Any, Dict, List, Optional, Tuple

# Third party imports
import numpy as np
import pandas as pd

# Posetta imports
from posetta.data import coordset_meta
from posetta.lib import exceptions


# Tables of the CoordSet
_TableSpec = namedtuple("_TableSpec", ("name", "num_cols"))
_TABLES = (
    _TableSpec("epochs", 1),
    _TableSpec("positions", 3),
    _TableSpec("velocities", 3),
    _TableSpec("values", None),
)

# Column specification
ColumnSpec = namedtuple("ColumnSpec", ("table", "idx"))


class CoordSet:
    """Coordinate Dataset

    Attributes:
        num_obs:    Number of rows in dataset.
        meta:       Metainformation about the dataset.
    """

    def __init__(self) -> None:
        """Set up tables for the CoordSet
        """
        self.num_obs: Optional[int] = None
        self.meta = coordset_meta.CoordSetMeta()
        self.columns: Dict[str, ColumnSpec] = dict()
        self.tables = {t.name: Table(t.num_cols) for t in _TABLES}
        for table_name, table in self.tables.items():
            setattr(self, table_name, table)

    def add(
        self, table_name: str, idx: Optional[int], val: np.ndarray, column_name: str
    ) -> None:
        """Add one column of values to the CoordSet
        """
        # Check that number of observations are consistent
        val_num_obs = len(val)
        if self.num_obs is None:
            self.num_obs = val_num_obs
        elif val_num_obs != self.num_obs:
            raise exceptions.CoordSetError(
                f"The number of values of {column_name} are not "
                f"consistent with data already in the CoordSet"
            )

        # Add value to table at specified index
        idx = self.tables[table_name].add_column(column_name, idx, val)

        # Update meta information
        self.columns[column_name] = ColumnSpec(table_name, idx)

    def as_dict(self) -> Dict[str, np.ndarray]:
        """Return columns of coordinate dataset as dictionary
        """
        data = dict()
        for column, table in self.columns.items():
            values = self.tables[table.table].values
            if values is not None:
                data[column] = values[:, table.idx]
        return data

    def as_dataframe(self) -> pd.DataFrame:
        """Return coordinate dataset as Pandas DataFrame
        """
        return pd.DataFrame(self.as_dict())

    def __repr__(self) -> str:
        """A simple string representation of the CoordSet
        """
        tables = [n for n, t in self.tables.items() if t.values is not None]
        return f"{self.__class__.__name__}({', '.join(tables)})"


class Table:
    """Table with columns used in CoordSet
    """

    def __init__(self, num_cols: Optional[int]) -> None:
        """Prepare one table
        """
        self._is_expandable: bool = num_cols is None
        self.num_cols: int = num_cols or 0
        self.values: Optional[np.ndarray] = None
        self.col_names: List[str] = [""] * self.num_cols

    def add_column(self, name: str, idx: Optional[int], val: np.ndarray) -> int:
        """Add one column of values to the Table
        """
        val_num_obs = len(val)

        # Create new array to hold values if necessary
        if self.values is None:
            self.values = np.full((val_num_obs, self.num_cols), np.nan)

        # Add value to table at specified index
        if idx is None:
            if self._is_expandable:
                idx = self.values.shape[1] or 0
                self.values = np.concatenate((self.values, val[:, None]), axis=1)
            else:
                raise ValueError(f"Table is not expandable, specify 'idx'")
        else:
            self.values[:, idx] = val

        return idx

    def __repr__(self) -> str:
        """A simple string representation of the Table
        """
        if self.values is None:
            return f"{self.__class__.__name__}()"
        else:
            return f"{self.__class__.__name__}({self.values.shape})"
