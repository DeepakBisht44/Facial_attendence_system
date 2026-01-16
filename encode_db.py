import face_recognition
from pathlib import Path
import pickle
import sys

# Paths
ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "dataset"

def encode_db(output_path):
    output_path = Path(output_path).resolve()

    print("\n============================================================")
    print("FAST FACE ENCODING")
    print("============================================================")
    print(f"Dataset: {DATASET}")
    print(f"Output:  {output_path}")
    print("============================================================\n")

    # Check if dataset exists
    if not DATASET.exists():
        print("[ERROR] Dataset folder missing!")
        sys.exit(1)

    known_encodings = []
    known_ids = []
    students = list(DATASET.iterdir())

    print(f"Found {len(students)} students")
    print("Encoding faces (fast mode)...\n")

    # Process each student folder
    for student_dir in students:
        if not student_dir.is_dir():
            continue

        sid = student_dir.name
        imgs = list(student_dir.glob("*.jpg"))

        count = 0
        # Process each image
        for img_path in imgs:
            # Load image
            image = face_recognition.load_image_file(str(img_path))
            
            # Detect faces
            boxes = face_recognition.face_locations(image, model="hog")

            if len(boxes) > 0:
                # Encode face (num_jitters=1 for speed)
                enc = face_recognition.face_encodings(image, boxes, num_jitters=1)
                if len(enc) > 0:
                    known_encodings.append(enc[0])
                    known_ids.append(sid)
                    count += 1

        print(f"Processing {sid}: {len(imgs)} images -> ({count} faces encoded)")

    # Check if any faces were encoded
    if len(known_encodings) == 0:
        print("\n[ERROR] No faces were encoded!")
        sys.exit(1)

    # Save encodings
    data = {"encodings": known_encodings, "ids": known_ids}

    with open(output_path, "wb") as f:
        pickle.dump(data, f)

    print("\n============================================================")
    print("ENCODING COMPLETE")
    print("============================================================")
    print(f"Students encoded: {len(set(known_ids))}")
    print(f"Total face samples: {len(known_encodings)}")
    print(f"Output: {output_path}")
    print("============================================================\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[ERROR] Usage: encode_db.py <output_path>")
        sys.exit(1)
    
    encode_db(sys.argv[1])