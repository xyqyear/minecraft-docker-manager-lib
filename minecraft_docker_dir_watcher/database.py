import aiosqlite

ServersT = dict[str, int]


class Database:
    async def connect(self, db_path: str):
        self._db = await aiosqlite.connect(db_path)
        await self._db.execute(
            "CREATE TABLE IF NOT EXISTS servers (name TEXT PRIMARY KEY, port INTEGER)"
        )

    async def close(self):
        await self._db.close()

    async def get_all_servers(self) -> ServersT:
        async with self._db.execute("SELECT * FROM servers") as cursor:
            servers = await cursor.fetchall()
        return {name: port for name, port in servers}

    async def update_servers(self, servers: ServersT):
        await self._db.executemany(
            "INSERT OR REPLACE INTO servers VALUES (?, ?)",
            servers.items(),
        )
        await self._db.commit()

    async def override_all_servers(self, servers: ServersT):
        await self._db.execute("DELETE FROM servers")
        await self._db.commit()
        await self.update_servers(servers)
