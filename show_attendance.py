import csv
import glob
import os
import re
import tkinter as tk
from tkinter import ttk

import pandas as pd

from student_records import load_student_records

project_path = os.path.dirname(os.path.abspath(__file__))
attendance_path = os.path.join(project_path, "Attendance")
studentdetail_path = os.path.join(
    project_path, "StudentDetails", "studentdetails.csv"
)
trainimage_path = os.path.join(project_path, "TrainingImage")
legacy_trainimage_path = os.path.join(
    os.path.splitdrive(project_path)[0] + os.sep, "TrainingImage"
)
if (
    not os.listdir(trainimage_path)
    and os.path.isdir(legacy_trainimage_path)
    and os.listdir(legacy_trainimage_path)
):
    trainimage_path = legacy_trainimage_path


def build_attendance_summary(filenames, subject_name, students):
    sessions = []
    session_attendance = {}
    for filename in filenames:
        frame = pd.read_csv(filename)
        if "Enrollment" not in frame.columns:
            raise ValueError(
                f"Missing Enrollment column in {os.path.basename(filename)}"
            )

        session_name = os.path.basename(filename)
        if session_name.startswith(subject_name + "_"):
            session_name = session_name[len(subject_name) + 1 : -4]
        sessions.append(session_name)
        attendance_columns = [
            column for column in frame.columns
            if column not in {"Enrollment", "Name"}
        ]

        for _, row in frame.iterrows():
            enrollment_value = row.get("Enrollment")
            if pd.isna(enrollment_value):
                continue
            enrollment = str(enrollment_value).strip()
            if enrollment.endswith(".0"):
                enrollment = enrollment[:-2]
            if not enrollment:
                continue

            name_value = row.get("Name", "")
            name = str(name_value).strip() if not pd.isna(name_value) else ""
            if not name or name == "[]":
                name = students.get(enrollment, enrollment)
            students.setdefault(enrollment, name)

            if attendance_columns:
                present = any(
                    not pd.isna(row[column])
                    and str(row[column]).strip().lower()
                    not in {"", "0", "0.0", "false", "absent", "[]"}
                    for column in attendance_columns
                )
            else:
                present = True
            session_attendance.setdefault(enrollment, {})[session_name] = present

    if not session_attendance:
        return [], []

    columns = ["Enrollment", "Name", *sessions, "Attendance"]
    output_rows = []
    for enrollment, name in sorted(students.items()):
        attended = session_attendance.get(enrollment, {})
        present_count = sum(attended.get(session, False) for session in sessions)
        percentage = round(present_count * 100 / len(sessions))
        output_rows.append(
            [
                enrollment,
                name,
                *[
                    "Present" if attended.get(session, False) else "Absent"
                    for session in sessions
                ],
                f"{percentage}%",
            ]
        )
    return columns, output_rows


def subjectchoose(text_to_speech):
    subject = tk.Tk()
    subject.title("View Attendance")
    subject.geometry("580x320")
    subject.resizable(False, False)
    subject.configure(background="black")

    title = tk.Label(
        subject,
        text="Enter the Subject Name",
        bg="black",
        fg="green",
        font=("arial", 25),
    )
    title.place(x=130, y=20)

    tk.Label(
        subject,
        text="Subject",
        width=10,
        height=2,
        bg="black",
        fg="yellow",
        font=("times new roman", 15),
    ).place(x=50, y=100)

    entry = tk.Entry(
        subject,
        width=15,
        bd=5,
        bg="black",
        fg="yellow",
        relief=tk.RIDGE,
        font=("times", 30, "bold"),
    )
    entry.place(x=190, y=100)

    status = tk.Label(
        subject, text="", bg="black", fg="yellow", font=("arial", 11), wraplength=520
    )
    status.place(x=25, y=250)

    def notify(message):
        status.configure(text=message)
        text_to_speech(message)

    def calculate_attendance():
        subject_name = entry.get().strip()
        if not subject_name:
            notify("Please enter a subject name.")
            return
        if not re.fullmatch(r"[A-Za-z0-9 _-]+", subject_name):
            notify("Use only letters, numbers, spaces, hyphens, or underscores.")
            return

        subject_dir = os.path.join(attendance_path, subject_name)
        filenames = sorted(
            glob.glob(os.path.join(subject_dir, f"{subject_name}_*.csv"))
        )
        if not filenames:
            notify(f"No attendance sheets found for subject: {subject_name}")
            return

        try:
            students = load_student_records(studentdetail_path, trainimage_path)
        except (OSError, csv.Error) as error:
            notify(f"Could not load student records: {error}")
            return
        try:
            columns, output_rows = build_attendance_summary(
                filenames, subject_name, students
            )
        except (OSError, pd.errors.ParserError, ValueError) as error:
            notify(f"Could not read attendance sheets: {error}")
            return

        if not output_rows:
            notify("The attendance sheets contain no student records.")
            return

        summary_path = os.path.join(subject_dir, "attendance.csv")
        try:
            with open(summary_path, "w", newline="", encoding="utf-8") as output_file:
                writer = csv.writer(output_file)
                writer.writerow(columns)
                writer.writerows(output_rows)
        except OSError as error:
            notify(f"Could not save attendance summary: {error}")
            return

        table_window = tk.Toplevel(subject)
        table_window.title(f"Attendance - {subject_name}")
        table_window.geometry("900x450")
        table = ttk.Treeview(table_window, columns=columns, show="headings")
        for column in columns:
            table.heading(column, text=column)
            table.column(column, width=130, anchor=tk.CENTER)
        for row in output_rows:
            table.insert("", tk.END, values=row)

        vertical_scroll = ttk.Scrollbar(
            table_window, orient=tk.VERTICAL, command=table.yview
        )
        horizontal_scroll = ttk.Scrollbar(
            table_window, orient=tk.HORIZONTAL, command=table.xview
        )
        table.configure(
            yscrollcommand=vertical_scroll.set,
            xscrollcommand=horizontal_scroll.set,
        )
        table.grid(row=0, column=0, sticky="nsew")
        vertical_scroll.grid(row=0, column=1, sticky="ns")
        horizontal_scroll.grid(row=1, column=0, sticky="ew")
        table_window.grid_rowconfigure(0, weight=1)
        table_window.grid_columnconfigure(0, weight=1)
        notify(f"Showing attendance for {subject_name}.")

    def open_sheets():
        subject_name = entry.get().strip()
        if not subject_name:
            notify("Please enter a subject name.")
            return
        if not re.fullmatch(r"[A-Za-z0-9 _-]+", subject_name):
            notify("Use only letters, numbers, spaces, hyphens, or underscores.")
            return
        folder = os.path.join(attendance_path, subject_name)
        if not os.path.isdir(folder):
            notify(f"No attendance sheets found for subject: {subject_name}")
            return
        os.startfile(folder)

    tk.Button(
        subject,
        text="View Attendance",
        command=calculate_attendance,
        bd=7,
        font=("times new roman", 15),
        bg="black",
        fg="yellow",
        height=2,
        width=14,
        relief=tk.RIDGE,
    ).place(x=155, y=170)

    tk.Button(
        subject,
        text="Check Sheets",
        command=open_sheets,
        bd=7,
        font=("times new roman", 15),
        bg="black",
        fg="yellow",
        height=2,
        width=12,
        relief=tk.RIDGE,
    ).place(x=350, y=170)

    subject.mainloop()
