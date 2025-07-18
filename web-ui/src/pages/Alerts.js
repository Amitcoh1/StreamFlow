import React, { useState } from 'react';
import { Bell, AlertTriangle, Info, Check } from 'lucide-react';
import { format } from 'date-fns';

const Alerts = () => {
  const [alerts, setAlerts] = useState([
    {
      id: '1',
      type: 'error',
      title: 'High Error Rate Detected',
      message: 'Error rate exceeded 5% threshold in the last 5 minutes',
      timestamp: new Date(Date.now() - 1000 * 60 * 10),
      status: 'active'
    },
    {
      id: '2',
      type: 'warning',
      title: 'Database Connection Pool High',
      message: 'Connection pool utilization is at 85%',
      timestamp: new Date(Date.now() - 1000 * 60 * 30),
      status: 'acknowledged'
    },
    {
      id: '3',
      type: 'info',
      title: 'Scheduled Maintenance Complete',
      message: 'Database maintenance completed successfully',
      timestamp: new Date(Date.now() - 1000 * 60 * 60),
      status: 'resolved'
    }
  ]);

  const getAlertIcon = (type) => {
    switch (type) {
      case 'error': return <AlertTriangle className="h-5 w-5 text-red-500" />;
      case 'warning': return <Bell className="h-5 w-5 text-yellow-500" />;
      case 'info': return <Info className="h-5 w-5 text-blue-500" />;
      default: return <Bell className="h-5 w-5 text-gray-500" />;
    }
  };

  const getAlertColor = (type) => {
    switch (type) {
      case 'error': return 'border-l-red-500 bg-red-50';
      case 'warning': return 'border-l-yellow-500 bg-yellow-50';
      case 'info': return 'border-l-blue-500 bg-blue-50';
      default: return 'border-l-gray-500 bg-gray-50';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'bg-red-100 text-red-800';
      case 'acknowledged': return 'bg-yellow-100 text-yellow-800';
      case 'resolved': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const acknowledgeAlert = (id) => {
    setAlerts(alerts.map(alert => 
      alert.id === id ? { ...alert, status: 'acknowledged' } : alert
    ));
  };

  const resolveAlert = (id) => {
    setAlerts(alerts.map(alert => 
      alert.id === id ? { ...alert, status: 'resolved' } : alert
    ));
  };

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Alerts</h1>
        <p className="text-gray-600">Monitor and manage system alerts</p>
      </div>

      <div className="space-y-4">
        {alerts.map((alert) => (
          <div key={alert.id} className={`border-l-4 ${getAlertColor(alert.type)} p-4 rounded-r-lg shadow`}>
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-3">
                {getAlertIcon(alert.type)}
                <div className="flex-1">
                  <h3 className="text-lg font-medium text-gray-900">{alert.title}</h3>
                  <p className="text-gray-600 mt-1">{alert.message}</p>
                  <div className="flex items-center mt-2 space-x-4">
                    <span className="text-sm text-gray-500">
                      {format(alert.timestamp, 'MMM dd, yyyy HH:mm')}
                    </span>
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(alert.status)}`}>
                      {alert.status}
                    </span>
                  </div>
                </div>
              </div>
              {alert.status === 'active' && (
                <div className="flex space-x-2">
                  <button
                    onClick={() => acknowledgeAlert(alert.id)}
                    className="px-3 py-1 bg-yellow-600 text-white text-sm rounded hover:bg-yellow-700"
                  >
                    Acknowledge
                  </button>
                  <button
                    onClick={() => resolveAlert(alert.id)}
                    className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
                  >
                    <Check className="h-4 w-4" />
                  </button>
                </div>
              )}
              {alert.status === 'acknowledged' && (
                <button
                  onClick={() => resolveAlert(alert.id)}
                  className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
                >
                  Resolve
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Alerts; 