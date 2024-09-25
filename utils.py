import pickle
import sqlite3
import datetime


from models import User, Record, Progress

conn = sqlite3.connect("aaa.db")
cursor = conn.cursor()

class UtilDatabase:
    """
    A utility class for performing common database operations such as creating tables, inserting data, updating data, and selecting data.
    Methods
    -------
    create_table(cursor, name, fields: dict)
        Creates a table with the given name and fields.
        Example:
            UtilDatabase.create_table(cursor, 'users', {'id': 'INTEGER', 'name': 'TEXT'})
    insert_data(cursor, data_name: str, data: dict)
        Inserts data into the specified table.
        Example:
            UtilDatabase.insert_data(cursor, 'users', {'id': 1, 'name': 'Alice'})
    update_data(cursor, data_name: str, data: dict, condition: dict)
        Updates data in the specified table based on the given condition.
        Example:
            UtilDatabase.update_data(cursor, 'users', {'name': 'Bob'}, {'id': 1})
    select_data(cursor, data_name: str, fields: list, condition: dict = None)
        Selects data from the specified table based on the given condition.
        Example:
            UtilDatabase.select_data(cursor, 'users', ['id', 'name'], {'id': 1})
    safe_action(action, conn, cursor, *args, **kwargs)
        Safely performs a database action, committing the transaction if successful or rolling back if an error occurs.
        Example:
            UtilDatabase.safe_action(UtilDatabase.insert_data, conn, cursor, 'users', {'id': 1, 'name': 'Alice'})
    safe_insert_data(conn, cursor, data_name: str, data: dict)
        Safely inserts data into the specified table.
        Example:
            UtilDatabase.safe_insert_data(conn, cursor, 'users', {'id': 1, 'name': 'Alice'})
    safe_select_data(conn, cursor, data_name: str, fields: list, condition: dict = None)
        Safely selects data from the specified table based on the given condition.
        Example:
            UtilDatabase.safe_select_data(conn, cursor, 'users', ['id', 'name'], {'id': 1})
    safe_create_table(conn, cursor, name, fields)
        Safely creates a table with the given name and fields.
        Example:
            UtilDatabase.safe_create_table(conn, cursor, 'users', {'id': 'INTEGER', 'name': 'TEXT'})
    safe_update_data(conn, cursor, data_name: str, data: dict, condition: dict)
        Safely updates data in the specified table based on the given condition.
        Example:
            UtilDatabase.safe_update_data(conn, cursor, 'users', {'name': 'Bob'}, {'id': 1})    
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
    def update_data(cursor, data_name: str = None, data: dict = None, condition: dict = None):
        if data_name is None or data is None or condition is None:
            raise ValueError("data_name, data, and condition should be given")
        
        command_prefix = f"UPDATE {data_name} SET "
        set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
        where_clause = " AND ".join([f"{key} = ?" for key in condition.keys()])
        
        command = f"{command_prefix}{set_clause} WHERE {where_clause}"
        values = list(data.values()) + list(condition.values())

        cursor.execute(command, values)

    @staticmethod
    def select_data(cursor, data_name: str = None, fields: list = None, condition: dict = None):
        if data_name is None or fields is None:
            raise ValueError("data_name and fields should be given")
        command_prefix = f"SELECT {', '.join(fields)} FROM {data_name} "
        command = command_prefix + "WHERE " + " AND ".join([f"{key} = ?" for key in condition.keys()]) if condition else ""

        cursor.execute(command, (*condition.values(),))

        return cursor.fetchall()
    
    @staticmethod
    def safe_action(action, conn, cursor, *args, **kwargs):
        try:
            res = action(cursor, *args, **kwargs)
            conn.commit()
            return res
        except Exception as e:
            print(f"Error: {e}")
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
    def safe_update_data(conn, cursor, data_name: str, data: dict, condition: dict):
        return UtilDatabase.safe_action(UtilDatabase.update_data, conn, cursor, data_name, data, condition)

class UtilDataclass:
    @staticmethod
    def construct_user(conn, name: str, password: str):
        res = UtilDatabase.safe_select_data(conn, cursor, "user",
            ["id", "name"], {"name": name, "password": password})
        
        if not res: return None
        return User(id=res[0][0], name=res[0][1], password=password, records=[], progress=None)

    @staticmethod
    def construct_records(user_id: int):
        res = UtilDatabase.safe_select_data(conn, cursor, "record",
            ["value", "record_time"], {"user_id": user_id})
        
        records = []
        for record in res:
            records.append(Record(value=record[0], user_id=user_id, record_time=record[1]))
        return records
    
    @staticmethod
    def construct_progresses_from_database(user_id: int):
        res = UtilDatabase.safe_select_data(conn, cursor, "progress",
            ["progress_file"], {"user_id": user_id})
        
        if res: return Progress(user_id=user_id, progress_file=res[0][0])

    @staticmethod
    def update_user_to_database(user: User):
        user and user.name and user.password and \
        UtilDatabase.safe_update_data(conn, cursor, "user",
                     {"name": user.name, "password": user.password}, {"id": user.id})
        
        UtilDataclass.update_progress_to_database(user.progress)

        if not user.records: return
        for record in user.records:
            UtilDataclass.update_record_to_database(record)
        
    @staticmethod
    def update_record_to_database(record: Record):
        record and record.user_id and record.value and record.record_time and \
        UtilDatabase.safe_update_data(conn, cursor, "record",
                {"value": record.value, "record_time": record.record_time}, {"user_id": record.user_id})

    @staticmethod
    def update_progress_to_database(progress: Progress):
        progress and progress.progress_file and progress.user_id and \
        UtilDatabase.safe_update_data(conn, cursor, "progress",
                {"progress_file": progress.progress_file}, {"user_id": progress.user_id})
        
class UtilProgress:
    @staticmethod
    def load(progress: Progress):
        progress_file = progress.progress_file
        with open(progress_file, "rb") as f:
            return pickle.load(f)
    
    @staticmethod
    def save(user: User, data):
        now = datetime.datetime.now()
        time_format = now.strftime("%Y-%m-%d-%H:%M")
        progress_file = f"{time_format}.pickle"

        with open(progress_file, "wb") as f:
            pickle.dump(data, f)

        UtilDatabase.safe_update_data(conn, cursor, "progress", 
                                            {"progress_file": progress_file}, {"user_id": user.id})

    @staticmethod
    def get_owner(progress: Progress):
        return UtilDatabase.safe_select_data(conn, cursor, "user", ["name"], {"id": progress.user_id})[0][0]

class UtilRecord:
    @staticmethod
    def get_owner(record: Record):
        # 通过逻辑运算的短路特性，如果record为None，不会执行后面的查询操作
        return record and \
        UtilDatabase.safe_select_data(conn, cursor, "user", ["name"], {"id": record.user_id})[0][0]

    @staticmethod
    def generate_time(record: Record):
        if record: record.record_time = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M")
    
    def format(record: Record):
        if record: return f"{UtilRecord.get_owner(record)}: {record.value} at {record.record_time}"

class UtilUser:
    @staticmethod
    def change_password(user: User, new_password: str):
        user.password = new_password
        UtilDataclass.update_user_to_database(user)
    
    @staticmethod
    def change_name(user: User, new_name: str):
        user.name = new_name
        UtilDataclass.update_user_to_database(user)
    
def test():
    a = UtilDatabase
    a.safe_create_table(conn, cursor, "user", {"id": "INTEGER", "name": "TEXT", "password": "TEXT"})
    a.safe_insert_data(conn, cursor, "user", {"id": 1, "name": "Alice", "password": "123"})
    a.safe_insert_data(conn, cursor, "user", {"id": 2, "name": "Bob", "password": "456"})
    a.safe_insert_data(conn, cursor, "user", {"id": 3, "name": "Charlie", "password": "789"})
    a.safe_update_data(conn, cursor, "user", {"name": "David"}, {"id": 1})
    print(a.safe_select_data(conn, cursor, "user", ["id", "name"], {"id": 1}))

test()
conn.close()