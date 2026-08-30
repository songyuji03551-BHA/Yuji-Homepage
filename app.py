from __future__ import annotations
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import json
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UPLOADS = ROOT / 'uploads'
VIDEO_DIR = UPLOADS / 'videos'
CAPTURE_DIR = UPLOADS / 'captures'
DATA_FILE = ROOT / 'robotics-state.json'

for directory in (VIDEO_DIR, CAPTURE_DIR):
    directory.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, static_folder=str(ROOT), static_url_path='')
CORS(app)

ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov'}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def load_state() -> dict:
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            pass
    return {
        'currentProjectId': None,
        'projects': {}
    }


def save_state(state: dict) -> None:
    DATA_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')


def allowed_file(filename: str, extensions: set[str]) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions


def ensure_project(state: dict, project_id: str) -> dict | None:
    if not project_id:
        return None
    if project_id not in state['projects']:
        state['projects'][project_id] = {
            'id': project_id,
            'title': 'Untitled Project',
            'description': '',
            'comments': [],
            'video': None,
            'codeUploads': []
        }
    return state['projects'][project_id]


def create_project(state: dict, title: str = 'New Project') -> dict:
    project_id = f'project-{int(time.time() * 1000)}'
    state['projects'][project_id] = {
        'id': project_id,
        'title': title,
        'description': '',
        'comments': [],
        'video': None,
        'codeUploads': []
    }
    state['currentProjectId'] = project_id
    return state['projects'][project_id]


@app.route('/')
def index():
    return app.send_static_file('Homepage.html')


@app.route('/api/robotics-state', methods=['GET'])
def robotics_state():
    return jsonify(load_state())


@app.route('/api/project', methods=['POST'])
def update_project():
    state = load_state()
    data = request.get_json(silent=True) or {}
    project_id = data.get('projectId') or state.get('currentProjectId')
    title = data.get('title', 'New Project')
    description = data.get('description', '')

    if not project_id:
        project = create_project(state, title)
    else:
        project = ensure_project(state, project_id)
        if not project:
            project = create_project(state, title)
    project['title'] = title
    project['description'] = description if isinstance(description, str) else ''
    state['currentProjectId'] = project['id']
    save_state(state)
    return jsonify(
        success=True,
        projectId=project['id'],
        projectTitle=project['title'],
        projectDescription=project['description'],
        projects=state['projects']
    )


@app.route('/api/comments', methods=['POST'])
def add_comment():
    state = load_state()
    data = request.get_json(silent=True) or {}
    payload = data.get('payload', {})
    project_id = payload.get('projectId') or data.get('projectId')
    project = ensure_project(state, project_id)
    if not project:
        return jsonify(success=False, message='Project not found'), 404

    comment_type = data.get('type')
    if comment_type == 'comment' and isinstance(payload.get('comment'), dict):
        project.setdefault('comments', [])
        project['comments'].insert(0, payload['comment'])
        save_state(state)
        return jsonify(success=True, comments=project['comments'])

    if comment_type == 'reply' and isinstance(payload.get('reply'), dict):
        parent_id = payload.get('parentId')
        reply = payload.get('reply')
        if not parent_id or not isinstance(reply, dict):
            return jsonify(success=False, message='Invalid payload'), 400
        for comment in project.get('comments', []):
            if comment.get('id') == parent_id:
                comment.setdefault('replies', []).append(reply)
                save_state(state)
                return jsonify(success=True, comment=comment)
        return jsonify(success=False, message='Parent comment not found'), 404

    return jsonify(success=False, message='Invalid request'), 400


@app.route('/api/upload-video', methods=['POST'])
def upload_video():
    state = load_state()
    project_id = request.form.get('projectId') or state.get('currentProjectId')
    project = ensure_project(state, project_id)
    if not project:
        return jsonify(success=False, message='Project not found'), 404

    if 'video' not in request.files:
        return jsonify(success=False, message='No video file'), 400
    video_file = request.files['video']
    if video_file.filename == '' or not allowed_file(video_file.filename, ALLOWED_VIDEO_EXTENSIONS):
        return jsonify(success=False, message='Invalid video format'), 400

    filename = f"{int(time.time() * 1000)}-{secure_filename(video_file.filename)}"
    target_path = VIDEO_DIR / filename
    video_file.save(target_path)

    project['video'] = {
        'name': video_file.filename,
        'filename': filename,
        'size': target_path.stat().st_size,
        'url': f'/uploads/videos/{filename}',
        'uploadedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    }
    state['currentProjectId'] = project_id
    save_state(state)
    return jsonify(success=True, video=project['video'])


@app.route('/api/upload-capture', methods=['POST'])
def upload_capture():
    state = load_state()
    project_id = request.form.get('projectId') or state.get('currentProjectId')
    project = ensure_project(state, project_id)
    if not project:
        return jsonify(success=False, message='Project not found'), 404

    files = request.files.getlist('captures')
    if not files:
        return jsonify(success=False, message='No capture files'), 400

    project.setdefault('codeUploads', [])
    for capture in files:
        if capture.filename == '' or not allowed_file(capture.filename, ALLOWED_IMAGE_EXTENSIONS):
            continue
        filename = f"{int(time.time() * 1000)}-{secure_filename(capture.filename)}"
        target_path = CAPTURE_DIR / filename
        capture.save(target_path)
        project['codeUploads'].append({
            'name': capture.filename,
            'filename': filename,
            'url': f'/uploads/captures/{filename}',
            'uploadedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        })

    state['currentProjectId'] = project_id
    save_state(state)
    return jsonify(success=True, codeUploads=project['codeUploads'])


@app.route('/uploads/<path:filename>')
def uploaded_file(filename: str):
    return send_from_directory(str(UPLOADS), filename)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=3000, debug=True)
