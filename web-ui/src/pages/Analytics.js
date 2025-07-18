import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { TrendingUp, BarChart3, PieChart as PieIcon } from 'lucide-react';

const Analytics = () => {
  const eventTrends = [
    { time: '00:00', webClicks: 45, apiRequests: 23, errors: 2 },
    { time: '04:00', webClicks: 32, apiRequests: 18, errors: 1 },
    { time: '08:00', webClicks: 89, apiRequests: 67, errors: 5 },
    { time: '12:00', webClicks: 134, apiRequests: 89, errors: 3 },
    { time: '16:00', webClicks: 98, apiRequests: 72, errors: 4 },
    { time: '20:00', webClicks: 67, apiRequests: 45, errors: 2 },
  ];

  const userDistribution = [
    { name: 'Desktop', value: 65, color: '#3b82f6' },
    { name: 'Mobile', value: 30, color: '#10b981' },
    { name: 'Tablet', value: 5, color: '#f59e0b' },
  ];

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
        <p className="text-gray-600">Advanced data visualization and insights</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Event Trends</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={eventTrends}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Area type="monotone" dataKey="webClicks" stackId="1" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.6} />
              <Area type="monotone" dataKey="apiRequests" stackId="1" stroke="#10b981" fill="#10b981" fillOpacity={0.6} />
              <Area type="monotone" dataKey="errors" stackId="1" stroke="#ef4444" fill="#ef4444" fillOpacity={0.6} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">User Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={userDistribution}
                cx="50%"
                cy="50%"
                outerRadius={80}
                dataKey="value"
                label={({ name, value }) => `${name}: ${value}%`}
              >
                {userDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <TrendingUp className="h-8 w-8 text-blue-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Conversion Rate</p>
              <p className="text-2xl font-bold text-gray-900">3.24%</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <BarChart3 className="h-8 w-8 text-green-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Avg Session</p>
              <p className="text-2xl font-bold text-gray-900">4m 32s</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <PieIcon className="h-8 w-8 text-purple-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Bounce Rate</p>
              <p className="text-2xl font-bold text-gray-900">23.5%</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics; 