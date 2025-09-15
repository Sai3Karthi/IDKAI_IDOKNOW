import { useState, useCallback } from 'react';
import { api } from './api';

export function useApiRequest() {
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState(null);

	const run = useCallback(async (method, path, body) => {
		setLoading(true); setError(null);
		try {
			const fn = method.toLowerCase() === 'post' ? api.post : api.get;
			const data = await fn(path, body);
			return data;
		} catch (e) {
			setError(e);
			throw e;
		} finally {
			setLoading(false);
		}
	}, []);

	return { run, loading, error };
}

export default useApiRequest;
