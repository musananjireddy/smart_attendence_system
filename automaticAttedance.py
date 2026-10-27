import tkinter as tk
from tkinter import *
import os, cv2
import shutil
import csv
import numpy as np
from PIL import ImageTk, Image
import pandas as pd
import datetime
import time
import re
import tkinter.ttk as tkk
import tkinter.font as font
from student_records import load_student_records

project_path = os.path.dirname(os.path.abspath(__file__))
haarcasecade_path = os.path.join(project_path, "haarcascade_frontalface_default.xml")
trainimagelabel_path = os.path.join(project_path, "TrainingImageLabel", "Trainner.yml")
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
studentdetail_path = os.path.join(
    project_path, "StudentDetails", "studentdetails.csv"
)
attendance_path = os.path.join(project_path, "Attendance")
# for choose subject and fill attendance
def subjectChoose(text_to_speech):
    def FillAttendance():
        subject_name = tx.get().strip()
        if not subject_name:
            notify("Please enter a subject name.")
            return
        if not re.fullmatch(r"[A-Za-z0-9 _-]+", subject_name):
            notify("Use only letters, numbers, spaces, hyphens, or underscores in the subject.")
            return
        if not os.path.isfile(trainimagelabel_path):
            notify("Model not found. Capture student images and click Train Image first.")
            return

        try:
            students = load_student_records(studentdetail_path, trainimage_path)
        except (OSError, csv.Error) as error:
            notify(f"Could not load student records: {error}")
            return
        if not students:
            notify("No student records found. Register students and train the model first.")
            return

        recognizer = cv2.face.LBPHFaceRecognizer_create()
        try:
            recognizer.read(trainimagelabel_path)
        except cv2.error as error:
            notify(f"Could not load the trained model: {error}")
            return

        face_cascade = cv2.CascadeClassifier(haarcasecade_path)
        if face_cascade.empty():
            notify("Could not load the face detector. Check the Haar cascade file.")
            return

        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            cam.release()
            notify("Could not open the camera. Check camera permissions and close other camera apps.")
            return

        recognized = {}
        deadline = time.time() + 20
        camera_error = None
        try:
            while time.time() < deadline:
                success, frame = cam.read()
                if not success or frame is None:
                    camera_error = "Could not read a frame from the camera."
                    break

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.2, 5)
                for (x, y, w, h) in faces:
                    student_id, confidence = recognizer.predict(gray[y : y + h, x : x + w])
                    student_id = str(student_id)
                    name = students.get(student_id) if confidence < 70 else None
                    if name:
                        recognized[student_id] = name
                        label = f"{name} ({student_id})"
                        color = (0, 220, 0)
                    else:
                        label = "Unknown"
                        color = (0, 25, 255)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 3)
                    cv2.putText(frame, label, (x, max(y - 10, 20)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

                cv2.imshow("Filling Attendance - press Esc to finish", frame)
                if cv2.waitKey(30) & 0xFF == 27:
                    break
        except cv2.error as error:
            camera_error = f"Camera or face recognition error: {error}"
        finally:
            cam.release()
            cv2.destroyAllWindows()

        if camera_error:
            notify(camera_error)
            return
        if not recognized:
            notify("No registered student was recognized. Face the camera with good lighting and try again.")
            return

        timestamp = datetime.datetime.now()
        date_column = timestamp.strftime("%Y-%m-%d")
        session_stamp = timestamp.strftime("%Y-%m-%d_%H-%M-%S")
        session_path = os.path.join(attendance_path, subject_name)
        os.makedirs(session_path, exist_ok=True)
        attendance = pd.DataFrame(
            [
                {"Enrollment": student_id, "Name": name, date_column: 1}
                for student_id, name in recognized.items()
            ]
        )
        output_path = os.path.join(
            session_path, f"{subject_name}_{session_stamp}.csv"
        )
        try:
            attendance.to_csv(output_path, index=False)
        except OSError as error:
            notify(f"Could not save attendance: {error}")
            return
        notify(
            f"Attendance saved for {len(recognized)} student(s) in {subject_name}."
        )

    def notify(message):
        Notifica.configure(
            text=message,
            bg="black",
            fg="yellow",
            width=55,
            relief=RIDGE,
            bd=5,
            font=("times", 12, "bold"),
        )
        Notifica.place(x=20, y=250)
        text_to_speech(message)

    ###windo is frame for subject chooser
    subject = Tk()
    # windo.iconbitmap("AMS.ico")
    subject.title("Subject...")
    subject.geometry("580x320")
    subject.resizable(0, 0)
    subject.configure(background="black")
    # subject_logo = Image.open("UI_Image/0004.png")
    # subject_logo = subject_logo.resize((50, 47), Image.ANTIALIAS)
    # subject_logo1 = ImageTk.PhotoImage(subject_logo)
    titl = tk.Label(subject, bg="black", relief=RIDGE, bd=10, font=("arial", 30))
    titl.pack(fill=X)
    # l1 = tk.Label(subject, image=subject_logo1, bg="black",)
    # l1.place(x=100, y=10)
    titl = tk.Label(
        subject,
        text="Enter the Subject Name",
        bg="black",
        fg="green",
        font=("arial", 25),
    )
    titl.place(x=160, y=12)
    Notifica = tk.Label(
        subject,
        text="Attendance filled Successfully",
        bg="yellow",
        fg="black",
        width=33,
        height=2,
        font=("times", 15, "bold"),
    )

    def Attf():
        sub = tx.get()
        if sub == "":
            t = "Please enter the subject name!!!"
            text_to_speech(t)
        else:
                folder = os.path.join(attendance_path, sub)
                if os.path.isdir(folder):
                    os.startfile(folder)
                else:
                    notify("No attendance sheets found for this subject yet.")

    attf = tk.Button(
        subject,
        text="Check Sheets",
        command=Attf,
        bd=7,
        font=("times new roman", 15),
        bg="black",
        fg="yellow",
        height=2,
        width=10,
        relief=RIDGE,
    )
    attf.place(x=360, y=170)

    sub = tk.Label(
        subject,
        text="Enter Subject",
        width=10,
        height=2,
        bg="black",
        fg="yellow",
        bd=5,
        relief=RIDGE,
        font=("times new roman", 15),
    )
    sub.place(x=50, y=100)

    tx = tk.Entry(
        subject,
        width=15,
        bd=5,
        bg="black",
        fg="yellow",
        relief=RIDGE,
        font=("times", 30, "bold"),
    )
    tx.place(x=190, y=100)

    fill_a = tk.Button(
        subject,
        text="Fill Attendance",
        command=FillAttendance,
        bd=7,
        font=("times new roman", 15),
        bg="black",
        fg="yellow",
        height=2,
        width=12,
        relief=RIDGE,
    )
    fill_a.place(x=195, y=170)
    subject.mainloop()
