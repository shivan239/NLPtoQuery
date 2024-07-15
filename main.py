from dotenv import load_dotenv
import os
import sqlite3
import google.generativeai as genai
import streamlit as st

load_dotenv()

# Securely load the Google API key from environment variables
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_google_gemini(question, prompt):
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content([prompt, question])
        return response.text.strip()
    except Exception as e:
        print(f"Error in Google Gemini API call: {e}")
        return ""

def sql_query(sql, db_path):
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        conn.commit()
        conn.close()
        return rows
    except sqlite3.OperationalError as e:
        print(f"OperationalError: {e}")
        return []

def create_database_and_table(db_path, table_name, columns):
    try:
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()

        column_defs = ', '.join([f'"{col.strip()}" TEXT' for col in columns])
        table_info = f"""
        CREATE TABLE IF NOT EXISTS "{table_name.strip()}" (
            {column_defs}
        );
        """
        cursor.execute(table_info)
        connection.commit()
        st.success(f"Database '{db_path}' and table '{table_name}' with columns {columns} have been created.")
    except sqlite3.OperationalError as e:
        st.error(f"OperationalError: {e}")
    finally:
        connection.close()

def insert_into_table(db_path, table_name, rows):
    try:
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()

        placeholders = ', '.join(['?' for _ in rows[0]])
        insert_query = f"INSERT INTO \"{table_name}\" VALUES ({placeholders})"
        cursor.executemany(insert_query, rows)
        connection.commit()
        st.success(f"Data has been inserted into table '{table_name}'.")
    except sqlite3.OperationalError as e:
        st.error(f"OperationalError: {e}")
    finally:
        connection.close()

def list_databases(path):
    return [f for f in os.listdir(path) if f.endswith('.db')]

def list_tables(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cur.fetchall()]
        conn.close()
        return tables
    except sqlite3.OperationalError as e:
        return []

# Define your prompts
prompts = [
    """
    You are an expert in converting English questions to SQL queries!
    The SQL database has the following schema: 
    - Table name: STUDENT
    - Columns: NAME, CLASS, SECTION, MARKS

    For example:
    Example 1 - How many entries of records are present?
    The SQL command will be something like this: SELECT COUNT(*) FROM STUDENT;

    Example 2 - Tell me all the students studying in Data Science class?
    The SQL command will be something like this: SELECT * FROM STUDENT WHERE CLASS="Data Science";

    The SQL code should not have ''' in the beginning or end, and the word SQL should not appear in the output.
    Example 3 -  Select all from info? The sql command will be something like this: SELECT * FROM info """,
    """
    You are an expert in converting English tasks to SQL queries! The task is to create a new database, a table within that database, and insert some rows into the table.

    For example:
    Example 1 - Create a database named SCHOOL.
    The SQL command will be something like this: CREATE DATABASE SCHOOL;

    Example 2 - Create a table named STUDENT with columns NAME, CLASS, SECTION, and MARKS.
    The SQL command will be something like this:
    CREATE TABLE STUDENT (
        NAME VARCHAR(25),
        CLASS VARCHAR(25),
        SECTION VARCHAR(25),
        MARKS INT
    );

    Example 3 - Insert rows into the STUDENT table.
    The SQL command will be something like this:
    INSERT INTO STUDENT (NAME, CLASS, SECTION, MARKS) VALUES ('John Doe', '10th', 'A', 85);
    INSERT INTO STUDENT (NAME, CLASS, SECTION, MARKS) VALUES ('Jane Smith', '11th', 'B', 90);
    """
]

# Set up Streamlit app
st.set_page_config(page_title="Gemini SQL Query Retriever", layout="wide")
st.header("Gemini App to Retrieve Data")

# Section for user to specify the database path
st.subheader("Specify Database Path")
database_path = st.text_input("Enter the path where databases should be stored:")

if database_path:
    DATABASE_PATH = database_path
    os.makedirs(DATABASE_PATH, exist_ok=True)
    st.success(f"Databases will be stored in: {DATABASE_PATH}")

# Section for database and table creation
st.subheader("Create Database and Table")
db_name = st.text_input("Enter database name:", key="db_name")
table_name = st.text_input("Enter table name:", key="table_name")
columns_input = st.text_input("Enter columns (comma-separated):", key="columns_input")
create_data = st.button("Create Database and Table")

if create_data and db_name and table_name and columns_input:
    columns = [col.strip() for col in columns_input.split(',')]
    db_path = os.path.join(DATABASE_PATH, f'{db_name}.db')
    create_database_and_table(db_path, table_name, columns)

# Section for data insertion
st.subheader("Insert Data into Table")
values_input = st.text_area("Enter multiple rows of values to insert (one row per line, comma-separated values):", key="values_input")
insert_data = st.button("Insert Data")

if insert_data and values_input and db_name and table_name:
    rows = [tuple(val.strip() for val in row.split(',')) for row in values_input.split('\n') if row.strip()]
    db_path = os.path.join(DATABASE_PATH, f'{db_name}.db')
    insert_into_table(db_path, table_name, rows)

# Section for querying the database
st.subheader("Query the Database")

if database_path:
    databases = list_databases(DATABASE_PATH)
    selected_db = st.selectbox("Select database:", databases, key="selected_db")
    if selected_db:
        db_path = os.path.join(DATABASE_PATH, selected_db)
        tables = list_tables(db_path)
        selected_table = st.selectbox("Select table:", tables, key="selected_table")

        if selected_table:
            question = st.text_input("Input your query here:", key="query")
            submit = st.button("Ask the Question")

            if submit and question:
                response = get_google_gemini(question, prompts[0])
                if response:
                    data = sql_query(response, db_path)
                    st.subheader("The response is:")
                    if data:
                        for row in data:
                            st.write(row)
                    else:
                        st.write("No data found or an error occurred.")
                else:
                    st.write("Failed to generate SQL query from the given question.")
