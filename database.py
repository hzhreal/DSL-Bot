import aiosqlite
from datetime import datetime, timedelta

class Db:
    NAME = "sales.db" # Name of the .db file

    # Create table if not existent
    @staticmethod
    async def createTable() -> None:
        async with aiosqlite.connect(Db.NAME) as db:
            cursor = await db.cursor()

            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS UserTimestamps (
                    username TEXT,
                    timestamp DATETIME
                )
                """)
            
            await db.commit()

    # Add a timestamp associated to an username
    @staticmethod
    async def insertData(username: str) -> None:
        async with aiosqlite.connect(Db.NAME) as db:
            cursor = await db.cursor()

            timestamp = datetime.now()
            await cursor.execute("INSERT INTO UserTimestamps (username, timestamp) VALUES (?, ?)", (username, timestamp))

            await db.commit()

    # Fetch all timestamps less than 2 hours ago or all of them depending on the fetchAll boolean variable
    @staticmethod
    async def fetchData(username: str, fetchAll: bool) -> tuple | list:
        data = []
        async with aiosqlite.connect(Db.NAME) as db:
            cursor = await db.cursor()

            if fetchAll:
                await cursor.execute("SELECT * FROM UserTimestamps WHERE username = ?", (username,))
            else:
                threshold = datetime.now() - timedelta(hours=2)
                await cursor.execute("SELECT * FROM UserTimestamps WHERE username = ? AND timestamp > ?", (username, threshold))

            rows = await cursor.fetchall()

            for row in rows:
                data.append(row)
            
            return data

    # Remove all timestams more than 24 hours ago
    @staticmethod
    async def checkData() -> None:
        async with aiosqlite.connect(Db.NAME) as db:
            cursor = await db.cursor()

            threshold = datetime.now() - timedelta(hours=24)
            await cursor.execute("DELETE FROM UserTimestamps WHERE timestamp < ?", (threshold,))

            await db.commit()

    # Delete a specific sale, index starts with 1 (ROWID)
    @staticmethod
    async def removeData(username: str, index: int) -> None:
        async with aiosqlite.connect(Db.NAME) as db:
            cursor = await db.cursor()

            await cursor.execute("DELETE FROM UserTimestamps WHERE username = ? AND ROWID = ?", (username, index))
            await db.commit()
