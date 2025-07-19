import React, { useState, useEffect, useCallback } from 'react';
import { Search, Download, RefreshCw, ChevronLeft, ChevronRight, Calendar, Eye, EyeOff } from 'lucide-react';
import { format, subDays } from 'date-fns';
import axios from 'axios';

const Events = () => {
  const [events, setEvents] = useState([]);
  const [filteredEvents, setFilteredEvents] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalEvents, setTotalEvents] = useState(0);
  const [eventsPerPage] = useState(50);
  const [dateFilter, setDateFilter] = useState('7days');
  const [expandedRows, setExpandedRows] = useState(new Set());

  // Calculate date range for filtering
  const getDateRange = () => {
    const endDate = new Date();
    let startDate;
    
    switch (dateFilter) {
      case '1day':
        startDate = subDays(endDate, 1);
        break;
      case '3days':
        startDate = subDays(endDate, 3);
        break;
      case '7days':
        startDate = subDays(endDate, 7);
        break;
      case '30days':
        startDate = subDays(endDate, 30);
        break;
      default:
        startDate = subDays(endDate, 7);
    }
    
    return { startDate, endDate };
  };

  // Fetch events from API with pagination and filtering
  const fetchEvents = useCallback(async (page = 1) => {
    try {
      setLoading(true);
      setError(null);
      
      const { startDate, endDate } = getDateRange();
      const offset = (page - 1) * eventsPerPage;
      
      const params = {
        limit: eventsPerPage,
        offset: offset,
        start_time: startDate.toISOString(),
        end_time: endDate.toISOString()
      };
      
      if (selectedType !== 'all') {
        params.event_type = selectedType;
      }
      
      const response = await axios.get('/api/v1/events', { params });
      
      if (Array.isArray(response.data)) {
        // Direct array response from storage service
        const eventsData = response.data;
        const normalizedEvents = eventsData.map(event => ({
          ...event,
          timestamp: new Date(event.timestamp),
          type: event.type.toUpperCase(),
          severity: event.severity.toUpperCase()
        }));
        
        setEvents(normalizedEvents);
        setFilteredEvents(normalizedEvents);
        setTotalEvents(normalizedEvents.length); // Approximate, since we don't have total count
      } else if (response.data.success) {
        // APIResponse format
        const eventsData = response.data.data || [];
        const normalizedEvents = eventsData.map(event => ({
          ...event,
          timestamp: new Date(event.timestamp),
          type: event.type.toUpperCase(),
          severity: event.severity.toUpperCase()
        }));
        
        setEvents(normalizedEvents);
        setFilteredEvents(normalizedEvents);
        setTotalEvents(normalizedEvents.length);
      } else {
        throw new Error('Failed to fetch events');
      }
    } catch (error) {
      console.error('Error fetching events:', error);
      setError('Failed to load events. Please try again.');
      setEvents([]);
      setFilteredEvents([]);
      setTotalEvents(0);
    } finally {
      setLoading(false);
    }
  }, [eventsPerPage, selectedType, dateFilter]);

  useEffect(() => {
    setCurrentPage(1); // Reset to first page when filters change
    fetchEvents(1);
  }, [fetchEvents]);

  useEffect(() => {
    // Auto-refresh every 60 seconds for live data
    const interval = setInterval(() => {
      if (currentPage === 1) { // Only auto-refresh if on first page
        fetchEvents(currentPage);
      }
    }, 60000);
    return () => clearInterval(interval);
  }, [fetchEvents, currentPage]);

  useEffect(() => {
    let filtered = events;

    if (searchTerm) {
      filtered = filtered.filter(event => 
        event.type.toLowerCase().includes(searchTerm.toLowerCase()) ||
        event.source.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (event.user_id && event.user_id.toLowerCase().includes(searchTerm.toLowerCase())) ||
        JSON.stringify(event.data).toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    setFilteredEvents(filtered);
  }, [searchTerm, events]);

  const handlePageChange = (newPage) => {
    setCurrentPage(newPage);
    fetchEvents(newPage);
  };

  const toggleRowExpansion = (eventId) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(eventId)) {
      newExpanded.delete(eventId);
    } else {
      newExpanded.add(eventId);
    }
    setExpandedRows(newExpanded);
  };

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
      case 'WEB_PAGEVIEW': return 'bg-green-100 text-green-800';
      case 'API_REQUEST': return 'bg-purple-100 text-purple-800';
      case 'ERROR': return 'bg-red-100 text-red-800';
      case 'CUSTOM': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const exportEvents = () => {
    const dataStr = JSON.stringify(filteredEvents, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `events_${format(new Date(), 'yyyy-MM-dd_HH-mm-ss')}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const totalPages = Math.ceil(totalEvents / eventsPerPage);

  return (
    <div className="p-6 max-w-full">
      {/* Header */}
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Events</h1>
          <p className="text-gray-600">Real-time event stream and history</p>
        </div>
        <button
          onClick={() => fetchEvents(currentPage)}
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

      {/* Filters */}
      <div className="mb-6 flex flex-col lg:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search events, sources, users, or data..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        
        <div className="flex gap-4">
          <div className="relative">
            <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <select
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
              className="pl-10 pr-8 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 appearance-none bg-white"
            >
              <option value="1day">Last 24 hours</option>
              <option value="3days">Last 3 days</option>
              <option value="7days">Last 7 days</option>
              <option value="30days">Last 30 days</option>
            </select>
          </div>
          
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="all">All Types</option>
            <option value="WEB_CLICK">Web Click</option>
            <option value="WEB_PAGEVIEW">Page View</option>
            <option value="API_REQUEST">API Request</option>
            <option value="ERROR">Error</option>
            <option value="CUSTOM">Custom</option>
          </select>
          
          <button 
            onClick={exportEvents}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center"
          >
            <Download className="h-4 w-4 mr-2" />
            Export
          </button>
        </div>
      </div>

      {/* Results Info */}
      <div className="mb-4 flex justify-between items-center">
        <div className="text-sm text-gray-600">
          Showing {filteredEvents.length} events
          {searchTerm && ` matching "${searchTerm}"`}
        </div>
        <div className="flex items-center text-sm text-gray-500">
          <div className={`h-2 w-2 rounded-full mr-2 ${!error ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`}></div>
          {!error ? 'Live updates' : 'Connection error'}
        </div>
      </div>

      {/* Events Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-4">
                  {/* Expand column */}
                </th>
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
                  Data Preview
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan="6" className="px-6 py-4 text-center text-gray-500">
                    <div className="flex items-center justify-center">
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      Loading events...
                    </div>
                  </td>
                </tr>
              ) : filteredEvents.length === 0 ? (
                <tr>
                  <td colSpan="6" className="px-6 py-4 text-center text-gray-500">
                    No events found for the selected criteria
                  </td>
                </tr>
              ) : (
                filteredEvents.map((event) => (
                  <React.Fragment key={event.id}>
                    <tr className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <button
                          onClick={() => toggleRowExpansion(event.id)}
                          className="text-gray-400 hover:text-gray-600"
                        >
                          {expandedRows.has(event.id) ? (
                            <EyeOff className="h-4 w-4" />
                          ) : (
                            <Eye className="h-4 w-4" />
                          )}
                        </button>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex flex-col">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getTypeColor(event.type)} mb-1`}>
                            {event.type}
                          </span>
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getSeverityColor(event.severity)}`}>
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
                        <div>
                          <div className="font-medium">{format(event.timestamp, 'MMM dd, HH:mm:ss')}</div>
                          <div className="text-xs text-gray-400">{format(event.timestamp, 'yyyy')}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500 max-w-xs">
                        <div className="truncate">
                          {typeof event.data === 'object' 
                            ? Object.keys(event.data).slice(0, 3).map(key => `${key}: ${JSON.stringify(event.data[key])}`).join(', ')
                            : String(event.data)
                          }
                          {Object.keys(event.data || {}).length > 3 && '...'}
                        </div>
                      </td>
                    </tr>
                    {expandedRows.has(event.id) && (
                      <tr>
                        <td colSpan="6" className="px-6 py-4 bg-gray-50">
                          <div className="space-y-4">
                            <div>
                              <h4 className="text-sm font-medium text-gray-900 mb-2">Full Event Data</h4>
                              <pre className="text-xs bg-white p-4 rounded border overflow-auto max-h-64 whitespace-pre-wrap">
                                {JSON.stringify(event.data, null, 2)}
                              </pre>
                            </div>
                            {event.metadata && Object.keys(event.metadata).length > 0 && (
                              <div>
                                <h4 className="text-sm font-medium text-gray-900 mb-2">Metadata</h4>
                                <pre className="text-xs bg-white p-4 rounded border overflow-auto max-h-32 whitespace-pre-wrap">
                                  {JSON.stringify(event.metadata, null, 2)}
                                </pre>
                              </div>
                            )}
                            <div className="flex flex-wrap gap-4 text-xs text-gray-500">
                              <span><strong>ID:</strong> {event.id}</span>
                              {event.correlation_id && <span><strong>Correlation:</strong> {event.correlation_id}</span>}
                              {event.session_id && <span><strong>Session:</strong> {event.session_id}</span>}
                              {event.tags && event.tags.length > 0 && (
                                <span><strong>Tags:</strong> {event.tags.join(', ')}</span>
                              )}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      {totalEvents > eventsPerPage && (
        <div className="mt-6 flex items-center justify-between">
          <div className="text-sm text-gray-700">
            Page {currentPage} of {totalPages} ({totalEvents} total events)
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1 || loading}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              <ChevronLeft className="h-4 w-4 mr-1" />
              Previous
            </button>
            
            {/* Page numbers */}
            <div className="flex space-x-1">
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                let pageNum;
                if (totalPages <= 5) {
                  pageNum = i + 1;
                } else if (currentPage <= 3) {
                  pageNum = i + 1;
                } else if (currentPage >= totalPages - 2) {
                  pageNum = totalPages - 4 + i;
                } else {
                  pageNum = currentPage - 2 + i;
                }
                
                return (
                  <button
                    key={pageNum}
                    onClick={() => handlePageChange(pageNum)}
                    disabled={loading}
                    className={`px-3 py-2 text-sm font-medium rounded-md disabled:opacity-50 ${
                      currentPage === pageNum
                        ? 'bg-blue-600 text-white'
                        : 'border border-gray-300 text-gray-700 bg-white hover:bg-gray-50'
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              })}
            </div>
            
            <button
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages || loading}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              Next
              <ChevronRight className="h-4 w-4 ml-1" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Events; 