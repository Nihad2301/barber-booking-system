from app.database import engine
from sqlalchemy import inspect

connection = engine.connect()
inspector = inspect(engine)
tables = inspector.get_table_names()

print('Tables in database:')
for table in sorted(tables):
    print(f'  - {table}')
    columns = inspector.get_columns(table)
    column_names = [col['name'] for col in columns]
    print(f'    Columns: {column_names}')

connection.close()
