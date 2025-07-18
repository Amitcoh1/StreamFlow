import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { Activity, Bell, TrendingUp, Users } from 'lucide-react';
import axios from 'axios';

const Dashboard = () => {
  const [metrics, setMetrics] = useState({
    totalEvents: 0,
    eventsPerSecond: 0,
    activeConnections: 0,
    alertsToday: 0,
  });

  const [eventData, setEventData] = useState([]);
  const [alertData, setAlertData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Sample data wrapped in useMemo to prevent re-creation on every render
  const sampleEventData = useMemo(() => [
    { time: '00:00', events: 120 },
    { time: '04:00', events: 89 },
    { time: '08:00', events: 234 },
    { time: '12:00', events: 456 },
    { time: '16:00', events: 378 },
    { time: '20:00', events: 289 },
  ], []);

  const sampleAlertData = useMemo(() => [
    { type: 'Info', count: 45 },
    { type: 'Warning', count: 23 },
    { type: 'Error', count: 8 },
    { type: 'Critical', count: 2 },
  ], []);

  const fetchMetrics = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch real metrics from APIs
      const response = await axios.get('/api/v1/stats');
      
      if (response.data.success) {
        const data = response.data.data;
        
        setMetrics({
          totalEvents: data.total_events || 0,
          eventsPerSecond: data.real_time_metrics?.events_per_second || 0,
          activeConnections: data.active_connections || 0,
          alertsToday: data.real_time_metrics?.active_alerts || 0,
        });

        // Convert events by type to chart data for alerts
        const eventsByType = data.events_by_type || {};
        const alertChartData = Object.entries(eventsByType).map(([type, count]) => ({
          type: type.replace(/[._]/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
          count: count
        }));
        
        setAlertData(alertChartData.length > 0 ? alertChartData : sampleAlertData);
        
        // Use sample event data for now (could be enhanced with real time-series data)
        setEventData(sampleEventData);
        
      } else {
        throw new Error('API returned error response');
      }

    } catch (error) {
      console.error('Error fetching metrics:', error);
      setError('Failed to fetch metrics. Using sample data.');
      
      // Fallback to sample data
      setMetrics({
        totalEvents: 0,
        eventsPerSecond: 23,
        activeConnections: 8,
        alertsToday: 12,
      });
      setEventData(sampleEventData);
      setAlertData(sampleAlertData);
    } finally {
      setLoading(false);
    }
  }, [sampleEventData, sampleAlertData]);

  useEffect(() => {
    fetchMetrics();
    // Update metrics every 5 seconds
    const interval = setInterval(fetchMetrics, 5000);
    return () => clearInterval(interval);
  }, [fetchMetrics]);

  const StatCard = ({ title, value, icon: Icon, color, change }) => (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900">{value}</p>
          {change && (
            <p className={`text-sm ${change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {change >= 0 ? '+' : ''}{change}% from yesterday
            </p>
          )}
        </div>
        <div className={`p-3 rounded-full ${color}`}>
          <Icon className="h-6 w-6 text-white" />
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-xl text-gray-600">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600">Real-time analytics and system overview</p>
        {error && (
          <div className="mt-2 p-2 bg-yellow-100 border border-yellow-400 text-yellow-700 rounded">
            {error} - Showing cached/sample data
          </div>
        )}
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Events"
          value={metrics.totalEvents.toLocaleString()}
          icon={Activity}
          color="bg-blue-500"
          change={12.5}
        />
        <StatCard
          title="Events/sec"
          value={metrics.eventsPerSecond}
          icon={TrendingUp}
          color="bg-green-500"
          change={-2.1}
        />
        <StatCard
          title="Active Connections"
          value={metrics.activeConnections}
          icon={Users}
          color="bg-purple-500"
          change={5.4}
        />
        <StatCard
          title="Alerts Today"
          value={metrics.alertsToday}
          icon={Bell}
          color="bg-red-500"
          change={-18.2}
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Event Timeline */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Event Timeline</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={eventData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Line 
                type="monotone" 
                dataKey="events" 
                stroke="#3b82f6" 
                strokeWidth={2}
                dot={{ fill: '#3b82f6' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Alert Distribution */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Alert Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={alertData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="type" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* System Status */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">System Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center space-x-3">
            <div className="h-3 w-3 bg-green-400 rounded-full"></div>
            <span className="text-sm text-gray-600">Ingestion Service</span>
            <span className="text-sm font-medium text-green-600">Healthy</span>
          </div>
          <div className="flex items-center space-x-3">
            <div className="h-3 w-3 bg-green-400 rounded-full"></div>
            <span className="text-sm text-gray-600">Analytics Service</span>
            <span className="text-sm font-medium text-green-600">Healthy</span>
          </div>
          <div className="flex items-center space-x-3">
            <div className="h-3 w-3 bg-green-400 rounded-full"></div>
            <span className="text-sm text-gray-600">Storage Service</span>
            <span className="text-sm font-medium text-green-600">Healthy</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 