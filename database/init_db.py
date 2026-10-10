from database.db_helper import get_db_connection
import mysql.connector

def init_db():
    """Reads schema.sql and builds the database tables from scratch."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("Reading schema.sql blueprint...")
    
    try:
        # Open and read the schema.sql file
        with open('database/schema.sql', 'r') as f:
            sql_file = f.read()
            
        # Split the file into individual SQL commands by the semicolon
        # MySQL connector prefers executing commands one at a time to track errors accurately
        sql_commands = sql_file.split(';')
        
        for command in sql_commands:
            # Clean up whitespace and ignore empty commands (like after the last semicolon)
            clean_command = command.strip()
            if clean_command:
                cur.execute(clean_command)
                
        # Commit the changes to make them permanent in MySQL
        conn.commit()
        print("! Database successfully initialized from schema.sql !")
        
    except FileNotFoundError:
        print("? Error: Could not find 'schema.sql' file in this directory.")
    except mysql.connector.Error as err:
        print(f"? MySQL Error during initialization: {err.msg}")
    finally:
        cur.close()
        conn.close()

def insert_db():
    """Reads insert.sql and populates the database with initial rows."""
    conn = get_db_connection()
    cur = conn.cursor()
    print("Reading insert.sql data...")
    
    try:
        with open('database/insert.sql', 'r') as f:
            sql_file = f.read()
            
        sql_commands = sql_file.split(';')
        for command in sql_commands:
            clean_command = command.strip()
            if clean_command:
                cur.execute(clean_command)
                
        conn.commit()
        print("! Database successfully inserted from insert.sql !")
        
    except FileNotFoundError:
        print("? Error: Could not find insert.sql file.")
    except mysql.connector.Error as err:
        print(f"? MySQL Error during inserting: {err.msg}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    init_db()
    insert_db()