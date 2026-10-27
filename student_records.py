import csv
import os


def load_student_records(student_details_path, training_images_path):
    """Load enrollment names, recovering missing entries from captured-image folders."""
    records = {}
    if os.path.isfile(student_details_path):
        with open(student_details_path, newline="", encoding="utf-8-sig") as student_file:
            reader = csv.DictReader(student_file)
            if reader.fieldnames and {"Enrollment", "Name"}.issubset(reader.fieldnames):
                for row in reader:
                    enrollment = (row.get("Enrollment") or "").strip()
                    name = (row.get("Name") or "").strip()
                    if enrollment and name and name != "[]":
                        records[enrollment] = name

    recovered = {}
    if os.path.isdir(training_images_path):
        for folder_name in os.listdir(training_images_path):
            enrollment, separator, name = folder_name.partition("_")
            folder_path = os.path.join(training_images_path, folder_name)
            if (
                separator
                and enrollment.isdigit()
                and name.strip()
                and os.path.isdir(folder_path)
                and any(
                    os.path.isfile(os.path.join(folder_path, filename))
                    and filename.lower().endswith((".jpg", ".jpeg", ".png", ".bmp"))
                    for filename in os.listdir(folder_path)
                )
            ):
                recovered.setdefault(enrollment, name.strip())

    missing_records = {
        enrollment: name
        for enrollment, name in recovered.items()
        if enrollment not in records
    }
    if missing_records:
        os.makedirs(os.path.dirname(os.path.abspath(student_details_path)), exist_ok=True)
        write_header = (
            not os.path.isfile(student_details_path)
            or os.path.getsize(student_details_path) == 0
        )
        with open(student_details_path, "a", newline="", encoding="utf-8") as student_file:
            writer = csv.writer(student_file)
            if write_header:
                writer.writerow(["Enrollment", "Name"])
            for enrollment, name in missing_records.items():
                writer.writerow([enrollment, name])
        records.update(missing_records)

    return records
