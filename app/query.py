import sqlite3
import configparser

import sqlparse

config = configparser.ConfigParser()
config.read("config.ini")

DATABASE = config['PATHES']['DATABASE']


class Opener():
    def __init__(self):
        self.con = sqlite3.connect(DATABASE)

    def __enter__(self):
        return self.con, self.con.cursor()

    def __exit__(self, type, value, traceback):
        self.con.commit()
        self.con.close()

class MissingArguments(Exception):
    pass

class UnknownQueryType(Exception):
    pass

class BadArguments(Exception):
    pass

class Query():
    query_str: str
    statements: str | list[str]

    """
    0 : Single statement
    1 : Script
    """
    query_type: int

    def __init__(self, query_path: str):

        with open(query_path, 'r') as query_file:
            self.query_str = query_file.read()

        # Is multi-part script?
        statements = sqlparse.split(self.query_str)

        if len(statements) == 1:
            self.statements = statements[0]
            self.query_type = 0
        else:
            self.statements = statements
            self.query_type = 1

    def execute(self, *kwargs) -> None | list:
        if self.query_type == 0:
            return self.executeSingleStatement(kwargs)
        elif self.query_type == 1:
            return self.executeScript(kwargs[0])
        else:
            raise UnknownQueryType("query_type is unknown.")

    def executeSingleStatement(self, *kwargs) -> None | list:
        arg_count = self.statements.count('?')

        if len(kwargs) != arg_count:
            raise MissingArguments(f"{arg_count} arguments expected, received {len(kwargs)}.")

        with Opener() as (con, cur):
            cur.execute(self.statements, kwargs)
            return cur.fetchall()

    """
    I'm expecting kwargs to be a list or tuple with the index corresponding to the args that need to be
    passed to that statement
    """
    def executeScript(self, arglist: dict) -> None | list:

        with Opener() as (con, cur):
            for index in range(0, len(self.statements)):

                args = []
                if index in arglist:
                    args = arglist[index]

                statement = self.statements[index]

                cur.execute(statement, args)

            return cur.fetchall()

    def forceExecuteSingle(self, index: int, args: None | list | tuple) -> None | list:

        with Opener() as (con, cur):
            cur.execute(self.statements[index], args)
            return cur.fetchall()
