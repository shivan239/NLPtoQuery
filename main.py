from dotenv import load_dotenv
import os
import sqlite3
import google.generativeai as genai
import streamlit as st

# Load environment variables
load_dotenv()

# Configure Google Generative AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Set up Streamlit app configuration
st.set_page_config(page_title="Gemini SQL Query Retriever")
st.header("Gemini App to Retrieve Data")

# Function to create the database path
def create_database_path(custom_path):
    if not os.path.exists(custom_path):
        os.makedirs(custom_path)
    return custom_path

# Function to interact with Google Gemini API
def get_google_gemini(question, prompt):
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content([prompt, question])
        return response.text.strip()
    except Exception as e:
        print(f"Error in Google Gemini API call: {e}")
        return ""

# Function to execute SQL queries
def sql_query(sql, db_path):
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        print("Executing SQL:", sql)
        cur.execute(sql)
        rows = cur.fetchall()
        conn.commit()
        conn.close()
        return rows
    except sqlite3.OperationalError as e:
        print(f"OperationalError: {e}")
        return []

# Function to create a database and table
def create_database_and_table(db_name, table_name, columns, custom_path):
    try:
        db_path = os.path.join(custom_path, f'{db_name}.db')
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        column_defs = ', '.join([f'"{col.strip()}" TEXT' for col in columns])
        table_info = f"""
        CREATE TABLE IF NOT EXISTS "{table_name.strip()}" (
            {column_defs}
        );
        """
        print("Executing SQL:", table_info)
        cursor.execute(table_info)
        connection.commit()
        st.success(f"Database '{db_name}' and table '{table_name}' with columns {columns} have been created.")
    except sqlite3.OperationalError as e:
        st.error(f"OperationalError: {e}")
        print(f"OperationalError: {e}")
    finally:
        connection.close()

# Function to insert data into the table
def insert_into_table(db_name, table_name, values, custom_path):
    try:
        db_path = os.path.join(custom_path, f'{db_name}.db')
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        placeholders = ', '.join(['?' for _ in values[0]])
        insert_query = f"INSERT INTO \"{table_name}\" VALUES ({placeholders})"
        print("Executing SQL:", insert_query)
        cursor.executemany(insert_query, values)
        connection.commit()
        st.success(f"Data {values} has been inserted into table '{table_name}'.")
    except sqlite3.OperationalError as e:
        st.error(f"OperationalError: {e}")
        print(f"OperationalError: {e}")
    finally:
        connection.close()

# Define prompts for Google Gemini
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
    """,
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

# Allow user to specify a custom path for the database
custom_path = st.text_input("Enter the path where you want to create the database:", value=os.getcwd())
create_path = st.button("Create Path")

if create_path and custom_path:
    DATABASE_PATH = create_database_path(custom_path)
    st.success(f"Path '{DATABASE_PATH}' has been created.")

# Section for database and table creation
db_name = st.text_input("Enter database name:", key="db_name")
table_name = st.text_input("Enter table name:", key="table_name")
columns_input = st.text_input("Enter columns (comma-separated):", key="columns_input")
create_data = st.button("Create Database and Table")

if create_data and db_name and table_name and columns_input:
    columns = [col.strip() for col in columns_input.split(',')]
    create_database_and_table(db_name, table_name, columns, DATABASE_PATH)

# Section for data insertion
values_input = st.text_area("Enter values to insert (one row per line, comma-separated):", key="values_input")
insert_data = st.button("Insert Data")

if insert_data and values_input and db_name and table_name:
    values = [tuple(val.strip() for val in line.split(',')) for line in values_input.strip().split('\n')]
    insert_into_table(db_name, table_name, values, DATABASE_PATH)

# Section for querying the database
st.header("Query the Database")
db_name_query = st.text_input("Enter database name for querying:", key="db_name_query")
question = st.text_input("Input your query here:", key="query")
submit_query = st.button("Ask the Question")

if submit_query and question and db_name_query:
    db_path = os.path.join(DATABASE_PATH, f"{db_name_query}.db")
    response = get_google_gemini(question, prompts[0])
    if response:
        print("Generated SQL:", response)
        data = sql_query(response, db_path)
        st.subheader("The response is:")
        if data:
            for row in data:
                st.write(row)
        else:
            st.write("No data found or an error occurred.")
    else:
        st.write("Failed to generate SQL query from the given question.")
