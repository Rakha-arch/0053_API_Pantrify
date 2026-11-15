const express = require('express');
const cors = require('cors');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
require('dotenv').config();
const db = require('./config/db');

const app = express();
app.use(cors());
app.use(express.json());

const JWT_SECRET = process.env.JWT_SECRET || 'pantrify-development-secret';
const asyncRoute = (handler) => (req, res, next) => Promise.resolve(handler(req, res, next)).catch(next);
const signToken = (user) => jwt.sign({ id: user.id, email: user.email, role: user.role }, JWT_SECRET, { expiresIn: '7d' });

function auth(req, res, next) {
    const token = req.headers.authorization?.replace(/^Bearer\\s+/i, '');
    if (!token) return res.status(401).json({ status: 'error', message: 'Token diperlukan' });
    try { req.user = jwt.verify(token, JWT_SECRET); next(); }
    catch { return res.status(401).json({ status: 'error', message: 'Token tidak valid atau sudah kedaluwarsa' }); }
}

app.get('/', asyncRoute(async (req, res) => {
    await db.query('SELECT 1');
    res.json({ status: 'success', message: 'Pantrify REST API & MySQL Database berjalan normal!' });
}));
app.get('/api/', asyncRoute(async (req, res) => {
    await db.query('SELECT 1');
    res.json({ status: 'success', message: 'API sehat' });
}));
app.get('/api/health', asyncRoute(async (req, res) => {
    await db.query('SELECT 1');
    res.json({ status: 'success', message: 'API sehat' });
}));

app.post('/api/auth/register', asyncRoute(async (req, res) => {
    const { name, email, password } = req.body;
    if (!name || !email || !password || password.length < 6)
        return res.status(400).json({ status: 'error', message: 'Nama, email, dan password minimal 6 karakter wajib diisi' });
    const [existing] = await db.query('SELECT id FROM users WHERE email = ?', [email]);
    if (existing.length) return res.status(409).json({ status: 'error', message: 'Email sudah terdaftar' });
    const passwordHash = await bcrypt.hash(password, 12);
    const [result] = await db.query('INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)', [name, email, passwordHash, 'user']);
    const user = { id: result.insertId, name, email, role: 'user' };
    res.status(201).json({ status: 'success', data: { user, token: signToken(user) } });
}));

app.post('/api/auth/login', asyncRoute(async (req, res) => {
    const { email, password } = req.body;
    const [rows] = await db.query('SELECT id, name, email, password_hash, role FROM users WHERE email = ?', [email]);
    if (!rows.length || !(await bcrypt.compare(password || '', rows[0].password_hash)))
        return res.status(401).json({ status: 'error', message: 'Email atau password salah' });
    const { password_hash, ...user } = rows[0];
    res.json({ status: 'success', data: { user, token: signToken(user) } });
}));

app.get('/api/auth/me', auth, asyncRoute(async (req, res) => {
    const [rows] = await db.query('SELECT id, name, email, role, created_at FROM users WHERE id = ?', [req.user.id]);
    if (!rows.length) return res.status(404).json({ status: 'error', message: 'User tidak ditemukan' });
    res.json({ status: 'success', data: rows[0] });
}));

app.get('/api/categories', auth, asyncRoute(async (req, res) => {
    const [rows] = await db.query('SELECT id, name, description, created_at FROM categories ORDER BY name');
    res.json({ status: 'success', data: rows });
}));
app.post('/api/categories', auth, asyncRoute(async (req, res) => {
    if (!req.body.name?.trim()) return res.status(400).json({ status: 'error', message: 'Nama kategori wajib diisi' });
    const [result] = await db.query('INSERT INTO categories (name, description) VALUES (?, ?)', [req.body.name.trim(), req.body.description || null]);
    res.status(201).json({ status: 'success', data: { id: result.insertId, name: req.body.name.trim(), description: req.body.description || null } });
}));
app.delete('/api/categories/:id', auth, asyncRoute(async (req, res) => {
    const [result] = await db.query('DELETE FROM categories WHERE id = ?', [req.params.id]);
    if (!result.affectedRows) return res.status(404).json({ status: 'error', message: 'Kategori tidak ditemukan' });
    res.status(204).end();
}));

app.use((err, req, res, next) => { console.error(err); res.status(500).json({ status: 'error', message: 'Terjadi kesalahan server' }); });

if (require.main === module) {
    const PORT = process.env.PORT || 8000;
    app.listen(PORT, () => console.log(`Server Pantrify berjalan di http://localhost:${PORT}`));
}
module.exports = app;
