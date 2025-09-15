// Basic API helper wrapping fetch with JSON handling & error surface.
const BASE_URL = process.env.REACT_APP_API_BASE || 'http://localhost:8001';

async function request(path, { method = 'GET', headers = {}, body, ...rest } = {}) {
	const opts = {
		method,
		headers: { 'Content-Type': 'application/json', ...headers },
		...rest
	};
	if (body !== undefined) {
		opts.body = typeof body === 'string' ? body : JSON.stringify(body);
	}
	const res = await fetch(BASE_URL + path, opts);
	const text = await res.text();
	let data;
	try { data = text ? JSON.parse(text) : null; } catch { data = text; }
	if (!res.ok) {
		const err = new Error(`API ${method} ${path} ${res.status}`);
		err.status = res.status;
		err.data = data;
		throw err;
	}
	return data;
}

export const api = {
	get: (path, opts) => request(path, { ...opts, method: 'GET' }),
	post: (path, body, opts) => request(path, { ...opts, method: 'POST', body }),
	BASE_URL
};

export default api;
