from dataclasses import dataclass

@dataclass()
class Record:
    value: int
    user_id: int
    record_time: str

@dataclass()
class Progress:
    user_id: int
    progress_file: str 

@dataclass()
class User:
    id: int
    name: str
    password: str
    progress: Progress
    records: list[Record]
