import sqlite3

# to connect sqlite
connection = sqlite3.connect('student.db')
cursor = connection.cursor()

## create the table
table_info="""
Create table STUDENT (NAME VARCHAR(25), CLASS VARCHAR(25),
SECTION VARCHAR(25), MARKS INT);"""


cursor.execute(table_info)


## Insert Some more records
cursor.execute('''Insert Into STUDENT values('Krish', 'Data Science', 'A',90)''')
cursor.execute('''Insert Into STUDENT values ('Sudhanshu', 'Data Science', 'B',100)''')
cursor.execute('''Insert Into STUDENT values ('Darius', 'Data Science', 'A', 86)''')
cursor.execute('''Insert Into STUDENT values('Vikash', 'DEVOPS', 'A',50)''')
cursor.execute('''Insert Into STUDENT values ('Dipesh', 'DEVOPS', 'A', 35)''')


## Display all the records
print("The inserted records are")
data=cursor.execute('''Select * From STUDENT''')


for row in data:
    print(row)

connection.commit()
connection.close()