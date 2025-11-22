import json
import pandas as pd

import pickle


def obj_to_file(obj, file_path: str):
    """Serialize any Python object to a file."""
    with open(file_path, "wb") as f:
        pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)


def file_to_obj(file_path: str):
    """Load any Python object from a pickle file."""
    with open(file_path, "rb") as f:
        return pickle.load(f)


def dict_to_file(data: dict, file_path: str, fmt: str = "json"):
    fmt = fmt.lower()

    if fmt == "json":
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)


def file_to_dict(file_path: str, fmt: str = "json") -> dict:
    fmt = fmt.lower()

    if fmt == "json":
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)


def df_to_file(df: pd.DataFrame, file_path: str, fmt: str = "csv"):
    fmt = fmt.lower()

    if fmt == "csv":
        df.to_csv(file_path, index=False)


def file_to_df(file_path: str, fmt: str = "csv") -> pd.DataFrame:
    fmt = fmt.lower()

    if fmt == "csv":
        return pd.read_csv(file_path)
