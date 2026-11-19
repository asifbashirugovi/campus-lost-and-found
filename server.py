import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path

from flask import Flask, jsonify, request

from settings import BUILDINGS, SERVER_HOST, SERVER_PORT


DATABASE_PATH = Path(__file__).with_name("found_items.sqlite3")
ITEM_NOT_FOUND = "This item no longer exists. Click Refresh to update the list."


class InvalidItem(ValueError):
    """A field or filter in the request is missing or invalid."""

    def __init__(self, message, field=None):
        super().__init__(message)
        self.field = field


def read_item_form(form):
    item_name = form.get("item_name", "").strip()
    building = form.get("building", "").strip()
    date_found = form.get("date_found", "").strip()

    if not item_name:
        raise InvalidItem("Enter an item name.", field="item_name")
    if building not in BUILDINGS:
        raise InvalidItem("Choose a campus building from the list.", field="building")

    try:
        found_date = date.fromisoformat(date_found)
    except ValueError as error:
        raise InvalidItem("Enter a valid date in YYYY-MM-DD format.", field="date_found") from error
    if found_date.isoformat() != date_found:
        raise InvalidItem("Enter the date in YYYY-MM-DD format.", field="date_found")

    return {"item_name": item_name, "building": building, "date_found": date_found}


class FoundItemRepository:
    def __init__(self, database_path):
        self.database_path = database_path

    def create_table(self):
        with closing(sqlite3.connect(self.database_path)) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS found_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_name TEXT NOT NULL,
                    building TEXT NOT NULL,
                    date_found TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def list_items(self, building=None):
        query = "SELECT id, item_name, building, date_found FROM found_items"
        parameters = ()
        if building is not None:
            query += " WHERE building = ?"
            parameters = (building,)

        with closing(sqlite3.connect(self.database_path)) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(query + " ORDER BY id DESC", parameters)
            return [dict(row) for row in rows]

    def add_item(self, item):
        with closing(sqlite3.connect(self.database_path)) as connection:
            cursor = connection.execute(
                """
                INSERT INTO found_items (item_name, building, date_found)
                VALUES (:item_name, :building, :date_found)
                """,
                item,
            )
            connection.commit()
            return {"id": cursor.lastrowid, **item}

    def edit_item(self, item_id, item):
        with closing(sqlite3.connect(self.database_path)) as connection:
            cursor = connection.execute(
                """
                UPDATE found_items
                SET item_name = :item_name, building = :building, date_found = :date_found
                WHERE id = :id
                """,
                {"id": item_id, **item},
            )
            if cursor.rowcount == 0:
                return None
            connection.commit()
            return {"id": item_id, **item}

    def delete_item(self, item_id):
        with closing(sqlite3.connect(self.database_path)) as connection:
            cursor = connection.execute("DELETE FROM found_items WHERE id = ?", (item_id,))
            connection.commit()
            return cursor.rowcount > 0


def create_app(database_path=DATABASE_PATH):
    app = Flask(__name__)
    repository = FoundItemRepository(database_path)
    repository.create_table()

    @app.get("/items")
    def list_items():
        building = request.args.get("building")
        if building is not None and building not in BUILDINGS:
            raise InvalidItem("Choose a campus building from the list.")
        return jsonify(items=repository.list_items(building))

    @app.post("/items/add")
    def add_item():
        item = read_item_form(request.form)
        return jsonify(item=repository.add_item(item)), 201

    @app.post("/items/<int:item_id>/edit")
    def edit_item(item_id):
        item = repository.edit_item(item_id, read_item_form(request.form))
        if item is None:
            return jsonify(error=ITEM_NOT_FOUND), 404
        return jsonify(item=item)

    @app.post("/items/<int:item_id>/delete")
    def delete_item(item_id):
        if not repository.delete_item(item_id):
            return jsonify(error=ITEM_NOT_FOUND), 404
        return jsonify(message="Item deleted.")

    @app.errorhandler(InvalidItem)
    def invalid_item(error):
        payload = {"error": str(error)}
        if error.field is not None:
            payload["field"] = error.field
        return jsonify(payload), 400

    @app.errorhandler(sqlite3.Error)
    def database_error(error):
        app.logger.error("Database request failed", exc_info=error)
        return jsonify(error="Could not access the saved items. Try again."), 500

    return app


if __name__ == "__main__":
    create_app().run(host=SERVER_HOST, port=SERVER_PORT)
