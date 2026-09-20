const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs').promises;
const fsSync = require('fs');
const cors = require('cors');

const ROOT = __dirname;
const DATA_FILE = path.join(ROOT, 'robotics-state.json');
const UPLOADS_DIR = path.join(ROOT, 'uploads');
const VIDEO_DIR = path.join(UPLOADS_DIR, 'videos');
const CAPTURE_DIR = path.join(UPLOADS_DIR, 'captures');
const HF_MODEL = process.env.HF_IMAGE_MODEL || 'Salesforce/blip-image-captioning-base';

const ensureDirectories = async () => {
  await fs.mkdir(VIDEO_DIR, { recursive: true });
  await fs.mkdir(CAPTURE_DIR, { recursive: true });
};

const loadState = () => {
  try {
    const raw = fsSync.readFileSync(DATA_FILE, 'utf8');
    return JSON.parse(raw);
  } catch (error) {
    return {
      projectDescription: '',
      comments: [],
      video: null,
      codeUploads: []
    };
  }
};

const saveState = async state => {
  await fs.writeFile(DATA_FILE, JSON.stringify(state, null, 2), 'utf8');
};

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    if (file.fieldname === 'video') cb(null, VIDEO_DIR);
    else cb(null, CAPTURE_DIR);
  },
  filename: (req, file, cb) => {
    const timestamp = Date.now();
    const safeName = file.originalname.replace(/[^a-zA-Z0-9._()-]/g, '_');
    cb(null, `${timestamp}-${safeName}`);
  }
});

const upload = multer({ storage });
const app = express();

app.use(cors());
app.use(express.json());
app.use('/uploads', express.static(UPLOADS_DIR));
app.use(express.static(ROOT));

app.get('/', (req, res) => {
  res.sendFile(path.join(ROOT, 'Homepage.html'));
});

app.get('/api/robotics-state', async (req, res) => {
  const state = loadState();
  res.json(state);
});

app.post('/api/analyze-hockey-frame', express.raw({ type: ['image/*', 'application/octet-stream'], limit: '8mb' }), async (req, res) => {
  const token = process.env.HF_TOKEN;
  if (!token) {
    return res.status(503).json({ success: false, message: 'Hugging Face token is not configured' });
  }
  if (!req.body || !req.body.length) {
    return res.status(400).json({ success: false, message: 'No image frame provided' });
  }

  try {
    const response = await fetch(`https://router.huggingface.co/hf-inference/models/${HF_MODEL}`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': req.headers['content-type'] || 'application/octet-stream'
      },
      body: req.body
    });
    const result = await response.json();
    if (!response.ok) {
      const message = typeof result?.error === 'string' ? result.error : 'Hugging Face analysis failed';
      return res.status(response.status).json({ success: false, message });
    }

    const caption = Array.isArray(result) ? result[0]?.generated_text : result?.generated_text;
    return res.json({ success: true, caption: caption || '프레임 설명을 받지 못했습니다.' });
  } catch (error) {
    console.error('Hugging Face request failed:', error.message);
    return res.status(502).json({ success: false, message: 'Hugging Face에 연결할 수 없습니다.' });
  }
});

app.post('/api/project', async (req, res) => {
  const { description } = req.body;
  const state = loadState();
  state.projectDescription = typeof description === 'string' ? description : '';
  await saveState(state);
  res.json({ success: true, projectDescription: state.projectDescription });
});

app.post('/api/comments', async (req, res) => {
  const { type, payload } = req.body;
  const state = loadState();

  if (type === 'comment' && payload) {
    state.comments = state.comments || [];
    state.comments.unshift(payload);
    await saveState(state);
    return res.json({ success: true, comments: state.comments });
  }

  if (type === 'reply' && payload && payload.parentId && payload.reply) {
    const comment = (state.comments || []).find(item => item.id === payload.parentId);
    if (!comment) return res.status(404).json({ success: false, message: 'Parent comment not found' });
    comment.replies = comment.replies || [];
    comment.replies.push(payload.reply);
    await saveState(state);
    return res.json({ success: true, comment });
  }

  res.status(400).json({ success: false, message: 'Invalid request' });
});

app.post('/api/upload-video', upload.single('video'), async (req, res) => {
  if (!req.file) return res.status(400).json({ success: false, message: 'No video uploaded' });

  const state = loadState();
  state.video = {
    name: req.file.originalname,
    filename: req.file.filename,
    size: req.file.size,
    url: `/uploads/videos/${req.file.filename}`,
    uploadedAt: new Date().toISOString()
  };
  await saveState(state);
  res.json({ success: true, video: state.video });
});

app.post('/api/upload-capture', upload.array('captures', 8), async (req, res) => {
  if (!req.files || !req.files.length) return res.status(400).json({ success: false, message: 'No capture files uploaded' });

  const state = loadState();
  state.codeUploads = (state.codeUploads || []).concat(req.files.map(file => ({
    name: file.originalname,
    filename: file.filename,
    url: `/uploads/captures/${file.filename}`,
    uploadedAt: new Date().toISOString()
  })));
  await saveState(state);
  res.json({ success: true, codeUploads: state.codeUploads });
});

const PORT = process.env.PORT || 3000;

ensureDirectories()
  .then(() => {
    app.listen(PORT, () => {
      console.log(`Server started at http://localhost:${PORT}`);
    });
  })
  .catch(error => {
    console.error('Failed to create directories', error);
    process.exit(1);
  });
