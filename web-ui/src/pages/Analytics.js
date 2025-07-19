import React, { useState, useEffect, useCallback } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar } from 'recharts';
import { TrendingUp, BarChart3, PieChart as PieIcon, RefreshCw, Users, Activity, Source } from 'lucide-react';
import axios from 'axios';

const Analytics = () => {
  const [eventTrends, setEventTrends] = useState([]);
  const [userDistribution, setUserDistribution] = useState([]);
  const [topSources, setTopSources] = useState([]);
  const [eventTypes, setEventTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  // Fetch all analytics data
  const fetchAnalyticsData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

             // Fetch analytics from analytics service (port 8002)
       const [trendsRes, distributionRes, sourcesRes, typesRes] = await Promise.all([
         axios.get('http://localhost:8002/api/v1/analytics/event-trends?hours=24&interval_minutes=240'), // 4-hour intervals for 24 hours
         axios.get('http://localhost:8002/api/v1/analytics/user-distribution'),
         axios.get('http://localhost:8002/api/v1/analytics/top-sources?limit=10'),
         axios.get('http://localhost:8002/api/v1/analytics/event-types')
       ]);

      // Process event trends data
      if (trendsRes.data.success) {
        setEventTrends(trendsRes.data.data);
      }

      // Process user distribution data
      if (distributionRes.data.success) {
        setUserDistribution(distributionRes.data.data);
      }

      // Process top sources data
      if (sourcesRes.data.success) {
        setTopSources(sourcesRes.data.data);
      }

      // Process event types data
      if (typesRes.data.success) {
        setEventTypes(typesRes.data.data);
      }

      setLastUpdated(new Date());

    } catch (error) {
      console.error('Error fetching analytics data:', error);
      setError('Failed to load analytics data. Please try again.');
      
      // Set fallback data if API fails
      setEventTrends([
        { time: '00:00', webClicks: 0, apiRequests: 0, errors: 0, custom: 0, total: 0 },
        { time: '04:00', webClicks: 0, apiRequests: 0, errors: 0, custom: 0, total: 0 },
        { time: '08:00', webClicks: 0, apiRequests: 0, errors: 0, custom: 0, total: 0 },
        { time: '12:00', webClicks: 0, apiRequests: 0, errors: 0, custom: 0, total: 0 },
        { time: '16:00', webClicks: 0, apiRequests: 0, errors: 0, custom: 0, total: 0 },
        { time: '20:00', webClicks: 0, apiRequests: 0, errors: 0, custom: 0, total: 0 },
      ]);
      setUserDistribution([
        { name: 'No Data', value: 100, color: '#6b7280', count: 0 }
      ]);
      setTopSources([]);
      setEventTypes([]);

    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAnalyticsData();
    
    // Auto-refresh every 5 minutes
    const interval = setInterval(fetchAnalyticsData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchAnalyticsData]);

  // Calculate summary stats
  const totalEvents = eventTrends.reduce((sum, trend) => sum + trend.total, 0);
  const totalUsers = topSources.reduce((sum, source) => sum + source.unique_users, 0);
  const totalSources = topSources.length;

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-600">
            Real-time data insights and trends
            {lastUpdated && (
              <span className="text-sm text-gray-500 ml-2">
                • Last updated: {lastUpdated.toLocaleTimeString()}
              </span>
            )}
          </p>
        </div>
        <button
          onClick={fetchAnalyticsData}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Error State */}
      {error && (
        <div className="mb-6 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Activity className="h-8 w-8 text-blue-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Events (24h)</p>
              <p className="text-2xl font-bold text-gray-900">{totalEvents.toLocaleString()}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Users className="h-8 w-8 text-green-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Unique Users</p>
              <p className="text-2xl font-bold text-gray-900">{totalUsers.toLocaleString()}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Source className="h-8 w-8 text-purple-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Active Sources</p>
              <p className="text-2xl font-bold text-gray-900">{totalSources}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Event Trends Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center mb-4">
            <TrendingUp className="h-5 w-5 text-gray-700 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">Event Trends (24 Hours)</h3>
          </div>
          {loading ? (
            <div className="h-64 flex items-center justify-center">
              <RefreshCw className="h-6 w-6 animate-spin text-gray-400" />
              <span className="ml-2 text-gray-500">Loading trends...</span>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={eventTrends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip 
                  labelFormatter={(label) => `Time: ${label}`}
                  formatter={(value, name) => [value, name.replace(/([A-Z])/g, ' $1').trim()]}
                />
                <Area type="monotone" dataKey="webClicks" stackId="1" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.6} />
                <Area type="monotone" dataKey="apiRequests" stackId="1" stroke="#10b981" fill="#10b981" fillOpacity={0.6} />
                <Area type="monotone" dataKey="custom" stackId="1" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.6} />
                <Area type="monotone" dataKey="errors" stackId="1" stroke="#ef4444" fill="#ef4444" fillOpacity={0.6} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* User Distribution Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center mb-4">
            <PieIcon className="h-5 w-5 text-gray-700 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">User Distribution</h3>
          </div>
          {loading ? (
            <div className="h-64 flex items-center justify-center">
              <RefreshCw className="h-6 w-6 animate-spin text-gray-400" />
              <span className="ml-2 text-gray-500">Loading distribution...</span>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={userDistribution}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="value"
                  label={({ name, value, count }) => `${name}: ${value}% (${count})`}
                >
                  {userDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value, name, props) => [
                    `${value}% (${props.payload.count} events)`, 
                    name
                  ]}
                />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Secondary Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Sources */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center mb-4">
            <BarChart3 className="h-5 w-5 text-gray-700 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">Top Event Sources</h3>
          </div>
          {loading ? (
            <div className="h-64 flex items-center justify-center">
              <RefreshCw className="h-6 w-6 animate-spin text-gray-400" />
              <span className="ml-2 text-gray-500">Loading sources...</span>
            </div>
          ) : topSources.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={topSources} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="source" type="category" width={80} />
                <Tooltip 
                  formatter={(value, name) => [
                    value, 
                    name === 'event_count' ? 'Events' : 'Unique Users'
                  ]}
                />
                <Bar dataKey="event_count" fill="#3b82f6" />
                <Bar dataKey="unique_users" fill="#10b981" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-500">
              No source data available
            </div>
          )}
        </div>

        {/* Event Types Distribution */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center mb-4">
            <PieIcon className="h-5 w-5 text-gray-700 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">Event Types Distribution</h3>
          </div>
          {loading ? (
            <div className="h-64 flex items-center justify-center">
              <RefreshCw className="h-6 w-6 animate-spin text-gray-400" />
              <span className="ml-2 text-gray-500">Loading event types...</span>
            </div>
          ) : eventTypes.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={eventTypes}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="count"
                  label={({ type, count }) => `${type}: ${count}`}
                >
                  {eventTypes.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value, name, props) => [
                    `${value} events`, 
                    props.payload.type
                  ]}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-500">
              No event type data available
            </div>
          )}
        </div>
      </div>

      {/* Data Summary */}
      {!loading && (
        <div className="mt-8 bg-gray-50 rounded-lg p-6">
          <h4 className="text-lg font-medium text-gray-900 mb-4">Data Summary</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="font-medium text-gray-700">Analysis Period:</span>
              <span className="ml-2 text-gray-600">Last 24 hours</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Data Points:</span>
              <span className="ml-2 text-gray-600">{eventTrends.length} time intervals</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Event Types:</span>
              <span className="ml-2 text-gray-600">{eventTypes.length} different types</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Data Source:</span>
              <span className="ml-2 text-gray-600">Real-time analytics service</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Analytics; 