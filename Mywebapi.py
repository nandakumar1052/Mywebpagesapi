from flask import Flask, jsonify
from flask_caching import Cache
import os
from mysql.connector.pooling import MySQLConnectionPool
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, 'Myenv', '.env'))

def create_app():
    app = Flask(__name__)

    # Flask-Caching setup (use a cache for better performance)
    cache = Cache(app, config={'CACHE_TYPE': 'simple'})

    dbconfig = {
        "host": os.getenv('DB_HOST'),
        "port": os.getenv('DB_PORT'),
        "user": os.getenv('DB_USER'),
        "password": os.getenv('DB_PASSWORD'),
        "database": os.getenv('DB_DATABASE'),
    }

    # Function to fetch data from MySQL (with caching)
    db_pool = MySQLConnectionPool(
        pool_name="mypool",
        pool_size=5,
        pool_reset_session=True,
        **dbconfig
    )

    def get_items_from_db():
        conn = None
        try:
            conn = db_pool.get_connection()
            query = "SELECT Project_details.Project_Id, Project_details.Project_Name, Project_details.Project_Description, Project_details.Project_Github_link, Project_details.Project_Link, Project_Images_table.Image_Id, Project_Images_table.Image FROM Project_details LEFT JOIN Project_Images_table ON Project_details.Project_Id = Project_Images_table.Project_Id;"
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(query)
                data = cursor.fetchall()
                return data

        except Exception as e:
            # Log the exception
            print(f"Error: {e}")
            return None

        finally:
            if conn:
                conn.close()

    @cache.cached(timeout=300, key_prefix='data')
    @app.route('/items/', methods=['GET'])
    def get_items():
        try:
            data = get_items_from_db()

            if data is not None:
                return jsonify(data)

            return jsonify({"error": "Unable to fetch data from the database"}), 500

        except Exception as e:
            # Log the exception
            print(f"Error: {e}")
            return jsonify({"error": "Internal Server Error"}), 500

    return app
