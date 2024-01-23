import os
import uuid

from werkzeug.utils import secure_filename
from helpers import UPLOAD_FOLDER


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_image_file(img_file):
    MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
    if img_file and allowed_file(img_file.filename):
        ext = os.path.splitext(img_file.filename)[-1].lower()
        file_length = img_file.seek(0, os.SEEK_END)
        img_file.seek(0, os.SEEK_SET)

        filename = str(uuid.uuid4()) + ext
        if 0 < file_length <= MAX_FILE_SIZE_BYTES:
            img_path = os.path.join(UPLOAD_FOLDER, filename)
            img_file.save(img_path)
            return filename
