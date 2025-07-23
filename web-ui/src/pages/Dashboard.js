import React, { useState, useEffect, useCallback } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import { Activity, Bell, TrendingUp, Users, RefreshCw, AlertTriangle, CheckCircle } from 'lucide-react';
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
  const [eventTrends, setEventTrends] = useState([]);
  const [topSources, setTopSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchMetrics = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch data from multiple services in parallel
      const [dashboardRes, analyticsEventsRes, analyticsSourcesRes, alertsRes] = await Promise.all([
        // Dashboard service stats
        axios.get('http://localhost:8004/api/v1/stats', {
          headers: { Authorization: 'Bearer demo' }
        }),
        // Analytics service for event trends  
        axios.get('http://localhost:8002/api/v1/analytics/event-trends?hours=24&interval_minutes=240', {
          headers: { Authorization: 'Bearer demo' }
        }),
        // Analytics service for top sources
        axios.get('http://localhost:8002/api/v1/analytics/top-sources?limit=5', {
          headers: { Authorization: 'Bearer demo' }
        }),
        // Alerting service for alert stats
        axios.get('http://localhost:8003/api/v1/alerts/stats', {
          headers: { Authorization: 'Bearer demo' }
        })
      ]);

      // Process dashboard stats
      if (dashboardRes.data.success) {
        const data = dashboardRes.data.data;
        
        setMetrics({
          totalEvents: data.total_events || 0,
          eventsPerSecond: data.real_time_metrics?.events_per_second?.value || 0,
          activeConnections: data.real_time_metrics?.active_connections?.value || 0,
          alertsToday: data.real_time_metrics?.active_alerts?.value || 0,
        });

        // Convert events by type to chart data
        const eventsByType = data.events_by_type || {};
        const eventTypeData = Object.entries(eventsByType).map(([type, count]) => ({
          type: type.replace(/[._]/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
          count: count
        }));
        
        setEventData(eventTypeData.length > 0 ? eventTypeData : []);
      }

      // Process analytics event trends
      if (analyticsEventsRes.data.success) {
        const trends = analyticsEventsRes.data.data.map(item => ({
          time: item.time,
          events: item.total,
          webClicks: item.webClicks,
          apiRequests: item.apiRequests,
          errors: item.errors,
          custom: item.custom
        }));
        setEventTrends(trends);
      }

      // Process top sources
      if (analyticsSourcesRes.data.success) {
        setTopSources(analyticsSourcesRes.data.data);
      }

      // Process alert data
      if (alertsRes.data.success) {
        const alertStats = alertsRes.data.data;
        const alertLevelData = Object.entries(alertStats.level_counts || {}).map(([level, count]) => ({
          type: level.charAt(0).toUpperCase() + level.slice(1),
          count: count,
          color: {
            'critical': '#dc2626',
            'high': '#f97316', 
            'medium': '#eab308',
            'low': '#3b82f6'
          }[level] || '#6b7280'
        }));
        
        setAlertData(alertLevelData.length > 0 ? alertLevelData : []);
        
        // Update alerts metric from real data
        setMetrics(prev => ({
          ...prev,
          alertsToday: alertStats.active_alerts || 0
        }));
      }

      setLastUpdated(new Date());

    } catch (error) {
      console.error('Error fetching metrics:', error);
      setError('Failed to fetch some metrics. Some data may be unavailable.');
      
      // Set minimal fallback data
      setEventData([]);
      setAlertData([]);
      setEventTrends([]);
      setTopSources([]);

    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMetrics();
    // Remove auto-refresh to prevent infinite loops
    // const interval = setInterval(fetchMetrics, 30000);
    // return () => clearInterval(interval);
  }, []);

  const StatCard = ({ title, value, icon: Icon, color, change }) => (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center">
        <Icon className={`h-8 w-8 ${color}`} />
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{typeof value === 'number' ? value.toLocaleString() : value}</p>
          {change && (
            <p className={`text-sm ${change.positive ? 'text-green-600' : 'text-red-600'}`}>
              {change.positive ? '+' : ''}{change.value}
            </p>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">
            Real-time system overview and metrics
            {lastUpdated && (
              <span className="text-sm text-gray-500 ml-2">
                • Last updated: {lastUpdated.toLocaleTimeString()}
              </span>
            )}
          </p>
        </div>
        <button
          onClick={fetchMetrics}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Error State */}
      {error && (
        <div className="mb-6 bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="mb-6 bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded flex items-center">
          <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
          Loading dashboard data...
        </div>
      )}

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Events"
          value={metrics.totalEvents}
          icon={Activity}
          color="text-blue-600"
        />
        <StatCard
          title="Events/sec"
          value={metrics.eventsPerSecond.toFixed(1)}
          icon={TrendingUp}
          color="text-green-600"
        />
        <StatCard
          title="Active Connections"
          value={metrics.activeConnections}
          icon={Users}
          color="text-purple-600"
        />
        <StatCard
          title="Active Alerts"
          value={metrics.alertsToday}
          icon={AlertTriangle}
          color="text-red-600"
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Event Trends Over Time */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Event Trends (24h)</h3>
            <TrendingUp className="h-5 w-5 text-gray-400" />
          </div>
          {eventTrends.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={eventTrends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip 
                  labelFormatter={(label) => `Time: ${label}`}
                  formatter={(value, name) => [value, name === 'events' ? 'Total Events' : name]}
                />
                <Line 
                  type="monotone" 
                  dataKey="events" 
                  stroke="#3b82f6" 
                  strokeWidth={2}
                  dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-500">
              <div className="text-center">
                <Activity className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                <p>No event trend data available</p>
              </div>
            </div>
          )}
        </div>

        {/* Alert Distribution */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Alert Distribution</h3>
            <Bell className="h-5 w-5 text-gray-400" />
          </div>
          {alertData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={alertData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="type" />
                <YAxis />
                <Tooltip formatter={(value) => [value, 'Count']} />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {alertData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-500">
              <div className="text-center">
                <CheckCircle className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                <p>No alerts in the last 24 hours</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Secondary Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Event Types Distribution */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Event Types</h3>
            <Activity className="h-5 w-5 text-gray-400" />
          </div>
          {eventData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={eventData}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="count"
                  label={({ type, count }) => `${type}: ${count}`}
                >
                  {eventData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={[
                        '#3b82f6', '#10b981', '#f59e0b', '#ef4444', 
                        '#8b5cf6', '#06b6d4', '#84cc16', '#f97316'
                      ][index % 8]} 
                    />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => [value, 'Events']} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-500">
              <div className="text-center">
                <Activity className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                <p>No event type data available</p>
              </div>
            </div>
          )}
        </div>

        {/* Top Sources */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Top Event Sources</h3>
            <Users className="h-5 w-5 text-gray-400" />
          </div>
          {topSources.length > 0 ? (
            <div className="space-y-4">
              {topSources.map((source, index) => (
                <div key={source.source} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className={`w-3 h-3 rounded-full mr-3 ${
                      ['bg-blue-500', 'bg-green-500', 'bg-yellow-500', 'bg-red-500', 'bg-purple-500'][index % 5]
                    }`}></div>
                    <span className="text-sm font-medium text-gray-900">{source.source}</span>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-bold text-gray-900">{source.event_count}</div>
                    <div className="text-xs text-gray-500">{source.unique_users} users</div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-500">
              <div className="text-center">
                <Users className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                <p>No source data available</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* System Status */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">System Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="flex items-center">
            <div className="w-3 h-3 bg-green-400 rounded-full mr-3"></div>
            <div>
              <div className="text-sm font-medium text-gray-900">Event Processing</div>
              <div className="text-xs text-gray-500">Online • {metrics.eventsPerSecond.toFixed(1)} events/sec</div>
            </div>
          </div>
          <div className="flex items-center">
            <div className={`w-3 h-3 rounded-full mr-3 ${metrics.alertsToday > 0 ? 'bg-yellow-400' : 'bg-green-400'}`}></div>
            <div>
              <div className="text-sm font-medium text-gray-900">Alert System</div>
              <div className="text-xs text-gray-500">
                {metrics.alertsToday > 0 ? `${metrics.alertsToday} active alerts` : 'All clear'}
              </div>
            </div>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-green-400 rounded-full mr-3"></div>
            <div>
              <div className="text-sm font-medium text-gray-900">Data Sources</div>
              <div className="text-xs text-gray-500">{topSources.length} active sources</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 