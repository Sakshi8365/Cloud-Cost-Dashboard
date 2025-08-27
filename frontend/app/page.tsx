'use client';
import { useEffect, useState } from "react";
import dayjs from "dayjs";
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid } from "recharts";
import Grid from '@mui/material/Unstable_Grid2';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import PaidIcon from '@mui/icons-material/Paid';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import RefreshIcon from '@mui/icons-material/Refresh';

type CostRecord = {
  timestamp: string;
  service: string;
  cost: number;
};


export default function Home() {
  const [costs, setCosts] = useState<CostRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedService, setSelectedService] = useState<string>("");
  const [startDate, setStartDate] = useState<string>("");
  const [endDate, setEndDate] = useState<string>("");

  useEffect(() => {
    fetch("http://localhost:8000/costs")
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch cost data");
        return res.json();
      })
      .then(setCosts)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);



  // Get unique services for dropdown
  const services = Array.from(new Set(costs.map((row) => row.service)));

  // Filter costs by date range
  const filteredCosts = costs.filter((row) => {
    const date = dayjs(row.timestamp);
    const afterStart = !startDate || date.isAfter(dayjs(startDate).subtract(1, 'day'));
    const beforeEnd = !endDate || date.isBefore(dayjs(endDate).add(1, 'day'));
    return afterStart && beforeEnd;
  });

  // Aggregate cost per timestamp for the selected service (or total if none selected)
  const chartData = Object.values(
    filteredCosts
      .filter((row) => !selectedService || row.service === selectedService)
      .reduce((acc, row) => {
        if (!acc[row.timestamp]) acc[row.timestamp] = { timestamp: row.timestamp, total: 0 };
        acc[row.timestamp].total += row.cost;
        return acc;
      }, {} as Record<string, { timestamp: string; total: number }>)
  ).sort((a, b) => a.timestamp.localeCompare(b.timestamp));

  // Summary metrics
  const totalCost = filteredCosts.reduce((sum, row) => sum + row.cost, 0);
  const serviceTotals = filteredCosts.reduce((acc, row) => {
    acc[row.service] = (acc[row.service] || 0) + row.cost;
    return acc;
  }, {} as Record<string, number>);
  const highestService = Object.entries(serviceTotals).sort((a, b) => b[1] - a[1])[0]?.[0] || "-";
  // For demo, anomaly count is 0 (could be fetched from backend in future)
  const anomalyCount = 0;

  // Handle CSV upload
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('http://localhost:8000/upload-csv', {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error('Failed to upload CSV');
      // Refetch data after upload
      const data = await fetch('http://localhost:8000/costs').then(r => r.json());
      setCosts(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={{ padding: '2rem', fontFamily: 'sans-serif', position: 'relative', minHeight: '100vh' }}>
      <h1>Cloud Cost & Performance Monitoring Dashboard</h1>
      <Box sx={{ flexGrow: 1, mb: 4 }}>
        <Box sx={{ mb: 2 }}>
          <Button
            variant="contained"
            component="label"
            startIcon={<UploadFileIcon />}
            sx={{ mb: 1 }}
          >
            Upload CSV
            <input
              type="file"
              accept=".csv"
              hidden
              onChange={handleFileUpload}
            />
          </Button>
          <Typography variant="body2" color="text.secondary">
            Upload your own cloud cost CSV file (timestamp, service, cost)
          </Typography>
        </Box>
        <Grid container spacing={2}>
          <Grid xs={12} md={4}>
            <Card sx={{ display: 'flex', alignItems: 'center', bgcolor: '#e3f2fd' }}>
              <CardContent sx={{ flex: 1 }}>
                <Typography variant="h6" color="text.secondary" gutterBottom>Total Cost</Typography>
                <Typography variant="h4" color="primary" sx={{ fontWeight: 700 }}>
                  ${totalCost.toFixed(2)}
                </Typography>
              </CardContent>
              <PaidIcon sx={{ fontSize: 48, color: '#1976d2', mr: 2 }} />
            </Card>
          </Grid>
          <Grid xs={12} md={4}>
            <Card sx={{ display: 'flex', alignItems: 'center', bgcolor: '#fff3e0' }}>
              <CardContent sx={{ flex: 1 }}>
                <Typography variant="h6" color="text.secondary" gutterBottom>Highest Service</Typography>
                <Typography variant="h4" color="primary" sx={{ fontWeight: 700 }}>
                  {highestService}
                </Typography>
              </CardContent>
              <TrendingUpIcon sx={{ fontSize: 48, color: '#ff9800', mr: 2 }} />
            </Card>
          </Grid>
          <Grid xs={12} md={4}>
            <Card sx={{ display: 'flex', alignItems: 'center', bgcolor: '#fce4ec' }}>
              <CardContent sx={{ flex: 1 }}>
                <Typography variant="h6" color="text.secondary" gutterBottom>Anomalies</Typography>
                <Typography variant="h4" color="primary" sx={{ fontWeight: 700 }}>
                  {anomalyCount}
                </Typography>
              </CardContent>
              <NotificationsActiveIcon sx={{ fontSize: 48, color: '#d81b60', mr: 2 }} />
            </Card>
          </Grid>
        </Grid>
      </Box>
      {loading && <p>Loading cost data...</p>}
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}
      {!loading && !error && <>
        <section style={{ marginBottom: 32 }}>
          <h2>Cost Over Time</h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16 }}>
            <label>
              Start date:
              <input
                type="date"
                value={startDate}
                onChange={e => setStartDate(e.target.value)}
                style={{ marginLeft: 8 }}
              />
            </label>
            <label>
              End date:
              <input
                type="date"
                value={endDate}
                onChange={e => setEndDate(e.target.value)}
                style={{ marginLeft: 8 }}
              />
            </label>
            <label style={{ marginLeft: 16 }}>
              Filter by service:
              <select
                value={selectedService}
                onChange={(e) => setSelectedService(e.target.value)}
                style={{ marginLeft: 8 }}
              >
                <option value="">All</option>
                {services.map((service) => (
                  <option key={service} value={service}>
                    {service}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData} margin={{ top: 16, right: 32, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" tick={{ fontSize: 10 }} minTickGap={32} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="total" stroke="#8884d8" name={selectedService ? `${selectedService} Cost ($)` : "Total Cost ($)"} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </section>
        <table style={{ borderCollapse: 'collapse', width: '100%' }}>
          <thead>
            <tr>
              <th style={{ border: '1px solid #ccc', padding: '8px' }}>Timestamp</th>
              <th style={{ border: '1px solid #ccc', padding: '8px' }}>Service</th>
              <th style={{ border: '1px solid #ccc', padding: '8px' }}>Cost ($)</th>
            </tr>
          </thead>
          <tbody>
            {filteredCosts.map((row, i) => (
              <tr key={i}>
                <td style={{ border: '1px solid #ccc', padding: '8px' }}>{row.timestamp}</td>
                <td style={{ border: '1px solid #ccc', padding: '8px' }}>{row.service}</td>
                <td style={{ border: '1px solid #ccc', padding: '8px' }}>{row.cost.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </>}
      <Button
        variant="outlined"
        color="secondary"
        onClick={async () => {
          setLoading(true);
          setError(null);
          try {
            const res = await fetch('http://localhost:8000/reset-mock-data', { method: 'POST' });
            if (!res.ok) throw new Error('Failed to reset mock data');
            const data = await fetch('http://localhost:8000/costs').then(r => r.json());
            setCosts(data);
          } catch (err: any) {
            setError(err.message);
          } finally {
            setLoading(false);
          }
        }}
        sx={{ position: 'fixed', left: 24, bottom: 24, minWidth: 0, width: 56, height: 56, borderRadius: '50%', zIndex: 1000, bgcolor: 'background.paper', boxShadow: 3 }}
      >
        <RefreshIcon />
      </Button>
      <Button
        variant="contained"
        color="secondary"
        onClick={async () => {
          setLoading(true);
          setError(null);
          try {
            const res = await fetch('http://localhost:8000/reset-mock-data', { method: 'POST' });
            if (!res.ok) throw new Error('Failed to reset mock data');
            const data = await fetch('http://localhost:8000/costs').then(r => r.json());
            setCosts(data);
          } catch (err: any) {
            setError(err.message);
          } finally {
            setLoading(false);
          }
        }}
        sx={{ position: 'fixed', left: 120, bottom: 24, minWidth: 0, width: 56, height: 56, borderRadius: '50%', zIndex: 2000, bgcolor: 'background.paper', boxShadow: 3, p: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
      >
        <RefreshIcon sx={{ fontSize: 32 }} />
      </Button>
    </main>
  );
}
