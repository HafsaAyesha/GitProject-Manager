from flask import Flask, render_template, request, redirect, url_for
import pymysql
import os

application = Flask(__name__)


def get_connection():
    return pymysql.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "project_manager"),
        cursorclass=pymysql.cursors.DictCursor
    )


@application.route("/")
def home():

    projects = []

    total_projects = 0
    in_progress = 0
    completed = 0
    pending = 0

    try:

        connection = get_connection()

        with connection.cursor() as cursor:

            cursor.execute(
                "SELECT * FROM projects ORDER BY id DESC"
            )

            projects = cursor.fetchall()

        connection.close()


        # Calculate statistics

        total_projects = len(projects)


        in_progress = sum(
            1 for project in projects
            if project["status"] == "In Progress"
        )


        completed = sum(
            1 for project in projects
            if project["status"] == "Completed"
        )


        pending = sum(
            1 for project in projects
            if project["status"] == "Pending"
        )


    except Exception as error:

        print(
            "Database error:",
            error
        )


    return render_template(
        "index.html",
        projects=projects,
        total_projects=total_projects,
        in_progress=in_progress,
        completed=completed,
        pending=pending
    )


@application.route(
    "/add-project",
    methods=["POST"]
)
def add_project():

    name = request.form.get("name")
    description = request.form.get("description")
    status = request.form.get("status")
    progress = request.form.get("progress")

    try:

        connection = get_connection()

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

        connection.commit()

        connection.close()


    except Exception as error:

        print(
            "Database error:",
            error
        )


    return redirect(
        url_for("home")
    )


if __name__ == "__main__":

    application.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )