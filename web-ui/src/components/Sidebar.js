import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  BarChart3, 
  Activity, 
  Bell, 
  Settings, 
  Waves,
  Home
} from 'lucide-react';

const Sidebar = () => {
  const location = useLocation();

  const navigation = [
    { name: 'Dashboard', href: '/', icon: Home },
    { name: 'Events', href: '/events', icon: Activity },
    { name: 'Analytics', href: '/analytics', icon: BarChart3 },
    { name: 'Alerts', href: '/alerts', icon: Bell },
    { name: 'Settings', href: '/settings', icon: Settings },
  ];

  return (
    <div className="flex h-full w-64 flex-col bg-white shadow-lg">
      {/* Logo */}
      <div className="flex items-center px-6 py-4 border-b border-gray-200">
        <Waves className="h-8 w-8 text-blue-600" />
        <span className="ml-3 text-xl font-bold text-gray-900">StreamFlow</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-4 space-y-2">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href;
          return (
            <Link
              key={item.name}
              to={item.href}
              className={`group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors duration-200 ${
                isActive
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
              }`}
            >
              <item.icon
                className={`mr-3 h-5 w-5 ${
                  isActive ? 'text-blue-500' : 'text-gray-400 group-hover:text-gray-500'
                }`}
              />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* Status */}
      <div className="px-4 py-4 border-t border-gray-200">
        <div className="flex items-center">
          <div className="h-2 w-2 bg-green-400 rounded-full"></div>
          <span className="ml-2 text-sm text-gray-600">All Systems Operational</span>
        </div>
      </div>
    </div>
  );
};

export default Sidebar; 