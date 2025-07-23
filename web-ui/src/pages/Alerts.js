import React, { useState, useEffect, useCallback } from 'react';
import { Bell, AlertTriangle, Info, Check, RefreshCw, Clock, CheckCircle, XCircle, Filter } from 'lucide-react';
import { format } from 'date-fns';
import axios from 'axios';

const Alerts = () => {
  const [alerts, setAlerts] = useState([]);
  const [alertStats, setAlertStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('all');
  const [lastUpdated, setLastUpdated] = useState(null);

  // Fetch alerts and statistics
  const fetchAlertsData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch from alerting service (port 8003)
      const [alertsRes, statsRes] = await Promise.all([
        axios.get(`http://localhost:8003/api/v1/alerts?limit=100&hours=24${statusFilter !== 'all' ? `&status=${statusFilter}` : ''}`, {
          headers: { Authorization: 'Bearer demo' }
        }),
        axios.get('http://localhost:8003/api/v1/alerts/stats', {
          headers: { Authorization: 'Bearer demo' }
        })
      ]);

      if (alertsRes.data.success) {
        setAlerts(alertsRes.data.data);
      }

      if (statsRes.data.success) {
        setAlertStats(statsRes.data.data);
      }

      setLastUpdated(new Date());

    } catch (error) {
      console.error('Error fetching alerts data:', error);
      setError('Failed to load alerts. Please try again.');
      
      // Set fallback data
      setAlerts([]);
      setAlertStats({
        status_counts: {},
        level_counts: {},
        hourly_trends: [],
        total_alerts_24h: 0,
        active_alerts: 0,
        resolved_alerts: 0
      });

    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    fetchAlertsData();
    
    // Remove auto-refresh to prevent infinite loops
    // const interval = setInterval(fetchAlertsData, 30 * 1000);
    // return () => clearInterval(interval);
  }, []);

  const acknowledgeAlert = async (alertId) => {
    try {
      await axios.post(`http://localhost:8003/api/v1/alerts/${alertId}/acknowledge`, {}, {
        headers: { Authorization: 'Bearer demo' }
      });
      
      // Update local state
      setAlerts(alerts.map(alert => 
        alert.id === alertId 
          ? { ...alert, status: 'acknowledged', acknowledged_by: 'api_user' }
          : alert
      ));
      
      // Refresh stats
      fetchAlertsData();
      
    } catch (error) {
      console.error('Error acknowledging alert:', error);
      setError('Failed to acknowledge alert');
    }
  };

  const resolveAlert = async (alertId) => {
    try {
      await axios.post(`http://localhost:8003/api/v1/alerts/${alertId}/resolve`, {}, {
        headers: { Authorization: 'Bearer demo' }
      });
      
      // Update local state
      setAlerts(alerts.map(alert => 
        alert.id === alertId 
          ? { ...alert, status: 'resolved', resolved_by: 'api_user' }
          : alert
      ));
      
      // Refresh stats
      fetchAlertsData();
      
    } catch (error) {
      console.error('Error resolving alert:', error);
      setError('Failed to resolve alert');
    }
  };

  const getAlertIcon = (level) => {
    switch (level?.toLowerCase()) {
      case 'critical': return <XCircle className="h-5 w-5 text-red-500" />;
      case 'high': return <AlertTriangle className="h-5 w-5 text-red-500" />;
      case 'medium': return <Bell className="h-5 w-5 text-yellow-500" />;
      case 'low': return <Info className="h-5 w-5 text-blue-500" />;
      default: return <Bell className="h-5 w-5 text-gray-500" />;
    }
  };

  const getAlertColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'critical': return 'border-l-red-500 bg-red-50';
      case 'high': return 'border-l-red-400 bg-red-50';
      case 'medium': return 'border-l-yellow-500 bg-yellow-50';
      case 'low': return 'border-l-blue-500 bg-blue-50';
      default: return 'border-l-gray-500 bg-gray-50';
    }
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'active': return 'bg-red-100 text-red-800';
      case 'acknowledged': return 'bg-yellow-100 text-yellow-800';
      case 'resolved': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'active': return <AlertTriangle className="h-4 w-4" />;
      case 'acknowledged': return <Clock className="h-4 w-4" />;
      case 'resolved': return <CheckCircle className="h-4 w-4" />;
      default: return <Bell className="h-4 w-4" />;
    }
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Alerts</h1>
          <p className="text-gray-600">
            Real-time system alerts and notifications
            {lastUpdated && (
              <span className="text-sm text-gray-500 ml-2">
                • Last updated: {lastUpdated.toLocaleTimeString()}
              </span>
            )}
          </p>
        </div>
        <button
          onClick={fetchAlertsData}
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

      {/* Alert Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <AlertTriangle className="h-8 w-8 text-red-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Active Alerts</p>
              <p className="text-2xl font-bold text-gray-900">{alertStats.active_alerts || 0}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <CheckCircle className="h-8 w-8 text-green-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Resolved (24h)</p>
              <p className="text-2xl font-bold text-gray-900">{alertStats.resolved_alerts || 0}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Bell className="h-8 w-8 text-yellow-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total (24h)</p>
              <p className="text-2xl font-bold text-gray-900">{alertStats.total_alerts_24h || 0}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Info className="h-8 w-8 text-blue-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Critical Alerts</p>
              <p className="text-2xl font-bold text-gray-900">{alertStats.level_counts?.critical || 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="mb-6 flex items-center space-x-4">
        <div className="flex items-center">
          <Filter className="h-4 w-4 text-gray-500 mr-2" />
          <label className="text-sm font-medium text-gray-700 mr-2">Status:</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="resolved">Resolved</option>
          </select>
        </div>
        
        <div className="text-sm text-gray-600">
          Showing {alerts.length} alerts
        </div>
      </div>

      {/* Alerts List */}
      <div className="space-y-4">
        {loading ? (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <RefreshCw className="h-8 w-8 animate-spin text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">Loading alerts...</p>
          </div>
        ) : alerts.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <Bell className="h-8 w-8 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">No alerts found for the selected criteria</p>
          </div>
        ) : (
          alerts.map((alert) => (
            <div
              key={alert.id}
              className={`bg-white rounded-lg shadow border-l-4 p-6 ${getAlertColor(alert.level)}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-4 flex-1">
                  <div className="flex-shrink-0">
                    {getAlertIcon(alert.level)}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900 truncate">
                        {alert.title}
                      </h3>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(alert.status)}`}>
                        {getStatusIcon(alert.status)}
                        <span className="ml-1 capitalize">{alert.status}</span>
                      </span>
                      <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        alert.level?.toLowerCase() === 'critical' ? 'bg-red-100 text-red-800' :
                        alert.level?.toLowerCase() === 'high' ? 'bg-red-100 text-red-800' :
                        alert.level?.toLowerCase() === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-blue-100 text-blue-800'
                      }`}>
                        {alert.level?.toUpperCase()}
                      </span>
                    </div>
                    
                    <p className="text-gray-700 mb-3">{alert.message}</p>
                    
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <span>
                        <strong>Created:</strong> {format(new Date(alert.created_at), 'MMM dd, yyyy HH:mm:ss')}
                      </span>
                      {alert.updated_at && alert.updated_at !== alert.created_at && (
                        <span>
                          <strong>Updated:</strong> {format(new Date(alert.updated_at), 'MMM dd, yyyy HH:mm:ss')}
                        </span>
                      )}
                      {alert.acknowledged_by && (
                        <span>
                          <strong>Acknowledged by:</strong> {alert.acknowledged_by}
                        </span>
                      )}
                      {alert.resolved_by && (
                        <span>
                          <strong>Resolved by:</strong> {alert.resolved_by}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                
                {/* Action Buttons */}
                <div className="flex space-x-2 ml-4">
                  {alert.status?.toLowerCase() === 'active' && (
                    <>
                      <button
                        onClick={() => acknowledgeAlert(alert.id)}
                        className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-md hover:bg-yellow-200 text-sm font-medium flex items-center"
                      >
                        <Clock className="h-4 w-4 mr-1" />
                        Acknowledge
                      </button>
                      <button
                        onClick={() => resolveAlert(alert.id)}
                        className="px-3 py-1 bg-green-100 text-green-800 rounded-md hover:bg-green-200 text-sm font-medium flex items-center"
                      >
                        <Check className="h-4 w-4 mr-1" />
                        Resolve
                      </button>
                    </>
                  )}
                  
                  {alert.status?.toLowerCase() === 'acknowledged' && (
                    <button
                      onClick={() => resolveAlert(alert.id)}
                      className="px-3 py-1 bg-green-100 text-green-800 rounded-md hover:bg-green-200 text-sm font-medium flex items-center"
                    >
                      <Check className="h-4 w-4 mr-1" />
                      Resolve
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Data Summary */}
      {!loading && alertStats.hourly_trends && (
        <div className="mt-8 bg-gray-50 rounded-lg p-6">
          <h4 className="text-lg font-medium text-gray-900 mb-4">Alert Summary</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <span className="font-medium text-gray-700">Status Distribution:</span>
              <div className="ml-2 text-gray-600">
                {Object.entries(alertStats.status_counts || {}).map(([status, count]) => (
                  <div key={status}>{status}: {count}</div>
                ))}
              </div>
            </div>
            <div>
              <span className="font-medium text-gray-700">Level Distribution:</span>
              <div className="ml-2 text-gray-600">
                {Object.entries(alertStats.level_counts || {}).map(([level, count]) => (
                  <div key={level}>{level}: {count}</div>
                ))}
              </div>
            </div>
            <div>
              <span className="font-medium text-gray-700">Data Source:</span>
              <span className="ml-2 text-gray-600">Real-time alerting service</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Alerts; 