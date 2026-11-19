import json
import socket
import tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import font, messagebox, ttk
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from settings import BUILDINGS, SERVER_URL


ALL_BUILDINGS = "All buildings"
GLASS_PANEL = "#F3EFFF"


def configure_styles(root):
    style = ttk.Style(root)
    style.theme_use("clam")
    page = "#EEE9FC"
    surface = "#FBF9FF"
    ink = "#231B48"
    muted = "#565071"
    border = "#C8BDE9"
    accent = "#593AC5"
    selected = "#E6DEFF"
    danger = "#9E3049"
    system_font = font.nametofont("TkDefaultFont", root=root)
    family = system_font.actual("family")
    size = system_font.actual("size")

    root.configure(background=page)
    style.configure(".", background=page, foreground=ink, font="TkDefaultFont")
    style.configure("Subtitle.TLabel", foreground=muted)
    style.configure("Section.TLabel", font=(family, 14, "bold"))
    style.configure("Empty.TLabel", background=surface, foreground=muted)
    style.configure("Panel.TFrame", background=GLASS_PANEL)
    style.configure("Panel.TLabel", background=GLASS_PANEL)
    style.configure("Section.Panel.TLabel", font=(family, 14, "bold"))
    style.configure("Hint.Panel.TLabel", foreground=muted)
    style.configure("Error.Panel.TLabel", foreground=danger)

    style.configure(
        "TButton", padding=(13, 7), background=surface, bordercolor=border,
        lightcolor=surface, darkcolor=surface, focuscolor=accent,
    )
    style.map(
        "TButton",
        background=[("disabled", page), ("pressed", selected), ("active", page)],
        foreground=[("disabled", muted)],
    )
    style.configure(
        "Primary.TButton", background=accent, foreground=surface, bordercolor=accent,
        lightcolor=accent, darkcolor=accent, focuscolor=surface, font=(family, size, "bold"),
    )
    style.map("Primary.TButton", background=[("pressed", "#42269F"), ("active", "#4F2DB8")])
    style.configure("Danger.TButton", foreground=danger, bordercolor="#D8A2BA")

    for widget_style in ("TEntry", "TCombobox"):
        style.configure(
            widget_style, padding=7, fieldbackground=surface, bordercolor=border,
            lightcolor=surface, darkcolor=surface,
        )
        style.map(widget_style, bordercolor=[("focus", accent)])
    style.configure("TEntry", insertcolor=ink)
    style.configure("TCombobox", background=page, arrowcolor=accent)
    style.map(
        "TCombobox", fieldbackground=[("readonly", surface)],
        selectbackground=[("readonly", selected)], selectforeground=[("readonly", ink)],
    )
    root.option_add("*TCombobox*Listbox.background", surface)
    root.option_add("*TCombobox*Listbox.foreground", ink)
    root.option_add("*TCombobox*Listbox.selectBackground", selected)
    root.option_add("*TCombobox*Listbox.selectForeground", ink)

    style.configure(
        "Treeview", background=surface, fieldbackground=surface, bordercolor=border,
        rowheight=max(29, system_font.metrics("linespace") + 12),
    )
    style.map("Treeview", background=[("selected", selected)], foreground=[("selected", ink)])
    style.configure(
        "Treeview.Heading", padding=(8, 7), background="#E3DCF8", bordercolor=border,
        font=(family, size, "bold"),
    )


class RequestError(Exception):
    """A request failure that can be shown in the Tkinter window."""

    def __init__(self, message, field=None):
        super().__init__(message)
        self.field = field


def request_json(route, values=None):
    data = None if values is None else urlencode(values).encode("utf-8")
    try:
        with urlopen(f"{SERVER_URL}{route}", data=data, timeout=5) as reply:
            return json.loads(reply.read().decode("utf-8"))
    except HTTPError as error:
        message = f"Flask returned an error (HTTP {error.code})."
        field = None
        with error:
            try:
                payload = json.loads(error.read().decode("utf-8"))
            except (ValueError, OSError):
                payload = None
        if isinstance(payload, dict):
            if isinstance(payload.get("error"), str):
                message = payload["error"]
            if isinstance(payload.get("field"), str):
                field = payload["field"]
        raise RequestError(message, field=field) from error
    except (URLError, socket.timeout, ConnectionError) as error:
        if values is not None:
            raise RequestError(
                "Could not confirm the change. Check that Flask is running, "
                "then refresh the list before trying again."
            ) from error
        raise RequestError("Could not reach Flask. Start the server and click Refresh.") from error
    except ValueError as error:
        raise RequestError("Flask sent an unreadable response. Try refreshing the list.") from error


