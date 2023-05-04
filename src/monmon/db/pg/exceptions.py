""""This file contains custom exceptions for a database"""


class QueryException(Exception):
    """It raises when something is wrong with query execution"""


class OpenConnectionException(
    Exception,
):
    """It raises when something is wrong while opening a connection to a database"""
