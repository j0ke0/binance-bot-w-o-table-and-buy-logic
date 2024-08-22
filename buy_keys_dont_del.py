import psycopg2
import os

# Function to get API key from PostgreSQL database
def yawi_api_key():
    try:
        # Establish connection to PostgreSQL database
        conn = psycopg2.connect(
            dbname='trading',
            user='postgres',
            host='localhost',
            port='5432',
            password=os.getenv('DATABASE_PASSWORD')
        )

        # Create a cursor object
        cur = conn.cursor()

        # Query to fetch the API key
        cur.execute("SELECT yawi_key FROM yawi_cred;")
        api_key = cur.fetchone()[0]  # Assuming there's only one row and column

        # Close cursor and connection
        cur.close()
        conn.close()

        return api_key

    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data from PostgreSQL", error)
        return None

# Example usage
if __name__ == '__main__':
    api_key = yawi_api_key()
    if api_key:
        print(f"yawi Key retrieved successfully")
    else:
        print("Failed to retrieve yawi Key")

# Function to get API key from PostgreSQL database
def yawi_secret_key():
    try:
        # Establish connection to PostgreSQL database
        conn = psycopg2.connect(
            dbname='trading',
            user='postgres',
            host='localhost',
            port='5432',
            password=os.getenv('DATABASE_PASSWORD')
        )

        # Create a cursor object
        cur = conn.cursor()

        # Query to fetch the API key
        cur.execute("SELECT yawi_secret FROM yawi_cred;")
        api_key = cur.fetchone()[0]  # Assuming there's only one row and column

        # Close cursor and connection
        cur.close()
        conn.close()

        return api_key

    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data from PostgreSQL", error)
        return None

# Example usage
if __name__ == '__main__':
    api_key = yawi_secret_key()
    if api_key:
        print(f"secret Key retrieved successfully")
    else:
        print("Failed to retrieve secret Key")

def save_base_url():
    try:
        # Establish connection to PostgreSQL database
        conn = psycopg2.connect(
            dbname='trading',
            user='postgres',
            host='localhost',
            port='5432',
            password=os.getenv('DATABASE_PASSWORD')
        )

        # Create a cursor object
        cur = conn.cursor()

        # Query to fetch the API key
        cur.execute("SELECT service_name FROM yawi_cred;")
        api_key = cur.fetchone()[0]  # Assuming there's only one row and column

        # Close cursor and connection
        cur.close()
        conn.close()

        return api_key

    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data from PostgreSQL", error)
        return None

# Example usage
if __name__ == '__main__':
    api_key = save_base_url()
    if api_key:
        print(f"url Key retrieved successfully")
    else:
        print("Failed to retrieve url Key")