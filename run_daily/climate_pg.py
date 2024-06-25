'''
Helper routines for PostgresQL (PG) DB access.
'''
import                           logging
from datetime                    import datetime
from uuid                        import UUID, uuid4

import                           asyncpg
from ogbujipt.embedding.pgvector import DataDB, PGVectorHelper
from utiloori.ansi_color         import ansi_color

DB_PREFIX = 'climate'
DB_VERSION = 'v0_2_0'

logger = logging.getLogger(__name__)  #This is the only logging config needed here

# ------ SQL queries ---------------------------------------------------------------------------------------------------
# PG only supports proper query arguments (e.g. $1, $2, etc.) for values, not for table or column names
# Table names are checked to be legit sequel table names, and embed_dimension is assured to be an integer

CREATE_MOTD = '''
CREATE TABLE IF NOT EXISTS {db_prefix}_{db_version}_MOTD (
    id SERIAL PRIMARY KEY,
    date_posted DATE NOT NULL,
    message TEXT NOT NULL,
    date_sent DATE
);
'''

RECENT_MOTD = '''
SELECT * FROM
    {db_prefix}_{db_version}_MOTD
WHERE
    date_sent IS NULL 
ORDER BY 
    date_posted 
LIMIT 1
;
'''

UPDATE_MOTD = '''
UPDATE
    {db_prefix}_{db_version}_MOTD
SET
    date_sent = $1
WHERE
    id = $2
;
'''

# ------ SQL queries ---------------------------------------------------------------------------------------------------


class newsDBHelper:
    '''
    Abstract Helper class for news vector database table operations
    '''
    def __init__(self, wrapper, db_connect: dict[str, str | int]):
        self.wrapper = wrapper
        self.db_connect = db_connect
        self.news_table_name = f'{DB_PREFIX}_{DB_VERSION}_news'

    async def setup(self):
        ''' Create session & guild tables if not preexisting '''
        logger.debug(f'Creating news table as needed: {self.news_table_name}')
        self.conn = await DataDB.from_conn_params(
            table_name=self.news_table_name, **self.db_connect)
        await self.conn.create_table()


class MotDDBHelper:
    '''
    Abstract Helper class for Message of the Day database table operations
    '''
    def __init__(self, wrapper, db_connect: dict[str, str | int]):
        self.wrapper = wrapper
        self.db_connect = db_connect
        self.motd_table_name = f'{DB_PREFIX}_{DB_VERSION}_MOTD'

    async def setup(self):
        logger.debug(f'Creating MOTD table as needed: {self.motd_table_name}')
        async with self.wrapper.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    CREATE_MOTD.format(db_prefix=DB_PREFIX, db_version=DB_VERSION)
                )

    async def get_motd(self):
        ''' 
        Returns the most recent MOTD uploaded to DB that hasnt been sent yet
        '''
        today = datetime.now()
        async with self.wrapper.pool.acquire() as conn:
            async with conn.transaction():
                motd = await conn.fetch(
                    RECENT_MOTD.format(db_prefix=DB_PREFIX, db_version=DB_VERSION)
                )
                if motd:
                    await conn.execute(
                        UPDATE_MOTD.format(db_prefix=DB_PREFIX, db_version=DB_VERSION),
                            today,
                            motd[0]['id']
                    )
        
        return motd


class DBHelper:
    # A bit belt & suspenders passing in both pool & conn_params, but we need the latter for OgbujiPT DBs
    def __init__(self, pool: asyncpg.pool.Pool, db_connect: dict[str, str | int]):
        self.pool = pool
        self.db_connect = db_connect
        # db_name, db_host, db_port, db_user, db_password = db_params
        # logger.debug(f'Connecting to PG DB at {ansi_color(db_host, "blue")}:{ansi_color(db_port, "blue")}…')

    @classmethod
    async def from_pool_params(
        cls,
        host,
        port,
        db_name,
        user,
        password,
        embedding_model
    ):
        db_connect = {'user': user, 'password': password, 'db_name': db_name,
                    'host': host, 'port': int(port), 'embedding_model': embedding_model}
        pool = await asyncpg.create_pool(init=PGVectorHelper.init_pool, host=host, port=port, user=user,
                                         password=password, database=db_name)

        obj = cls(pool, db_connect)
        obj.motd = MotDDBHelper(obj, db_connect)
        await obj.motd.setup()
        obj.news = newsDBHelper(obj, db_connect)
        await obj.news.setup()
        return obj