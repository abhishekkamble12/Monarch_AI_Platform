import { IncidentRecord, InvestigationResult, SystemHealth } from './types';

declare const process: { env: { NEXT_PUBLIC_API_URL?: string } } | undefined;

const API_BASE = (typeof process !== 'undefined' && process?.env?.NEXT_PUBLIC_API_URL) || 'http://localhost:8000';

export async function fetchHealth(): Promise<SystemHealth> {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) throw new Error('Failed to fetch system health');
  return res.json();
}

export async function runInvestigation(query: string): Promise<InvestigationResult> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) throw new Error('Investigation request failed');
  return res.json();
}

export async function loadDemoIncident(): Promise<{ status: string; incident_id: string; suggested_query: string; files_loaded: string[] }> {
  const res = await fetch(`${API_BASE}/api/demo-incident`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to load demo incident');
  return res.json();
}

export async function fetchIncidents(): Promise<{ incidents: IncidentRecord[]; count: number }> {
  const res = await fetch(`${API_BASE}/api/incidents`);
  if (!res.ok) throw new Error('Failed to fetch incidents list');
  return res.json();
}

export async function generateReport(incidentId: string, result: InvestigationResult): Promise<{ markdown: string }> {
  const res = await fetch(`${API_BASE}/api/report`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ incident_id: incidentId, investigation_result: result }),
  });
  if (!res.ok) throw new Error('Failed to generate report');
  return res.json();
}

export async function uploadEvidence(files: File[]): Promise<any> {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));
  const res = await fetch(`${API_BASE}/api/ingest`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error('Failed to upload evidence files');
  return res.json();
}
