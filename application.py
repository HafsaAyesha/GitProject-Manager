from flask import Flask, render_template, request, redirect, url_for
import pymysql
import os

application = Flask(__name__)


# --------------------------------------------------
# Read Docker Secret
# --------------------------------------------------

def read_secret(secret_name):
    secret_path = f"/run/secrets/{secret_name}"

    try:
        with open(secret_path, "r") as file:
            return file.read().strip()

    except FileNotFoundError:
        return os.getenv(secret_name)


# --------------------------------------------------
# Database Connection
# --------------------------------------------------

def get_connection():
    return pymysql.connect(
        host=os.environ.get("DB_HOST", "db"),
        user=os.environ.get("DB_USER", "projectuser"),
        password=read_secret("db_password"),
        database=os.environ.get(
            "DB_NAME",
            "project_manager"
        ),
        cursorclass=pymysql.cursors.DictCursor,
        ssl={"check_hostname": False},
        autocommit=False
    )


def ensure_projects_table(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT NOT NULL,
                status VARCHAR(32) NOT NULL,
                progress TINYINT UNSIGNED NOT NULL
            )
            """
        )


# --------------------------------------------------
# Prevent Browser Caching
# --------------------------------------------------

@application.after_request
def add_no_cache_headers(response):

    response.headers["Cache-Control"] = (
        "no-store, no-cache, must-revalidate, "
        "max-age=0"
    )

    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response


# --------------------------------------------------
# Home Page
# --------------------------------------------------

@application.route("/")
def home():

    projects = []

    total_projects = 0
    in_progress = 0
    completed = 0
    pending = 0

    connection = None

    try:

        connection = get_connection()
        ensure_projects_table(connection)

        with connection.cursor() as cursor:

            cursor.execute(
                "SELECT * FROM projects ORDER BY id DESC"
            )

            projects = cursor.fetchall()


        # ------------------------------------------
        # Calculate Project Statistics
        # ------------------------------------------

        total_projects = len(projects)

        in_progress = sum(
            1
            for project in projects
            if project["status"] == "In Progress"
        )

        completed = sum(
            1
            for project in projects
            if project["status"] == "Completed"
        )

        pending = sum(
            1
            for project in projects
            if project["status"] == "Pending"
        )


    except Exception as error:

        print(
            "Database error:",
            error
        )


    finally:

        if connection:
            connection.close()


    return render_template(
        "index.html",
        projects=projects,
        total_projects=total_projects,
        in_progress=in_progress,
        completed=completed,
        pending=pending
    )


# --------------------------------------------------
# Add Project
# --------------------------------------------------

@application.route(
    "/add-project",
    methods=["POST"]
)
def add_project():

    name = request.form.get("name")
    description = request.form.get("description")
    status = request.form.get("status")
    progress = request.form.get("progress")

    connection = None

    try:

        connection = get_connection()
        ensure_projects_table(connection)

        with connection.cursor() as cursor:

            sql = """
                INSERT INTO projects
                (
                    name,
                    description,
                    status,
                    progress
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s
                )
            """

            cursor.execute(
                sql,
                (
                    name,
                    description,
                    status,
                    int(progress)
                )
            )


        # Save project permanently to MySQL
        connection.commit()

        print(
            "Project added successfully:",
            name
        )


    except Exception as error:

        if connection:
            connection.rollback()

        print(
            "Database error:",
            error
        )


    finally:

        if connection:
            connection.close()


    # Reload home page with latest database data
    return redirect(
        url_for("home")
    )


# --------------------------------------------------
# Run Application
# --------------------------------------------------

if __name__ == "__main__":

    application.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )