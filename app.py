from dataclasses import dataclass
import sqlite3

conn = sqlite3.connect("data.db")
cursor = conn.cursor()

class UtilDatabase:
    """
    @param cursor: sqlite3.Cursor
    @param name: str
    @param fields: dict {field_name: field_type (TEXT, INTEGER, REAL, BLOB)}
    """
    @staticmethod
    def create_table(cursor, name, fields: dict):
        if not name or not fields:
            raise ValueError("name and fields should be given")
        command = f"CREATE TABLE IF NOT EXISTS {name} ("

        for field_name, field_type in fields.items():
            command += f"{field_name} {field_type}, "
        command = command[:-2] + ")"
        cursor.execute(command)

    @staticmethod
    def insert_data(cursor, data_name: str = None, data: dict = None):
        if data_name is None or data is None:
            raise ValueError("data_name and data should be given")
        command_prefix = f"INSERT INTO {data_name} "

        data_list = []
        data_length = 0

        for key in data.keys():
            data_list.append(key)
            data_length += 1

        command = command_prefix + str(tuple(data_list)).replace("'", "") + " VALUES (" + "?," * (data_length - 1) + "?)"
        values = [data[key] for key in data.keys()]

        cursor.execute(command, values)

    @staticmethod
    def update_data_by_id(cursor, data_name: str = None, data: dict = None, condition: dict = None):
        if data_name is None or data is None:
            raise ValueError("data_name and data should be given")
        command_prefix = f"UPDATE {data_name} SET "

        data_list = []
        data_length = 0

        for key in data.keys():
            data_list.append(key)
            data_length += 1

        command = command_prefix + ", ".join([f"{key} = ?" for key in data_list]) + " " + \
            "WHERE " + " AND ".join([f"{key} = ?" for key in condition.keys()]) if condition else ""
        values = [data[key] for key in data.keys()]

        cursor.execute(command, values.extend(tuple(condition.values())))

    @staticmethod
    def select_data(cursor, data_name: str = None, fields: list = None, condition: dict = None):
        if data_name is None or fields is None:
            raise ValueError("data_name and fields should be given")
        command_prefix = f"SELECT {', '.join(fields)} FROM {data_name} "
        command = command_prefix + "WHERE " + " AND ".join([f"{key} = ?" for key in condition.keys()]) if condition else ""

        cursor.execute(command, tuple(condition.values()))

        return cursor.fetchall()
    
    @staticmethod
    def safe_action(action, conn, cursor, *args, **kwargs):
        try:
            res = action(cursor, *args, **kwargs)
            conn.commit()
            return res
        except Exception as e:
            conn.rollback()
    
    @staticmethod
    def safe_insert_data(conn, cursor, data_name: str, data: dict):
        return UtilDatabase.safe_action(UtilDatabase.insert_data, conn, cursor, data_name, data)

    @staticmethod
    def safe_select_data(conn, cursor, data_name: str, fields: list, condition: dict = None):
        return UtilDatabase.safe_action(UtilDatabase.select_data, conn, cursor, data_name, fields, condition)
    
    @staticmethod
    def safe_create_table(conn, cursor, name, fields):
        return UtilDatabase.safe_action(UtilDatabase.create_table, conn, cursor, name, fields)

    @staticmethod
    def safe_update_data_by_id(conn, cursor, data_name: str, data: dict, condition: dict):
        return UtilDatabase.safe_action(UtilDatabase.update_data_by_id, conn, cursor, data_name, data, condition)

@dataclass()
class Record:
    id: int
    value: int
    user_id: int
    record_time: str

@dataclass()
class Progress:
    id: int
    user_id: int
    progress_file: str 

@dataclass()
class User:
    id: int
    name: str
    password: str
    records: list[Record]
    progresses: list[Progress]

class UtilDataclass:
    @staticmethod
    def construct_user_from_database(conn, name: str, password: str):
        res = UtilDatabase.safe_select_data(conn, cursor, "user",
            ["id", "name"], {"name": name, "password": password})
        
        if not res: return None
        return User(id=res[0][0], name=res[0][1], password=password, records=[], progresses=[])

    @staticmethod
    def construct_records_from_database(user_id: int):
        res = UtilDatabase.safe_select_data(conn, cursor, "record",
            ["id", "value", "record_time"], {"user_id": user_id})
        
        records = []
        for record in res:
            records.append(Record(id=record[0], value=record[1], user_id=user_id, record_time=record[2]))
        return
    
    @staticmethod
    def construct_progresses_from_database(user_id: int):
        res = UtilDatabase.safe_select_data(conn, cursor, "progress",
            ["progress_file"], {"user_id": user_id})
        
        progresses = []
        for progress in res:
            progresses.append(Progress(progress_file=progress[0]))
        return progresses

    @staticmethod
    def update_user_to_database(user: User):
        UtilDatabase.safe_update_data_by_id(conn, cursor, "user",
                     {"name": user.name, "password": user.password}, f"WHERE id = {user.id}")
        
        for record in user.records:
            UtilDataclass.update_record_to_database(record)
        
        for progress in user.progresses:
            UtilDataclass.update_progress_to_database(progress)
    
    @staticmethod
    def update_record_to_database(record: Record):
        UtilDatabase.safe_update_data_by_id(conn, cursor, "record",
                {"value": record.value, "record_time": record.record_time}, f"WHERE id = {record.id}")

    @staticmethod
    def update_progress_to_database(progress: Progress):
        UtilDatabase.safe_update_data_by_id(conn, cursor, "progress",
                {"progress_file": progress.progress_file}, f"WHERE id = {progress.id}")
        