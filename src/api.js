const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function getApi(path) {
  const response = await fetch(`${baseUrl}${path}`);
  if (!response.ok) throw new Error(`Request failed (${response.status})`);
  return response.json();
}

export const operationsSocketUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/operations';
