import React, { useState } from 'react';
import { Calendar, Package, AlertCircle, CheckCircle, Clock } from 'lucide-react';

const ProcurementList = () => {
  const [filterStatus, setFilterStatus] = useState('all');
  const [sortBy, setSortBy] = useState('date');

  const procurementItems = [
    // VENUE & FACILITIES
    {
      category: 'Venue & Facilities',
      item: 'Venue Rental Contract',
      description: '力合/黄院/清华文创协会 - 2 days + setup time',
      quantity: '1 venue',
      confirmBy: 'Nov 8, 2025',
      owner: 'Tim/Penny',
      status: 'urgent',
      priority: 'Critical',
      notes: 'Three options under consideration - decision meeting Nov 8'
    },
    {
      category: 'Venue & Facilities',
      item: 'Parking Reservations',
      description: '20 parking spots + 1 space for 30-seat bus',
      quantity: '21 spots',
      confirmBy: 'Nov 14, 2025',
      owner: 'TBD',
      status: 'pending',
      priority: 'High',
      notes: 'Provide parking tickets to reception desk'
    },

    // GUEST SERVICES - TRAVEL
    {
      category: 'Guest Services - Travel',
      item: 'International Flight Bookings',
      description: 'Round-trip flights for international speakers',
      quantity: '20+ tickets',
      confirmBy: 'Nov 14, 2025',
      owner: 'Tim',
      status: 'in-progress',
      priority: 'Critical',
      notes: 'Requires passport copies by Nov 30'
    },
    {
      category: 'Guest Services - Travel',
      item: 'Airport Transfer Services',
      description: 'Pick-up and drop-off for international guests',
      quantity: '20+ transfers',
      confirmBy: 'Nov 17, 2025',
      owner: 'Guest Escort Team',
      status: 'pending',
      priority: 'High',
      notes: 'Coordinate with flight schedules'
    },
    {
      category: 'Guest Services - Travel',
      item: 'Shenzhen-Hong Kong Vehicle Permits',
      description: 'Cross-border vehicles for guests (Tony, Ray, Wilson, etc.)',
      quantity: '3-5 vehicles',
      confirmBy: 'Nov 17, 2025',
      owner: 'Guest Escort Team',
      status: 'pending',
      priority: 'High',
      notes: 'Guest escorts: Sophia, Catina, Fanny, Sidne'
    },

    // GUEST SERVICES - ACCOMMODATION
    {
      category: 'Guest Services - Accommodation',
      item: 'Hotel Room Reservations',
      description: 'Negotiate with partner hotel (汉普斯) for room blocks',
      quantity: '20+ rooms, 3-4 nights',
      confirmBy: 'Nov 21, 2025',
      owner: 'Tim',
      status: 'pending',
      priority: 'Critical',
      notes: 'Dec 12-14 minimum, some guests may stay through Dec 18'
    },

    // CATERING
    {
      category: 'Catering & Hospitality',
      item: 'VIP Lunch Service',
      description: '紫荆/喜粤 buffet, includes vegetarian/vegan options',
      quantity: '3 tables',
      confirmBy: 'Nov 8, 2025',
      owner: 'Cloudy',
      status: 'in-progress',
      priority: 'High',
      notes: 'Speaker lunch time: 12:15-14:00; 214 hall lunch: 13:00-14:30'
    },
    {
      category: 'Catering & Hospitality',
      item: 'Staff Meals (3 days)',
      description: 'Meals for 50+ staff members',
      quantity: '150+ meals',
      confirmBy: 'Nov 8, 2025',
      owner: 'Cloudy',
      status: 'in-progress',
      priority: 'Medium',
      notes: 'Dec 12-14 coverage'
    },
    {
      category: 'Catering & Hospitality',
      item: 'VIP Tea/Coffee Service',
      description: 'Premium refreshments for VIP areas',
      quantity: 'TBD',
      confirmBy: 'Nov 8, 2025',
      owner: 'Cloudy',
      status: 'pending',
      priority: 'Medium',
      notes: 'Coordinate with venue facilities'
    },
    {
      category: 'Catering & Hospitality',
      item: 'General Water & Refreshments',
      description: 'Bottled water and light refreshments for 900 attendees',
      quantity: '~1000 units',
      confirmBy: 'Nov 8, 2025',
      owner: 'Cloudy',
      status: 'pending',
      priority: 'Medium',
      notes: 'Daily supply for 2 days'
    },

    // TECHNICAL EQUIPMENT
    {
      category: 'Technical Equipment',
      item: 'AV Equipment Rental',
      description: 'Sound system, microphones, projectors, screens for multiple rooms',
      quantity: '5+ rooms',
      confirmBy: 'Nov 13, 2025',
      owner: 'Adrian',
      status: 'pending',
      priority: 'Critical',
      notes: 'Installation Dec 11-13, testing required'
    },
    {
      category: 'Technical Equipment',
      item: 'Translation Equipment (CPII)',
      description: 'Simultaneous interpretation equipment for 4 classrooms',
      quantity: '4 rooms',
      confirmBy: 'Nov 13, 2025',
      owner: 'Ivan',
      status: 'in-progress',
      priority: 'Critical',
      notes: 'Site survey in progress; confirm language requirements'
    },
    {
      category: 'Technical Equipment',
      item: 'LED Screens',
      description: 'Main stage screens and classroom displays',
      quantity: 'Multiple',
      confirmBy: 'Nov 13, 2025',
      owner: 'Adrian',
      status: 'pending',
      priority: 'High',
      notes: 'Coordinate with venue capabilities'
    },
    {
      category: 'Technical Equipment',
      item: 'Network/Wifi Equipment',
      description: 'Reliable connectivity for 900 attendees',
      quantity: '1 system',
      confirmBy: 'Dec 11, 2025',
      owner: 'IT Team',
      status: 'pending',
      priority: 'High',
      notes: 'Testing during setup period'
    },
    {
      category: 'Technical Equipment',
      item: 'Power Strips & Cabling',
      description: 'Power distribution for equipment and charging stations',
      quantity: 'TBD',
      confirmBy: 'Nov 8, 2025',
      owner: 'Ivan/Cloudy',
      status: 'pending',
      priority: 'Medium',
      notes: 'Contact 中航 for procurement assistance'
    },

    // EVENT MATERIALS - PRINTING
    {
      category: 'Event Materials - Printing',
      item: 'Event Programs',
      description: 'Conference agenda and schedule booklets',
      quantity: '1,000 copies',
      confirmBy: 'Nov 12, 2025',
      owner: 'Yan/Adrian',
      status: 'in-progress',
      priority: 'High',
      notes: 'Design: Nov 6-10; Proofreading: Nov 10; Print: Nov 11-12'
    },
    {
      category: 'Event Materials - Printing',
      item: 'Backdrop & Stage Signage',
      description: 'Large format printing for main stage and classrooms',
      quantity: '5+ areas',
      confirmBy: 'Dec 5, 2025',
      owner: 'Yan/Adrian',
      status: 'pending',
      priority: 'High',
      notes: 'Design ready Nov 28; Print start Dec 5'
    },
    {
      category: 'Event Materials - Printing',
      item: 'Banners & KT Board Materials',
      description: 'Directional signage and promotional materials',
      quantity: 'Multiple',
      confirmBy: 'Dec 5, 2025',
      owner: 'Yan/Adrian',
      status: 'pending',
      priority: 'High',
      notes: 'Large materials printing starts Dec 5'
    },
    {
      category: 'Event Materials - Printing',
      item: 'Name Badges',
      description: 'Printed badges for attendees and staff',
      quantity: '900+',
      confirmBy: 'Dec 11, 2025',
      owner: 'Yan/Adrian',
      status: 'pending',
      priority: 'Medium',
      notes: 'Coordinate with registration data'
    },
    {
      category: 'Event Materials - Printing',
      item: 'Wayfinding Signs',
      description: 'Directional and room identification signs',
      quantity: 'TBD',
      confirmBy: 'Dec 12, 2025',
      owner: 'Yan/Adrian',
      status: 'pending',
      priority: 'Medium',
      notes: 'Install Dec 11-12'
    },

    // EVENT MATERIALS - FABRICATION
    {
      category: 'Event Materials - Fabrication',
      item: 'Stage Construction & Setup',
      description: 'Main stage build including lectern decoration',
      quantity: '1 main stage',
      confirmBy: 'Dec 12, 2025',
      owner: 'Yan/Adrian',
      status: 'pending',
      priority: 'Critical',
      notes: 'Installation Dec 11-12'
    },
    {
      category: 'Event Materials - Fabrication',
      item: 'Classroom Backdrops',
      description: 'Background boards for 6 training classrooms',
      quantity: '6 rooms',
      confirmBy: 'Dec 12, 2025',
      owner: 'Yan/Adrian',
      status: 'pending',
      priority: 'High',
      notes: 'Installation Dec 11-12'
    },
    {
      category: 'Event Materials - Fabrication',
      item: 'Exhibition Booth Setup',
      description: 'Tables, chairs, display materials for 6 exhibitors',
      quantity: '6 booths',
      confirmBy: 'Dec 13, 2025',
      owner: 'Cloudy',
      status: 'pending',
      priority: 'Low',
      notes: 'Scaled down from original plan; exhibitors provide own materials'
    },

    // PROMOTIONAL MATERIALS
    {
      category: 'Promotional Materials',
      item: 'Work Uniforms',
      description: 'Staff uniforms with IAICC branding',
      quantity: '50+ sets',
      confirmBy: 'Nov 11, 2025',
      owner: 'Milne/Cloudy',
      status: 'in-progress',
      priority: 'Medium',
      notes: 'Design approved Oct 29; Manufacturing 10 working days; Ship by Nov 10'
    },
    {
      category: 'Promotional Materials',
      item: 'Guest Gift Packages',
      description: 'Welcome gifts for international speakers',
      quantity: '20+ packages',
      confirmBy: 'Dec 10, 2025',
      owner: 'Cloudy/Penny',
      status: 'pending',
      priority: 'Medium',
      notes: 'Reuse notebooks from warehouse inventory'
    },
    {
      category: 'Promotional Materials',
      item: 'Attendee Gift Bags',
      description: 'Conference materials and branded items',
      quantity: '900 bags',
      confirmBy: 'Dec 10, 2025',
      owner: 'Cloudy',
      status: 'pending',
      priority: 'Low',
      notes: 'CGGE indicates 1000+ gifts available, 50 special'
    },
    {
      category: 'Promotional Materials',
      item: 'Canvas Tote Bags',
      description: 'Custom bags for social media check-in activity',
      quantity: 'TBD',
      confirmBy: 'Nov 13, 2025',
      owner: 'Milne/Cloudy',
      status: 'pending',
      priority: 'Low',
      notes: 'For WeChat Moments promotion'
    },

    // PROFESSIONAL SERVICES
    {
      category: 'Professional Services',
      item: 'Photography Services',
      description: 'Professional event photographers',
      quantity: '1-2 per day',
      confirmBy: 'Nov 14, 2025',
      owner: 'Celia',
      status: 'in-progress',
      priority: 'High',
      notes: 'Dec 15: 1 photographer; Dec 16: 2 photographers; Dec 17: 1 photographer'
    },
    {
      category: 'Professional Services',
      item: 'Videography Services',
      description: 'Session recording and livestream operators',
      quantity: '2-day coverage',
      confirmBy: 'Nov 14, 2025',
      owner: 'Luca/Molly',
      status: 'pending',
      priority: 'High',
      notes: '3 roaming videographers per day'
    },
    {
      category: 'Professional Services',
      item: 'Livestreaming Platform & Services',
      description: 'B站/抖音/快手/腾讯 setup and operation',
      quantity: '2 days',
      confirmBy: 'Nov 12, 2025',
      owner: 'Penny',
      status: 'in-progress',
      priority: 'Medium',
      notes: 'Platform selection in progress; consider 华夏 partnership'
    },
    {
      category: 'Professional Services',
      item: 'Installation & Setup Crew',
      description: 'Professional installers for materials and equipment',
      quantity: 'TBD crew size',
      confirmBy: 'Nov 30, 2025',
      owner: 'Yan/Adrian',
      status: 'pending',
      priority: 'High',
      notes: 'Work period: Dec 11-12'
    },
    {
      category: 'Professional Services',
      item: 'Event Security Services',
      description: 'On-site security personnel',
      quantity: 'TBD',
      confirmBy: 'Dec 10, 2025',
      owner: 'Venue/Operations',
      status: 'pending',
      priority: 'Medium',
      notes: 'Coordinate with venue requirements'
    },
    {
      category: 'Professional Services',
      item: 'Medical/First Aid Services',
      description: 'On-site medical support team',
      quantity: '2-day coverage',
      confirmBy: 'Dec 10, 2025',
      owner: 'Operations',
      status: 'pending',
      priority: 'Medium',
      notes: 'Emergency response capability required'
    },

    // INSURANCE
    {
      category: 'Insurance',
      item: 'Event Liability Insurance',
      description: 'General liability coverage for event',
      quantity: '1 policy',
      confirmBy: 'Nov 30, 2025',
      owner: 'Penny',
      status: 'pending',
      priority: 'High',
      notes: 'Coverage for Dec 12-14'
    },
    {
      category: 'Insurance',
      item: 'Participant Accident Insurance',
      description: 'Coverage for 900 attendees',
      quantity: '900 policies',
      confirmBy: 'Registration close',
      owner: 'Penny',
      status: 'pending',
      priority: 'High',
      notes: 'Contract being drafted; finalize based on registration'
    },

    // DIGITAL SERVICES
    {
      category: 'Digital Services',
      item: 'Registration System Development',
      description: 'UAT for online registration platform',
      quantity: '1 system',
      confirmBy: 'Nov 29, 2025',
      owner: 'Phil/Celia/Ivan',
      status: 'in-progress',
      priority: 'Critical',
      notes: 'QR code system, VIP/general queue management'
    },
    {
      category: 'Digital Services',
      item: 'Ticketing Platform',
      description: 'Ticket sales and distribution system',
      quantity: '1 platform',
      confirmBy: 'Nov 29, 2025',
      owner: 'Yeung/Tom/Jeff',
      status: 'in-progress',
      priority: 'Critical',
      notes: 'VIP (100), General (600), Student (800 target) tickets'
    },
    {
      category: 'Digital Services',
      item: 'E-Certificate Generation System',
      description: 'Automated digital certificate for participants',
      quantity: '900 certificates',
      confirmBy: 'Nov 30, 2025',
      owner: 'Yeung/Tom/Jeff',
      status: 'pending',
      priority: 'Medium',
      notes: 'Distribution by Dec 20'
    },

    // TRANSPORTATION
    {
      category: 'Transportation',
      item: 'Guest Shuttle Bus Service',
      description: 'Hotel to venue transportation',
      quantity: '2-3 buses daily',
      confirmBy: 'Nov 21, 2025',
      owner: 'Tim/Logistics',
      status: 'pending',
      priority: 'High',
      notes: 'Dec 12-15 service period'
    },

    // MISCELLANEOUS
    {
      category: 'Miscellaneous Supplies',
      item: 'Office Supplies & Stationery',
      description: 'Pens, paper, notebooks, etc.',
      quantity: 'Bulk order',
      confirmBy: 'Nov 8, 2025',
      owner: 'Cloudy',
      status: 'pending',
      priority: 'Low',
      notes: 'List compiled Nov 1-5'
    },
    {
      category: 'Miscellaneous Supplies',
      item: 'Materials Storage & Management',
      description: 'Storage for CGGE custom merchandise',
      quantity: 'As needed',
      confirmBy: 'Nov 5, 2025',
      owner: 'Milne/Cloudy',
      status: 'pending',
      priority: 'Low',
      notes: 'Coordinate with CGGE delivery schedule'
    }
  ];

  const getStatusColor = (status) => {
    switch(status) {
      case 'completed': return 'bg-green-100 text-green-800 border-green-300';
      case 'in-progress': return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'pending': return 'bg-gray-100 text-gray-800 border-gray-300';
      case 'urgent': return 'bg-red-100 text-red-800 border-red-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getPriorityColor = (priority) => {
    switch(priority) {
      case 'Critical': return 'bg-purple-600 text-white';
      case 'High': return 'bg-orange-500 text-white';
      case 'Medium': return 'bg-yellow-500 text-white';
      case 'Low': return 'bg-gray-400 text-white';
      default: return 'bg-gray-400 text-white';
    }
  };

  const getStatusIcon = (status) => {
    switch(status) {
      case 'completed': return <CheckCircle size={16} className="text-green-600" />;
      case 'in-progress': return <Clock size={16} className="text-blue-600" />;
      case 'pending': return <Package size={16} className="text-gray-600" />;
      case 'urgent': return <AlertCircle size={16} className="text-red-600" />;
      default: return <Package size={16} className="text-gray-600" />;
    }
  };

  const parseDate = (dateStr) => {
    const months = {
      'Nov': 10, 'Dec': 11
    };
    const parts = dateStr.split(' ');
    if (parts.length >= 2) {
      const month = months[parts[0]];
      const day = parseInt(parts[1].replace(',', ''));
      return new Date(2025, month, day);
    }
    return new Date(2025, 11, 31);
  };

  const filteredItems = procurementItems.filter(item => {
    if (filterStatus === 'all') return true;
    return item.status === filterStatus;
  });

  const sortedItems = [...filteredItems].sort((a, b) => {
    if (sortBy === 'date') {
      return parseDate(a.confirmBy) - parseDate(b.confirmBy);
    } else if (sortBy === 'priority') {
      const priorityOrder = { 'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3 };
      return priorityOrder[a.priority] - priorityOrder[b.priority];
    } else if (sortBy === 'category') {
      return a.category.localeCompare(b.category);
    }
    return 0;
  });

  const categories = [...new Set(procurementItems.map(item => item.category))];
  const statusCounts = {
    all: procurementItems.length,
    urgent: procurementItems.filter(i => i.status === 'urgent').length,
    'in-progress': procurementItems.filter(i => i.status === 'in-progress').length,
    pending: procurementItems.filter(i => i.status === 'pending').length,
    completed: procurementItems.filter(i => i.status === 'completed').length
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-7xl mx-auto">
        <header className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 rounded-lg mb-6">
          <div className="flex items-center gap-3 mb-2">
            <Package size={32} />
            <h1 className="text-3xl font-bold">IAICC 2025 Procurement List</h1>
          </div>
          <p className="text-sm opacity-90">Comprehensive procurement services and confirmation deadlines</p>
          <p className="text-xs opacity-75 mt-2">Last Updated: November 6, 2025</p>
        </header>

        {/* Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg border-2 border-gray-300 shadow">
            <p className="text-sm text-gray-600">Total Items</p>
            <p className="text-3xl font-bold text-gray-900">{statusCounts.all}</p>
          </div>
          <div className="bg-white p-4 rounded-lg border-2 border-red-300 shadow">
            <p className="text-sm text-red-600">Urgent</p>
            <p className="text-3xl font-bold text-red-600">{statusCounts.urgent}</p>
          </div>
          <div className="bg-white p-4 rounded-lg border-2 border-blue-300 shadow">
            <p className="text-sm text-blue-600">In Progress</p>
            <p className="text-3xl font-bold text-blue-600">{statusCounts['in-progress']}</p>
          </div>
          <div className="bg-white p-4 rounded-lg border-2 border-gray-300 shadow">
            <p className="text-sm text-gray-600">Pending</p>
            <p className="text-3xl font-bold text-gray-600">{statusCounts.pending}</p>
          </div>
          <div className="bg-white p-4 rounded-lg border-2 border-green-300 shadow">
            <p className="text-sm text-green-600">Completed</p>
            <p className="text-3xl font-bold text-green-600">{statusCounts.completed}</p>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white p-4 rounded-lg shadow mb-6">
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Filter by Status</label>
              <select 
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="w-full p-2 border rounded-lg"
              >
                <option value="all">All Status ({statusCounts.all})</option>
                <option value="urgent">Urgent ({statusCounts.urgent})</option>
                <option value="in-progress">In Progress ({statusCounts['in-progress']})</option>
                <option value="pending">Pending ({statusCounts.pending})</option>
                <option value="completed">Completed ({statusCounts.completed})</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Sort By</label>
              <select 
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="w-full p-2 border rounded-lg"
              >
                <option value="date">Confirmation Date</option>
                <option value="priority">Priority Level</option>
                <option value="category">Category</option>
              </select>
            </div>
          </div>
        </div>

        {/* Procurement Items */}
        <div className="space-y-4">
          {sortedItems.map((item, idx) => (
            <div key={idx} className="bg-white rounded-lg shadow border-l-4 border-blue-500 overflow-hidden">
              <div className="p-4">
                <div className="flex flex-wrap items-start justify-between gap-3 mb-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      {getStatusIcon(item.status)}
                      <h3 className="font-bold text-lg text-gray-900">{item.item}</h3>
                    </div>
                    <p className="text-sm text-gray-600 mb-1">{item.description}</p>
                    <div className="flex flex-wrap gap-2 mt-2">
                      <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                        {item.category}
                      </span>
                      <span className={`text-xs px-2 py-1 rounded ${getPriorityColor(item.priority)}`}>
                        {item.priority}
                      </span>
                      <span className={`text-xs px-2 py-1 rounded border ${getStatusColor(item.status)}`}>
                        {item.status.replace('-', ' ').toUpperCase()}
                      </span>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className="flex items-center gap-2 text-orange-600 mb-2">
                      <Calendar size={16} />
                      <span className="font-bold">{item.confirmBy}</span>
                    </div>
                    <p className="text-xs text-gray-600">Owner: {item.owner}</p>
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-4 mt-3 pt-3 border-t">
                  <div>
                    <p className="text-xs font-semibold text-gray-600 mb-1">Quantity</p>
                    <p className="text-sm">{item.quantity}</p>
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-gray-600 mb-1">Notes</p>
                    <p className="text-sm text-gray-700">{item.notes}</p>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Category Summary */}
        <div className="mt-8 bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Items by Category</h2>
          <div className="grid md:grid-cols-3 gap-4">
            {categories.map((category, idx) => {
              const count = procurementItems.filter(i => i.category === category).length;
              return (
                <div key={idx} className="border rounded-lg p-3">
                  <p className="font-semibold text-gray-800">{category}</p>
                  <p className="text-2xl font-bold text-blue-600">{count} items</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Critical Deadlines Alert */}
        <div className="mt-6 bg-red-50 border-2 border-red-300 rounded-lg p-6">
          <div className="flex items-start gap-3">
            <AlertCircle size={24} className="text-red-600 flex-shrink-0 mt-1" />
            <div>
              <h3 className="font-bold text-red-900 text-lg mb-2">Critical Upcoming Deadlines</h3>
              <ul className="space-y-2 text-sm">
                {procurementItems
                  .filter(item => item.priority === 'Critical' && item.status !== 'completed')
                  .sort((a, b) => parseDate(a.confirmBy) - parseDate(b.confirmBy))
                  .slice(0, 5)
                  .map((item, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="font-semibold text-red-700">{item.confirmBy}:</span>
                      <span className="text-gray-800">{item.item} ({item.owner})</span>
                    </li>
                  ))}
              </ul>
            </div>
          </div>
        </div>

        {/* Contact Information */}
        <div className="mt-6 bg-blue-50 border border-blue-300 rounded-lg p-4">
          <h3 className="font-semibold text-blue-900 mb-2">Procurement Coordination Contacts</h3>
          <div className="grid md:grid-cols-2 gap-3 text-sm">
            <div>
              <p className="font-semibold">Primary Contact: Tim Tan</p>
              <p>+86 13692149164 (China/WeChat)</p>
              <p>+852 64074182 (HK/WhatsApp)</p>
              <p>tim.tan@cgge.media</p>
            </div>
            <div>
              <p className="font-semibold">Procurement Team Lead: Lily</p>
              <p className="text-gray-700">Team: 李娟娟, 李思颖, 杨德兴</p>
              <p className="mt-2 font-semibold">Logistics Lead: 谭海秀</p>
              <p className="text-gray-700">Team: Yoyo, 徐靖波</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProcurementList;