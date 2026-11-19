# Campus Lost & Found

A Python desktop app for the lost-and-found desk at the Islamic University of Madinah. A desk worker can add, view, edit, delete, and filter records by building. Tkinter contacts Flask automatically, and Flask saves the records in SQLite.

Students ask a desk worker to look up a missing item. The worker uses **Show building** to narrow the list. Run the app on a staff-operated computer because anyone using the staff window can change records or confirm a deletion.

## Run the app

Use Python 3.10 or newer with Tkinter. Run these commands from the project folder in the first terminal.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python server.py
```

Flask listens on `127.0.0.1:5050` and creates `found_items.sqlite3` in the project folder when it starts. Leave the server running. Open a second terminal in the same folder and start Tkinter.

```sh
. .venv/bin/activate
python client.py
```

If Flask and Tkinter are already running from an earlier version, close both and start them again. Flask opens the existing database on startup.

The window uses a lavender-to-blue gradient, a glass-style form, and a violet primary button. A lost-item illustration sits in the top-right corner. The button shows **Add Item** for a new record and **Save Changes** when you select an existing record. Press **Enter** from the item name or date field to use that action. The form heading shows the selected record's ID.

## Edit or delete an item

- Select a row to fill the form. Change the details and click **Save Changes**.
- Select a row and click **Delete**. The dialog shows the item name and ID. Confirm to remove it or choose **No** to keep it.
- Click **Clear** to deselect the row and start a new entry. If another window has already deleted the selected item, click **Refresh** to update the list.

## Filter by building

Choose a location in **Show building** to update the table, or choose **All buildings** to see all records. **Refresh** reloads the current view. If the filter finds no matches, the table displays a message. If the filter would hide a row you are editing, the app asks before discarding unsaved changes. Choose **No** to keep editing or **Yes** to apply the filter and clear the draft. If you save an item in a different building, the status confirms the save and names the building where you can find it.

In `client.py`, `load_items` sends a `building` query parameter to `GET /items` when a building is selected. In `server.py`, `FoundItemRepository.list_items` uses a SQL placeholder to match the building. This is the extra feature for the course project.

## Generate the text report

With Flask running, open a terminal in the project folder and run these commands.

```sh
. .venv/bin/activate
python report.py
```

The command prints the location of `found_items_report.txt`. The report uses UTF-8 and lists each item's ID, date, and name under its campus building. It includes all saved items, independent of the building shown in Tkinter.

In `report.py`, `fetch_items` gets the records from `GET /items`, and `format_report` groups the list of item dictionaries by building. `main` starts one thread to run `write_report` and waits with `join()` before printing the result. The worker opens the file with a `with` block and replaces the previous report after the new one is written.

## How Add Item works

Enter an item name, choose a building, enter the date, and click **Add Item**.

1. `LostAndFoundWindow.add_item` in `client.py` reads the form. `request_json` encodes the fields and sends `POST /items/add`.
2. The `add_item` route in `server.py` validates the fields. `FoundItemRepository.add_item` saves the record using SQL placeholders and commits the write.
3. Flask replies with JSON and status `201`. Tkinter calls `GET /items` and updates its table from the returned list.

Each record is a dictionary with an ID, item name, building, and date. `request_json` handles network and HTTP errors. For an invalid form field, Flask includes the field name in its error response. Tkinter shows the message below that field and moves keyboard focus there so you can correct it.

Edits send the same form fields to `POST /items/<id>/edit` and reuse `read_item_form` in `server.py`. Deletion uses `POST /items/<id>/delete`. Both repository methods use the selected ID in the SQL `WHERE` clause.

## Course topics

| Topic | Where to find it |
| --- | --- |
| Python collections and control flow | `report.py` uses a dictionary of building names and lists of records in `format_report`. |
| Exceptions | `client.py` handles HTTP, connection, and timeout errors in `request_json`. `report.py` handles file errors in `write_report`. |
| Classes | `server.py` uses `FoundItemRepository` for database work. `client.py` uses `LostAndFoundWindow` for the interface. |
| SQLite | `FoundItemRepository` creates the table, uses a connection per operation, and binds values with SQL placeholders. |
| Threads and files | `report.py` starts and joins a worker in `main`. The worker writes the UTF-8 file in `write_report`. |
| Tkinter | `LostAndFoundWindow` builds the form, table, and buttons, and updates the status after requests. |
| Client and server | `request_json` in `client.py` sends GET and form-encoded POST requests and decodes JSON. |
| Flask | `create_app` in `server.py` defines the routes and JSON error handlers. `read_item_form` validates add and edit requests. |

## Quick check

Add **Black umbrella** at **Central Library**. Restart Flask and Tkinter and confirm the row is still there. Try an empty name and an impossible date. Stop Flask, click **Refresh**, then restart Flask and click **Refresh** again from the same window.

## Verification

- Installed the dependencies from `requirements.txt` in a clean project copy. The app created a fresh SQLite database, and a saved record appeared after launching a fresh Flask process. The Tkinter and report checks also passed from the clean copy.
- Adding the umbrella displayed one row and saved the expected values in SQLite. The same record appeared in a fresh Tkinter process after Flask restarted.
- The window displayed an empty list, rejected a blank name and an impossible date, and kept the form values after a validation error. Flask also rejected an unknown building.
- When Flask stopped, the window showed a connection error and kept the loaded rows. Refresh worked from the same window when Flask restarted.
- Editing and confirmed deletion affected only the selected ID. An invalid edit kept the saved values, and choosing **No** left both records in place.
- After one window deleted an item, saving it from the second window showed a clear missing-item message. Refresh removed the stale row. The Flask API returned JSON with status `404` for repeated edit and delete requests.
- The building filter showed only matching records and reported an empty result by building. Adding or moving an item outside the current filter kept the filter active and named the item's building. After Flask restarted, **Refresh** applied the selected filter in the same window.
- Invalid names, buildings, and dates displayed a message under the correct field and moved keyboard focus to it. Canceling a filter change kept the selected row and its draft. Confirming applied the filter without saving the draft.
- At the minimum window size, the table and the longest building name fit. The illustration stayed to the right of the title at three tested window sizes. Inline errors appeared below the correct fields, and Enter submitted the displayed action.
- The report command produced an empty report and a grouped UTF-8 report with Arabic and accented names. A file error returned a clear message. Stopping Flask or receiving an HTTP error preserved the last saved report.

Verification used temporary databases, including one with a record from the original schema. A first run creates an empty list.

## Design and credits

The design describes the app and report and credits the university’s campus map. [System design](DESIGN.md)

The PowerPoint deck contains the live demo sequence, the Add Item walkthrough, and the report example. [Demo slides](Campus_Lost_and_Found_Demo.pptx)

OpenAI Codex assisted with the design, implementation, verification, and presentation materials.

The header illustration was created with OpenAI ImageGen. [Image asset](assets/lost-item-illustration.png)
