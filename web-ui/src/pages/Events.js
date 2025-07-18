import React, { useState, useEffect, useCallback } from 'react';
import { Search, Download } from 'lucide-react';
import { format } from 'date-fns';

const Events = () => {
  const [events, setEvents] = useState([]);
  const [filteredEvents, setFilteredEvents] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState('all');

  // Sample events data
  const getSampleEvents = useCallback(() => [
    {
      id: '1',
      type: 'WEB_CLICK',
      source: 'web-app',
      timestamp: new Date(Date.now() - 1000 * 60 * 5),
      severity: 'INFO',
      data: { user_id: 'user123', button: 'submit' },
      user_id: 'user123'
    },
    {
      id: '2',
      type: 'API_REQUEST',
      source: 'mobile-app',
      timestamp: new Date(Date.now() - 1000 * 60 * 10),
      severity: 'INFO',
      data: { endpoint: '/api/users', method: 'GET' },
      user_id: 'user456'
    },
    {
      id: '3',
      type: 'ERROR',
      source: 'backend',
      timestamp: new Date(Date.now() - 1000 * 60 * 15),
      severity: 'ERROR',
      data: { error_code: 500, message: 'Database timeout' },
      user_id: null
    }
  ], []);

  useEffect(() => {
    const sampleEvents = getSampleEvents();
    setEvents(sampleEvents);
    setFilteredEvents(sampleEvents);
  }, [getSampleEvents]);

  useEffect(() => {
    let filtered = events;

    if (searchTerm) {
      filtered = filtered.filter(event => 
        event.type.toLowerCase().includes(searchTerm.toLowerCase()) ||
        event.source.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (event.user_id && event.user_id.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    if (selectedType !== 'all') {
      filtered = filtered.filter(event => event.type === selectedType);
    }

    setFilteredEvents(filtered);
  }, [searchTerm, selectedType, events]);

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'ERROR': return 'bg-red-100 text-red-800';
      case 'WARNING': return 'bg-yellow-100 text-yellow-800';
      case 'INFO': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getTypeColor = (type) => {
    switch (type) {
      case 'WEB_CLICK': return 'bg-green-100 text-green-800';
      case 'API_REQUEST': return 'bg-purple-100 text-purple-800';
      case 'ERROR': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Events</h1>
        <p className="text-gray-600">Real-time event stream and history</p>
      </div>

      {/* Filters */}
      <div className="mb-6 flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search events..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <select
          value={selectedType}
          onChange={(e) => setSelectedType(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="all">All Types</option>
          <option value="WEB_CLICK">Web Click</option>
          <option value="API_REQUEST">API Request</option>
          <option value="ERROR">Error</option>
          <option value="METRIC">Metric</option>
        </select>
        <button className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center">
          <Download className="h-4 w-4 mr-2" />
          Export
        </button>
      </div>

      {/* Events Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Event
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Source
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Timestamp
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Data
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredEvents.map((event) => (
                <tr key={event.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getTypeColor(event.type)}`}>
                        {event.type}
                      </span>
                      <span className={`ml-2 inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getSeverityColor(event.severity)}`}>
                        {event.severity}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {event.source}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {event.user_id || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {format(event.timestamp, 'MMM dd, HH:mm:ss')}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    <pre className="text-xs bg-gray-100 p-2 rounded max-w-xs overflow-hidden">
                      {JSON.stringify(event.data, null, 1)}
                    </pre>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Live indicator */}
      <div className="mt-4 flex items-center text-sm text-gray-500">
        <div className="h-2 w-2 bg-green-400 rounded-full animate-pulse mr-2"></div>
        Live updates • {filteredEvents.length} events shown
      </div>
    </div>
  );
};

export default Events; 