class LostAndFoundWindow:
    def __init__(self, root):
        root.title("Campus Lost & Found")
        root.geometry("980x635")
        root.minsize(760, 545)
        configure_styles(root)

        self.item_name = tk.StringVar(master=root)
        self.building = tk.StringVar(master=root)
        self.building_filter = tk.StringVar(master=root, value=ALL_BUILDINGS)
        self.loaded_building = ALL_BUILDINGS
        self.date_found = tk.StringVar(master=root, value=date.today().isoformat())
        self.status = tk.StringVar(master=root)
        self.form_heading = tk.StringVar(master=root, value="Item details")

        frame = ttk.Frame(root, padding=(24, 8, 24, 18))
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, minsize=124)
        frame.rowconfigure(3, weight=1)

        backdrop = tk.Canvas(frame, highlightthickness=0, borderwidth=0, takefocus=False)
        backdrop.place(relwidth=1, relheight=1, bordermode="outside")

        form = ttk.Frame(frame, style="Panel.TFrame", padding=(12, 9))
        form.grid(row=1, column=0, sticky="ew", padx=8, pady=(8, 19))
        form.columnconfigure(0, weight=4)
        form.columnconfigure(1, weight=5, minsize=322)
        form.columnconfigure(2, minsize=164)
        ttk.Label(form, textvariable=self.form_heading, style="Section.Panel.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 10)
        )

        ttk.Label(form, text="Item name", style="Panel.TLabel").grid(
            row=1, column=0, sticky="w", pady=(0, 4)
        )
        name_entry = ttk.Entry(form, textvariable=self.item_name, width=18)
        name_entry.grid(row=2, column=0, sticky="ew", padx=(0, 12))

        ttk.Label(form, text="Found at", style="Panel.TLabel").grid(
            row=1, column=1, sticky="w", pady=(0, 4)
        )
        building_dropdown = ttk.Combobox(
            form, textvariable=self.building, values=BUILDINGS, state="readonly", width=23
        )
        building_dropdown.grid(row=2, column=1, sticky="ew", padx=(0, 12))

        date_label = ttk.Frame(form, style="Panel.TFrame")
        date_label.grid(row=1, column=2, sticky="ew", pady=(0, 4))
        ttk.Label(date_label, text="Date found", style="Panel.TLabel").pack(side="left")
        ttk.Label(date_label, text="YYYY-MM-DD", style="Hint.Panel.TLabel").pack(side="right")
        date_entry = ttk.Entry(form, textvariable=self.date_found, width=14)
        date_entry.grid(row=2, column=2, sticky="ew")

        self.form_fields = {
            "item_name": (name_entry, 0),
            "building": (building_dropdown, 1),
            "date_found": (date_entry, 2),
        }
        self.field_error = ttk.Label(form, style="Error.Panel.TLabel", justify="left")
        for entry in (name_entry, date_entry):
            entry.bind("<Return>", self.submit_form)
            entry.bind("<KP_Enter>", self.submit_form)

        actions = ttk.Frame(form, style="Panel.TFrame")
        actions.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(12, 0))
        self.primary_button = ttk.Button(
            actions, text="Add Item", command=self.submit_form, style="Primary.TButton", width=14
        )
        self.primary_button.pack(side="left")
        ttk.Button(actions, text="Clear", command=self.clear_form).pack(side="left", padx=(8, 0))
        self.delete_button = ttk.Button(
            actions, text="Delete", command=self.delete_item,
            state="disabled", style="Danger.TButton",
        )
        self.delete_button.pack(side="right")

        filters = ttk.Frame(frame)
        filters.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        filters.columnconfigure(0, weight=1)
        ttk.Label(filters, text="Found items", style="Section.TLabel").grid(
            row=0, column=0, sticky="w", padx=(0, 10)
        )
        ttk.Label(filters, text="Show building").grid(row=0, column=1, sticky="e")
        filter_dropdown = ttk.Combobox(
            filters,
            textvariable=self.building_filter,
            values=(ALL_BUILDINGS, *BUILDINGS),
            state="readonly",
            width=41,
        )
        filter_dropdown.grid(row=0, column=2, sticky="ew", padx=(8, 8))
        filter_dropdown.bind("<<ComboboxSelected>>", self.refresh_items)
        ttk.Button(filters, text="Refresh", command=self.refresh_items).grid(row=0, column=3)

        table_frame = ttk.Frame(frame)
        table_frame.grid(row=3, column=0, sticky="nsew")
        columns = ("id", "item_name", "building", "date_found")
        self.table = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        self.table.bind("<<TreeviewSelect>>", self.select_item)
        self.table.tag_configure("alternate", background="#F2EEFC")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.table.pack(side="left", fill="both", expand=True)
        self.empty_message = ttk.Label(
            table_frame, style="Empty.TLabel", justify="center", wraplength=440
        )

        for column, label, width, stretch in (
            ("id", "ID", 52, False),
            ("item_name", "Item name", 210, True),
            ("building", "Found at", 310, True),
            ("date_found", "Date found", 110, False),
        ):
            self.table.heading(column, text=label, anchor="w")
            self.table.column(column, width=width, stretch=stretch)

        ttk.Label(frame, textvariable=self.status, style="Subtitle.TLabel", wraplength=680).grid(
            row=4, column=0, sticky="w", pady=(10, 0)
        )
        self.decorate_backdrop(backdrop, form)
        name_entry.focus_set()
        root.after_idle(self.refresh_items)

    def decorate_backdrop(self, canvas, form):
        family = font.nametofont("TkDefaultFont", root=canvas).actual("family")
        canvas.create_text(
            34, 43, text="Campus Lost & Found", anchor="w",
            fill="#231B48", font=(family, 26, "bold"), tags="heading",
        )
        canvas.create_text(
            35, 79, text="Staff desk at the Islamic University of Madinah", anchor="w",
            fill="#565071", font="TkDefaultFont", tags="heading",
        )
        image_path = Path(__file__).parent / "assets" / "lost-item-illustration.png"
        illustration = tk.PhotoImage(master=canvas, file=str(image_path))
        self.header_illustration = illustration.subsample(2)
        artwork = canvas.create_image(0, 8, image=self.header_illustration, anchor="ne")

        def draw_gradient(event):
            width, height = event.width, event.height
            canvas.delete("gradient")
            left = (242, 235, 255)
            right = (193, 206, 255)
            for x in range(0, width, 5):
                fraction = x / width
                color = "#%02x%02x%02x" % tuple(
                    round(start + (end - start) * fraction) for start, end in zip(left, right)
                )
                canvas.create_rectangle(
                    x, 0, x + 5, height, fill=color, outline="", tags="gradient"
                )
            canvas.create_polygon(
                width * 0.46, 104, width * 0.67, 6, width * 0.82, 27,
                width + 25, -29, width + 25, 66, width * 0.83, 110,
                width * 0.66, 83, smooth=True, fill="#DAD8FC", tags="gradient",
            )
            canvas.tag_lower("gradient")
            canvas.coords(artwork, width - 24, 8)

        def draw_form_panel(event):
            canvas.delete("form-panel")
            left, top = form.winfo_x() - 8, form.winfo_y() - 8
            right, bottom = left + event.width + 16, top + event.height + 16
            radius = 18
            canvas.create_polygon(
                left, top + radius, left, top, left + radius, top,
                right - radius, top, right, top, right, top + radius,
                right, bottom - radius, right, bottom, right - radius, bottom,
                left + radius, bottom, left, bottom, left, bottom - radius,
                smooth=True, fill=GLASS_PANEL, outline="#FFFCFF", width=2, tags="form-panel",
            )

        canvas.bind("<Configure>", draw_gradient)
        form.bind("<Configure>", draw_form_panel)

    def load_items(self):
        building = self.building_filter.get()
        route = "/items"
        if building != ALL_BUILDINGS:
            route += "?" + urlencode({"building": building})
        items = request_json(route)["items"]
        if building != self.loaded_building and not self.confirm_filter_change(items):
            self.building_filter.set(self.loaded_building)
            self.status.set("Filter change canceled. You can keep editing.")
            return None

        existing_ids = set(self.table.get_children())
        for position, item in enumerate(items):
            item_id = str(item["id"])
            values = (item["id"], item["item_name"], item["building"], item["date_found"])
            tags = ("alternate",) if position % 2 else ()
            if item_id in existing_ids:
                self.table.item(item_id, values=values, tags=tags)
                self.table.move(item_id, "", position)
                existing_ids.remove(item_id)
            else:
                self.table.insert("", position, iid=item_id, values=values, tags=tags)
        if existing_ids.intersection(self.table.selection()):
            self.clear_form()
        self.table.delete(*existing_ids)
        self.loaded_building = building
        if items:
            self.empty_message.place_forget()
        else:
            message = "No items found."
            if building != ALL_BUILDINGS:
                message = f"No items found at {building}."
            self.empty_message.configure(text=message)
            self.empty_message.place(in_=self.table, relx=0.5, rely=0.58, anchor="center")
        return len(items)

    def confirm_filter_change(self, items):
        selected = self.table.selection()
        if not selected or any(str(item["id"]) == selected[0] for item in items):
            return True

        saved_values = self.table.set(selected[0])
        if all(saved_values[field] == value for field, value in self.form_values().items()):
            return True

        return messagebox.askyesno(
            "Discard unsaved changes?",
            "Changing the filter hides the selected item. Choose No to keep editing.",
            default=messagebox.NO,
            parent=self.table.winfo_toplevel(),
        )

    def refresh_items(self, _event=None):
        try:
            count = self.load_items()
        except RequestError as error:
            self.status.set(f"{error} The table keeps the last loaded rows.")
            return
        if count:
            self.status.set(f"Found items shown: {count}")
        elif count == 0:
            self.status.set("")

    def select_item(self, _event=None):
        selected = self.table.selection()
        self.primary_button.configure(text="Save Changes" if selected else "Add Item")
        self.delete_button.state(["!disabled"] if selected else ["disabled"])
        self.form_heading.set(f"Editing item #{selected[0]}" if selected else "Item details")

        if selected:
            self.field_error.grid_remove()
            _, item_name, building, date_found = self.table.item(selected[0], "values")
            self.item_name.set(item_name)
            self.building.set(building)
            self.date_found.set(date_found)

    def clear_form(self):
        self.field_error.grid_remove()
        self.table.selection_remove(*self.table.selection())
        self.select_item()
        self.item_name.set("")
        self.building.set("")
        self.date_found.set(date.today().isoformat())
        self.status.set("")

    def form_values(self):
        return {
            "item_name": self.item_name.get(),
            "building": self.building.get(),
            "date_found": self.date_found.get(),
        }

    def submit_form(self, _event=None):
        if self.table.selection():
            self.edit_item()
        else:
            self.add_item()
        return "break"

    def add_item(self):
        self.submit_change(
            "/items/add", self.form_values(), "Item added successfully.", clear_all=False
        )

    def edit_item(self):
        selected = self.table.selection()
        if selected:
            self.submit_change(
                f"/items/{selected[0]}/edit", self.form_values(), "Changes saved."
            )

    def delete_item(self):
        selected = self.table.selection()
        if not selected:
            return

        item_id = selected[0]
        item_name = self.table.set(item_id, "item_name")
        confirmed = messagebox.askyesno(
            "Delete item",
            f'Delete "{item_name}" (ID {item_id})?',
            default=messagebox.NO,
            parent=self.table.winfo_toplevel(),
        )
        if confirmed:
            self.submit_change(f"/items/{item_id}/delete", {}, "Item deleted.")

    def submit_change(self, route, values, success_message, *, clear_all=True):
        self.field_error.grid_remove()
        try:
            result = request_json(route, values)
        except RequestError as error:
            field = self.form_fields.get(error.field)
            if field is None:
                self.status.set(str(error))
            else:
                widget, column = field
                self.field_error.configure(text=str(error), wraplength=max(widget.winfo_width(), 120))
                self.field_error.grid(row=3, column=column, sticky="w", pady=(4, 0))
                self.status.set("")
                widget.focus_set()
            return

        saved_item = result.get("item")
        if saved_item and self.building_filter.get() not in (ALL_BUILDINGS, saved_item["building"]):
            success_message += f' Switch to {saved_item["building"]} to see it.'

        if clear_all:
            self.clear_form()
        else:
            self.item_name.set("")

        try:
            self.load_items()
        except RequestError:
            self.status.set(f"{success_message} Click Refresh to reload the list.")
        else:
            self.status.set(success_message)


if __name__ == "__main__":
    root = tk.Tk()
    LostAndFoundWindow(root)
    root.mainloop()
