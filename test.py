import psycopg
conn = psycopg.connect("dbname=restaurant_api user=postgres password=postgres host=db")
print("Conexión exitosa")
conn.close()