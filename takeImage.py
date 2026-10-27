import csv
import os
import shutil
import time
import cv2



# take Image of user
def TakeImage(l1, l2, haarcasecade_path, trainimage_path, message, err_screen,text_to_speech):
    if (l1 == "") and (l2==""):
        t='Please Enter the your Enrollment Number and Name.'
        text_to_speech(t)
        return False
    elif l1=='':
        t='Please Enter the your Enrollment Number.'
        text_to_speech(t)
        return False
    elif l2 == "":
        t='Please Enter the your Name.'
        text_to_speech(t)
        return False
    else:
        cam = None
        path = None
        sample_num = 0
        created_student_folder = False
        try:
            cam = cv2.VideoCapture(0)
            if not cam.isOpened():
                raise RuntimeError("Could not open the camera. Check that it is connected and not in use.")

            detector = cv2.CascadeClassifier(haarcasecade_path)
            if detector.empty():
                raise FileNotFoundError(f"Could not load face detector: {haarcasecade_path}")

            Enrollment = l1.strip()
            Name = l2.strip()
            directory = Enrollment + "_" + Name
            path = os.path.join(trainimage_path, directory)
            os.makedirs(trainimage_path, exist_ok=True)
            os.mkdir(path)
            created_student_folder = True

            message.configure(text="Camera started. Keep one face in view until 50 images are saved.")
            message.update_idletasks()
            next_capture_time = 0.0

            while sample_num < 50:
                ret, img = cam.read()
                if not ret or img is None:
                    raise RuntimeError("Could not read a frame from the camera.")

                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                faces = detector.detectMultiScale(gray, 1.3, 5)
                if len(faces):
                    x, y, w, h = max(faces, key=lambda face: face[2] * face[3])
                    cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                    current_time = time.monotonic()
                    if current_time >= next_capture_time:
                        next_sample_num = sample_num + 1
                        image_path = os.path.join(
                            path, f"{Name}_{Enrollment}_{next_sample_num}.jpg"
                        )
                        if not cv2.imwrite(image_path, gray[y : y + h, x : x + w]):
                            raise OSError(f"Could not save captured face image: {image_path}")
                        sample_num = next_sample_num
                        next_capture_time = current_time + 0.15

                cv2.putText(
                    img,
                    f"Face images: {sample_num}/50  |  Keep one face in view",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )
                cv2.imshow("Frame", img)
                if cv2.waitKey(1) & 0xFF == 27:
                    break

            if sample_num < 50:
                shutil.rmtree(path)
                created_student_folder = False
                if sample_num == 0:
                    message.configure(text="No face detected. Check lighting and camera position, then try again.")
                else:
                    message.configure(
                        text=f"Capture stopped at {sample_num}/50. Click Take Image again and let it finish."
                    )
                return False

            student_details_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "StudentDetails",
                "studentdetails.csv",
            )
            os.makedirs(os.path.dirname(student_details_path), exist_ok=True)
            with open(
                student_details_path,
                "a+",
                newline="",
            ) as csvFile:
                writer = csv.writer(csvFile, delimiter=",")
                writer.writerow([Enrollment, Name])

            created_student_folder = False
            res = f"Saved all {sample_num} face images for ER No: {Enrollment}, Name: {Name}"
            message.configure(text=res)
            text_to_speech(res)
            return True
        except FileExistsError:
            message.configure(text="Student data already exists. Use a different enrollment number.")
            text_to_speech("Student data already exists")
            return False
        except (OSError, RuntimeError, cv2.error) as error:
            if created_student_folder and path and os.path.isdir(path):
                shutil.rmtree(path)
            message.configure(text=f"Image capture failed: {error}")
            text_to_speech("Image capture failed. Check the notification for details.")
            return False
        finally:
            if cam is not None:
                cam.release()
            cv2.destroyAllWindows()
