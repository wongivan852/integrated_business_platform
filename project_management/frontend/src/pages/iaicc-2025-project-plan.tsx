import React, { useState } from 'react';
import { Calendar, DollarSign, AlertTriangle, Users, CheckCircle, Target, FileText, TrendingUp, Clock, Award } from 'lucide-react';
import ExportButton from "../components/ExportButton.tsx";
import { exportGanttToCSV } from '../utils/csvExport';

const IAICCProjectPlan = () => {
  const [activeTab, setActiveTab] = useState('gantt');
  
  const tabs = [
    { id: 'gantt', label: 'Gantt Chart', icon: Calendar },
    { id: 'wbs', label: 'WBS', icon: FileText },
    { id: 'deliverables', label: 'Deliverables', icon: CheckCircle },
    { id: 'milestones', label: 'Milestones', icon: Award },
    { id: 'financial', label: 'Financial', icon: DollarSign },
    { id: 'risks', label: 'Risk Management', icon: AlertTriangle },
    { id: 'quality', label: 'Quality', icon: Target },
    { id: 'resources', label: 'Resources', icon: Users }
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-7xl mx-auto">
        <header className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 rounded-lg mb-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold">IAICC 2025 Project Management Plan</h1>
              <p className="mt-2">International AI and Creativity Conference | Dec 13-14, 2025</p>
            </div>
            <ExportButton
              onClick={() => {
                alert('CSV Export works! See EXPORT_INTEGRATION_GUIDE.md for full integration');
              }}
              label="Test Export"
              variant="success"
            />
          </div>
        </header>

        <div className="flex flex-wrap gap-2 mb-6">
          {tabs.map(tab => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
                  activeTab === tab.id
                    ? 'bg-blue-600 text-white shadow-lg'
                    : 'bg-white text-gray-700 hover:bg-gray-100'
                }`}
              >
                <Icon size={18} />
                <span className="font-medium">{tab.label}</span>
              </button>
            );
          })}
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6">
          {activeTab === 'gantt' && <GanttChart />}
          {activeTab === 'wbs' && <WBS />}
          {activeTab === 'deliverables' && <Deliverables />}
          {activeTab === 'milestones' && <Milestones />}
          {activeTab === 'financial' && <FinancialManagement />}
          {activeTab === 'risks' && <RiskManagement />}
          {activeTab === 'quality' && <QualityManagement />}
          {activeTab === 'resources' && <ResourceEstimation />}
        </div>
      </div>
    </div>
  );
};

const GanttChart = () => {
  const phases = [
    {
      phase: 'Phase 1: Planning & Setup',
      duration: 'Nov 4 - Nov 10',
      tasks: [
        { name: 'Venue Confirmation', start: 'Nov 4', end: 'Nov 8', progress: 60, owner: 'Tim/Penny', critical: true },
        { name: 'Sponsor Outreach', start: 'Nov 4', end: 'Nov 14', progress: 50, owner: 'Penny/Tim', critical: false },
        { name: 'Partner Agreements', start: 'Nov 4', end: 'Nov 14', progress: 40, owner: 'Ivan/Sabrina', critical: false },
        { name: 'School Partnerships', start: 'Nov 1', end: 'Nov 28', progress: 30, owner: 'Sean/Celia', critical: false }
      ]
    },
    {
      phase: 'Phase 2: Speaker & Content',
      duration: 'Nov 10 - Nov 30',
      tasks: [
        { name: 'Speaker Assets Collection', start: 'Nov 10', end: 'Nov 14', progress: 20, owner: 'Tim', critical: true },
        { name: 'Flight Booking', start: 'Nov 4', end: 'Nov 14', progress: 30, owner: 'Tim', critical: true },
        { name: 'PPT Submission', start: 'Nov 14', end: 'Nov 30', progress: 0, owner: 'Sabrina', critical: true },
        { name: 'Content Compliance Review', start: 'Nov 20', end: 'Nov 30', progress: 0, owner: 'Compliance Team', critical: true },
        { name: 'Hotel Reservations', start: 'Nov 17', end: 'Nov 21', progress: 10, owner: 'Tim', critical: false }
      ]
    },
    {
      phase: 'Phase 3: Marketing & PR',
      duration: 'Nov 10 - Dec 10',
      tasks: [
        { name: 'Media Kit Preparation', start: 'Nov 10', end: 'Nov 14', progress: 60, owner: 'Sabrina/Adrian', critical: false },
        { name: 'Press Release 1', start: 'Nov 14', end: 'Nov 14', progress: 0, owner: 'Adrian', critical: false },
        { name: 'Website Updates', start: 'Nov 15', end: 'Nov 29', progress: 0, owner: 'Phil/Celia', critical: false },
        { name: 'Livestream Setup', start: 'Nov 4', end: 'Nov 12', progress: 40, owner: 'Penny', critical: false }
      ]
    },
    {
      phase: 'Phase 4: Operations Setup',
      duration: 'Nov 1 - Dec 11',
      tasks: [
        { name: 'Training Content Development', start: 'Nov 1', end: 'Nov 14', progress: 70, owner: 'Catina', critical: false },
        { name: 'Translation Equipment', start: 'Oct 21', end: 'Nov 13', progress: 50, owner: 'Ivan', critical: false },
        { name: 'Materials Design', start: 'Nov 6', end: 'Nov 10', progress: 80, owner: 'Yan/Adrian', critical: false },
        { name: 'Materials Printing', start: 'Nov 11', end: 'Nov 12', progress: 0, owner: 'Yan/Adrian', critical: false },
        { name: 'Website UAT', start: 'Nov 20', end: 'Nov 29', progress: 0, owner: 'Phil/Celia/Ivan', critical: true }
      ]
    },
    {
      phase: 'Phase 5: Final Preparations',
      duration: 'Dec 1 - Dec 11',
      tasks: [
        { name: 'Equipment Installation', start: 'Dec 11', end: 'Dec 13', progress: 0, owner: 'Adrian/Ivan', critical: true },
        { name: 'Materials Installation', start: 'Dec 11', end: 'Dec 14', progress: 0, owner: 'Yan/Adrian', critical: true },
        { name: 'First Rehearsal', start: 'Dec 5', end: 'Dec 5', progress: 0, owner: 'All', critical: true },
        { name: 'Full Rehearsal', start: 'Dec 12', end: 'Dec 12', progress: 0, owner: 'All', critical: true },
        { name: 'Staff Training', start: 'Dec 10', end: 'Dec 11', progress: 0, owner: 'Jacky', critical: false }
      ]
    },
    {
      phase: 'Phase 6: Event Execution',
      duration: 'Dec 12 - Dec 14',
      tasks: [
        { name: 'Pre-Conference Visits', start: 'Dec 12', end: 'Dec 12', progress: 0, owner: 'Guest Team', critical: false },
        { name: 'Main Event Day 1', start: 'Dec 13', end: 'Dec 13', progress: 0, owner: 'All', critical: true },
        { name: 'Main Event Day 2', start: 'Dec 14', end: 'Dec 14', progress: 0, owner: 'All', critical: true }
      ]
    },
    {
      phase: 'Phase 7: Wrap-up',
      duration: 'Dec 15 - Dec 30',
      tasks: [
        { name: 'Event Documentation', start: 'Dec 15', end: 'Dec 20', progress: 0, owner: 'Celia', critical: false },
        { name: 'Final Payments', start: 'Dec 15', end: 'Dec 25', progress: 0, owner: 'Tim', critical: false },
        { name: 'Post-Event Report', start: 'Dec 20', end: 'Dec 30', progress: 0, owner: 'Tim', critical: false }
      ]
    }
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">Project Gantt Chart</h2>
      
      <div className="bg-blue-50 p-4 rounded-lg mb-4">
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-red-500 rounded"></div>
            <span>Critical Path</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-blue-500 rounded"></div>
            <span>On Track</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-gray-300 rounded"></div>
            <span>Not Started</span>
          </div>
        </div>
      </div>

      {phases.map((phase, idx) => (
        <div key={idx} className="border rounded-lg overflow-hidden">
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-3">
            <h3 className="font-bold">{phase.phase}</h3>
            <p className="text-sm opacity-90">{phase.duration}</p>
          </div>
          
          <div className="divide-y">
            {phase.tasks.map((task, taskIdx) => (
              <div key={taskIdx} className="p-4 hover:bg-gray-50">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className={`font-medium ${task.critical ? 'text-red-600' : 'text-gray-800'}`}>
                        {task.name}
                      </span>
                      {task.critical && (
                        <span className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded">
                          CRITICAL
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      {task.start} → {task.end} | Owner: {task.owner}
                    </p>
                  </div>
                  <span className="text-sm font-semibold text-gray-700">
                    {task.progress}%
                  </span>
                </div>
                
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all ${
                      task.critical ? 'bg-red-500' : 'bg-blue-500'
                    }`}
                    style={{ width: `${task.progress}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

const WBS = () => {
  const wbs = [
    {
      code: '1.0',
      name: 'Venue Management',
      children: [
        { code: '1.1', name: 'Venue Selection & Contract', owner: 'Tim/Penny', deadline: 'Nov 8' },
        { code: '1.2', name: 'Space Mapping & Allocation', owner: 'Tim/Penny', deadline: 'Nov 8' },
        { code: '1.3', name: 'Permits & Licenses', owner: 'Tim/Penny', deadline: 'Nov 8' },
        { code: '1.4', name: 'Parking & Transportation', owner: 'TBD', deadline: 'Nov 14' }
      ]
    },
    {
      code: '2.0',
      name: 'Guest Management',
      children: [
        { code: '2.1', name: 'Guest List & Invitations', owner: '周玉花', deadline: 'Nov 10' },
        { code: '2.2', name: 'Flight Booking', owner: 'Tim', deadline: 'Nov 14' },
        { code: '2.3', name: 'Hotel Accommodation', owner: 'Tim', deadline: 'Nov 21' },
        { code: '2.4', name: 'Transportation Arrangements', owner: 'Guest Escort Team', deadline: 'Nov 17' },
        { code: '2.5', name: 'Meal Arrangements', owner: 'Logistics', deadline: 'Nov 5' },
        { code: '2.6', name: 'Speaker Handbook', owner: 'Tim/Sabrina', deadline: 'Nov 7' },
        { code: '2.7', name: 'Gifts & Welcome Packages', owner: 'Cloudy/Penny', deadline: 'Dec 10' }
      ]
    },
    {
      code: '3.0',
      name: 'Sponsorship & Partnerships',
      children: [
        { code: '3.1', name: 'Sponsor Acquisition', owner: 'Penny/Tim', deadline: 'Nov 14' },
        { code: '3.2', name: 'Partnership Agreements', owner: 'Ivan/Sabrina', deadline: 'Nov 14' },
        { code: '3.3', name: 'School Partnerships (22+)', owner: 'Sean/Celia/Tim/Sabrina', deadline: 'Nov 28' },
        { code: '3.4', name: 'Benefits Fulfillment', owner: 'Multiple', deadline: 'Dec 14' }
      ]
    },
    {
      code: '4.0',
      name: 'Content & Programming',
      children: [
        { code: '4.1', name: 'Speaker Asset Collection', owner: 'Tim', deadline: 'Nov 10' },
        { code: '4.2', name: 'PPT Collection & Review', owner: 'Sabrina', deadline: 'Nov 30' },
        { code: '4.3', name: 'Content Compliance', owner: 'Compliance Team', deadline: 'Nov 30' },
        { code: '4.4', name: 'Training Content (90min)', owner: 'Catina', deadline: 'Nov 14' },
        { code: '4.5', name: 'Host Script Preparation', owner: 'Penny', deadline: 'Nov 14' }
      ]
    },
    {
      code: '5.0',
      name: 'Marketing & Communications',
      children: [
        { code: '5.1', name: 'Media Kit Development', owner: 'Sabrina/Adrian', deadline: 'Nov 14' },
        { code: '5.2', name: 'Press Releases', owner: 'Adrian/Sabrina', deadline: 'Nov 14+' },
        { code: '5.3', name: 'Website Updates', owner: 'Phil/Celia', deadline: 'Nov 29' },
        { code: '5.4', name: 'Social Media Campaign', owner: 'Yan', deadline: 'Ongoing' },
        { code: '5.5', name: 'Livestream Setup', owner: 'Penny', deadline: 'Nov 12' }
      ]
    },
    {
      code: '6.0',
      name: 'Technical Infrastructure',
      children: [
        { code: '6.1', name: 'AV Equipment Setup', owner: 'Adrian', deadline: 'Nov 13' },
        { code: '6.2', name: 'Translation Equipment (4 rooms)', owner: 'Ivan', deadline: 'Nov 13' },
        { code: '6.3', name: 'Registration System', owner: 'Phil/Celia/Ivan', deadline: 'Nov 29' },
        { code: '6.4', name: 'Ticketing System', owner: 'Yeung/Tom/Jeff', deadline: 'Nov 29' },
        { code: '6.5', name: 'Network & Connectivity', owner: 'IT Team', deadline: 'Dec 11' }
      ]
    },
    {
      code: '7.0',
      name: 'Event Materials',
      children: [
        { code: '7.1', name: 'Materials Design', owner: 'Yan/Adrian', deadline: 'Nov 10' },
        { code: '7.2', name: 'Materials Proofreading', owner: 'Timothy/Milne/Cloudy', deadline: 'Nov 10' },
        { code: '7.3', name: 'Materials Printing', owner: 'Yan/Adrian', deadline: 'Nov 12' },
        { code: '7.4', name: 'Materials Installation', owner: 'Yan/Adrian', deadline: 'Dec 14' },
        { code: '7.5', name: 'Signage & Wayfinding', owner: 'Yan/Adrian', deadline: 'Dec 12' }
      ]
    },
    {
      code: '8.0',
      name: 'Logistics & Operations',
      children: [
        { code: '8.1', name: 'Work Uniforms', owner: 'Milne/Cloudy', deadline: 'Nov 11' },
        { code: '8.2', name: 'Catering Arrangements', owner: 'Cloudy', deadline: 'Nov 8' },
        { code: '8.3', name: 'Equipment Procurement', owner: 'Cloudy', deadline: 'Nov 8' },
        { code: '8.4', name: 'Insurance', owner: 'Penny', deadline: 'Registration close' },
        { code: '8.5', name: 'Emergency Planning', owner: 'All', deadline: 'Dec 10' }
      ]
    },
    {
      code: '9.0',
      name: 'Exhibition Area',
      children: [
        { code: '9.1', name: 'Exhibitor Coordination', owner: 'Ivan/徐思奇', deadline: 'Nov 6' },
        { code: '9.2', name: 'Booth Setup', owner: 'Cloudy', deadline: 'Dec 13' }
      ]
    },
    {
      code: '10.0',
      name: 'Training & Rehearsal',
      children: [
        { code: '10.1', name: 'Staff Training', owner: 'Jacky', deadline: 'Dec 11' },
        { code: '10.2', name: 'Equipment Testing', owner: 'Ivan', deadline: 'Nov 13' },
        { code: '10.3', name: 'First Rehearsal', owner: 'All', deadline: 'Dec 5' },
        { code: '10.4', name: 'Full Rehearsal', owner: 'All', deadline: 'Dec 12' }
      ]
    },
    {
      code: '11.0',
      name: 'Event Execution',
      children: [
        { code: '11.1', name: 'Registration Operations', owner: '陈晓敏/Emily', deadline: 'Dec 13-14' },
        { code: '11.2', name: 'Session Management', owner: 'Jacky', deadline: 'Dec 13-14' },
        { code: '11.3', name: 'Training Coordination', owner: 'Catina/Ivan', deadline: 'Dec 13-14' },
        { code: '11.4', name: 'Photography/Video', owner: 'Molly/杨静怡', deadline: 'Dec 13-14' },
        { code: '11.5', name: 'Guest Services', owner: 'Guest Team', deadline: 'Dec 12-14' }
      ]
    },
    {
      code: '12.0',
      name: 'Post-Event',
      children: [
        { code: '12.1', name: 'Certificate Distribution', owner: 'Yeung/Tom/Jeff', deadline: 'Dec 20' },
        { code: '12.2', name: 'Final Payments', owner: 'Tim', deadline: 'Dec 25' },
        { code: '12.3', name: 'Post-Event Report', owner: 'Tim', deadline: 'Dec 30' },
        { code: '12.4', name: 'Asset Archive', owner: 'Celia', deadline: 'Dec 30' }
      ]
    }
  ];

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">Work Breakdown Structure</h2>
      
      <div className="space-y-3">
        {wbs.map((item, idx) => (
          <div key={idx} className="border rounded-lg overflow-hidden">
            <div className="bg-blue-600 text-white p-3">
              <h3 className="font-bold">{item.code} {item.name}</h3>
            </div>
            <div className="divide-y">
              {item.children.map((child, childIdx) => (
                <div key={childIdx} className="p-3 hover:bg-gray-50 flex justify-between items-center">
                  <div className="flex-1">
                    <span className="font-medium text-gray-800">{child.code} {child.name}</span>
                  </div>
                  <div className="text-right text-sm">
                    <div className="text-gray-600">{child.owner}</div>
                    <div className="text-orange-600 font-semibold">{child.deadline}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const Deliverables = () => {
  const deliverables = [
    {
      category: 'Documentation',
      items: [
        { name: 'Speaker Contracts', qty: '20+', deadline: 'Nov 14', owner: 'Tim' },
        { name: 'Speaker Handbook', qty: '1', deadline: 'Nov 7', owner: 'Tim/Sabrina' },
        { name: 'Speaker Assets Package', qty: '1', deadline: 'Nov 10', owner: 'Tim' },
        { name: 'Host Scripts', qty: '1', deadline: 'Nov 14', owner: 'Penny' },
        { name: 'Event Program', qty: '1000', deadline: 'Nov 12', owner: 'Yan/Adrian' },
        { name: 'Press Kit', qty: '1', deadline: 'Nov 14', owner: 'Sabrina/Adrian' }
      ]
    },
    {
      category: 'Digital Assets',
      items: [
        { name: 'Event Website Updates', qty: '1', deadline: 'Nov 29', owner: 'Phil/Celia' },
        { name: 'Registration System', qty: '1', deadline: 'Nov 29', owner: 'Phil/Celia/Ivan' },
        { name: 'Ticketing Platform', qty: '1', deadline: 'Nov 29', owner: 'Yeung/Tom/Jeff' },
        { name: 'Presentation Files (reviewed)', qty: '20+', deadline: 'Nov 30', owner: 'Sabrina' },
        { name: 'E-Certificates', qty: '900', deadline: 'Dec 20', owner: 'Yeung/Tom/Jeff' },
        { name: 'Event Recordings', qty: '2 days', deadline: 'Dec 20', owner: 'Molly' }
      ]
    },
    {
      category: 'Physical Materials',
      items: [
        { name: 'Backdrop/Stage Design', qty: '5 areas', deadline: 'Dec 12', owner: 'Yan/Adrian' },
        { name: 'Signage & Wayfinding', qty: 'Multiple', deadline: 'Dec 12', owner: 'Yan/Adrian' },
        { name: 'Name Badges', qty: '900', deadline: 'Dec 11', owner: 'Yan/Adrian' },
        { name: 'Work Uniforms', qty: '50+', deadline: 'Nov 11', owner: 'Milne/Cloudy' },
        { name: 'Guest Gift Packages', qty: '20+', deadline: 'Dec 10', owner: 'Cloudy/Penny' },
        { name: 'Participant Gifts', qty: '900', deadline: 'Dec 10', owner: 'Cloudy' }
      ]
    },
    {
      category: 'Services',
      items: [
        { name: 'Flight Bookings', qty: '20+', deadline: 'Nov 14', owner: 'Tim' },
        { name: 'Hotel Reservations', qty: '20+ rooms', deadline: 'Nov 21', owner: 'Tim' },
        { name: 'Translation Services', qty: '4 rooms', deadline: 'Nov 13', owner: 'Ivan' },
        { name: 'Catering Services', qty: '3 days', deadline: 'Nov 8', owner: 'Cloudy' },
        { name: 'Photography Services', qty: '3 days', deadline: 'Nov 14', owner: 'Celia' },
        { name: 'Livestream Services', qty: '2 days', deadline: 'Nov 12', owner: 'Penny' }
      ]
    },
    {
      category: 'Reports & Analytics',
      items: [
        { name: 'Registration Report', qty: 'Daily', deadline: 'Ongoing', owner: 'Lily' },
        { name: 'Budget Tracking Report', qty: 'Weekly', deadline: 'Ongoing', owner: 'Tim' },
        { name: 'Post-Event Report', qty: '1', deadline: 'Dec 30', owner: 'Tim' },
        { name: 'Feedback Analysis', qty: '1', deadline: 'Dec 30', owner: 'All' }
      ]
    }
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">Project Deliverables</h2>
      
      {deliverables.map((category, idx) => (
        <div key={idx} className="border rounded-lg overflow-hidden">
          <div className="bg-gradient-to-r from-green-600 to-teal-600 text-white p-3">
            <h3 className="font-bold text-lg">{category.category}</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-100">
                <tr>
                  <th className="p-3 text-left text-sm font-semibold">Deliverable</th>
                  <th className="p-3 text-left text-sm font-semibold">Quantity</th>
                  <th className="p-3 text-left text-sm font-semibold">Deadline</th>
                  <th className="p-3 text-left text-sm font-semibold">Owner</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {category.items.map((item, itemIdx) => (
                  <tr key={itemIdx} className="hover:bg-gray-50">
                    <td className="p-3 text-sm">{item.name}</td>
                    <td className="p-3 text-sm">{item.qty}</td>
                    <td className="p-3 text-sm font-semibold text-orange-600">{item.deadline}</td>
                    <td className="p-3 text-sm text-gray-600">{item.owner}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </div>
  );
};

const Milestones = () => {
  const milestones = [
    {
      date: 'Nov 8, 2025',
      title: 'M1: Venue Confirmed',
      status: 'at-risk',
      deliverables: [
        'Venue contract signed (力合/黄院/清华)',
        'Space allocation finalized',
        'Permits obtained'
      ],
      dependencies: 'Critical for all downstream planning',
      risks: 'Multiple venues under consideration, no final confirmation'
    },
    {
      date: 'Nov 10, 2025',
      title: 'M2: Speaker Assets Complete',
      status: 'on-track',
      deliverables: [
        'All speaker headshots received',
        'Speaker bios collected',
        'Keynote topics confirmed',
        'Speaker assets package ready'
      ],
      dependencies: 'Required for PR launch',
      risks: 'International coordination challenges'
    },
    {
      date: 'Nov 14, 2025',
      title: 'M3: Contracts & PR Launch',
      status: 'upcoming',
      deliverables: [
        'All speaker contracts signed',
        'First press release issued',
        'Flight bookings completed',
        'Sponsorship agreements finalized'
      ],
      dependencies: 'M2 completion required',
      risks: 'Contract negotiation delays'
    },
    {
      date: 'Nov 21, 2025',
      title: 'M4: Travel Arrangements Complete',
      status: 'upcoming',
      deliverables: [
        'All hotel reservations confirmed',
        'Transportation coordinated',
        'Guest itineraries distributed'
      ],
      dependencies: 'Flight bookings from M3',
      risks: 'Hotel availability, pricing'
    },
    {
      date: 'Nov 29, 2025',
      title: 'M5: Website & Registration Live',
      status: 'upcoming',
      deliverables: [
        'Registration system UAT passed',
        'Ticketing platform operational',
        'Website fully updated',
        'QR code system tested'
      ],
      dependencies: 'Technical development on track',
      risks: 'Integration issues, testing delays'
    },
    {
      date: 'Nov 30, 2025',
      title: 'M6: Content Finalized',
      status: 'upcoming',
      deliverables: [
        'All PowerPoint presentations submitted',
        'Content compliance review completed',
        'Passport copies collected',
        'Training materials ready'
      ],
      dependencies: 'Speaker submissions',
      risks: 'Late submissions, compliance issues'
    },
    {
      date: 'Dec 5, 2025',
      title: 'M7: First Rehearsal',
      status: 'upcoming',
      deliverables: [
        'Technical setup verified',
        'Staff roles confirmed',
        'Run-through completed'
      ],
      dependencies: 'Venue access, equipment ready',
      risks: 'Equipment failures, venue issues'
    },
    {
      date: 'Dec 11, 2025',
      title: 'M8: Event Readiness',
      status: 'upcoming',
      deliverables: [
        'All materials installed',
        'Equipment tested and operational',
        'Staff training completed',
        'Emergency procedures briefed'
      ],
      dependencies: 'All prior milestones',
      risks: 'Last-minute issues, vendor delays'
    },
    {
      date: 'Dec 12, 2025',
      title: 'M9: Pre-Conference Complete',
      status: 'upcoming',
      deliverables: [
        'Speakers checked into hotels',
        'Pre-conference visits done',
        'Full rehearsal completed',
        'Go/No-go decision confirmed'
      ],
      dependencies: 'M8 completion',
      risks: 'Travel delays, last-minute cancellations'
    },
    {
      date: 'Dec 14, 2025',
      title: 'M10: Event Execution Complete',
      status: 'upcoming',
      deliverables: [
        'All sessions delivered successfully',
        'Attendee satisfaction recorded',
        'Content captured and recorded',
        'No major incidents'
      ],
      dependencies: 'Entire project chain',
      risks: 'Execution risks, force majeure'
    },
    {
      date: 'Dec 30, 2025',
      title: 'M11: Project Closure',
      status: 'upcoming',
      deliverables: [
        'Final financial reconciliation',
        'Post-event report completed',
        'Lessons learned documented',
        'Archive completed'
      ],
      dependencies: 'Event completion',
      risks: 'Documentation delays, payment delays'
    }
  ];

  const statusColors = {
    'completed': 'bg-green-100 border-green-500',
    'on-track': 'bg-blue-100 border-blue-500',
    'at-risk': 'bg-orange-100 border-orange-500',
    'upcoming': 'bg-gray-100 border-gray-400'
  };

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">Project Milestones</h2>
      
      <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-300 mb-6">
        <p className="font-semibold text-yellow-800">Critical Path Alert</p>
        <p className="text-sm text-yellow-700 mt-1">
          M1 (Venue) is at risk and blocks downstream activities. M2-M6 form the critical path for content preparation.
        </p>
      </div>

      <div className="space-y-4">
        {milestones.map((milestone, idx) => (
          <div key={idx} className={`border-l-4 p-4 rounded-lg ${statusColors[milestone.status]}`}>
            <div className="flex justify-between items-start mb-3">
              <div className="flex-1">
                <div className="flex items-center gap-3">
                  <span className="text-lg font-bold text-gray-800">{milestone.title}</span>
                  <span className="text-xs uppercase px-2 py-1 bg-white rounded border font-semibold">
                    {milestone.status.replace('-', ' ')}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mt-1">{milestone.date}</p>
              </div>
            </div>
            
            <div className="space-y-2 mt-3">
              <div>
                <p className="text-sm font-semibold text-gray-700">Deliverables:</p>
                <ul className="text-sm space-y-1 mt-1">
                  {milestone.deliverables.map((item, itemIdx) => (
                    <li key={itemIdx} className="flex items-start">
                      <span className="mr-2">•</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
              
              <div className="grid md:grid-cols-2 gap-3 mt-3">
                <div className="bg-white bg-opacity-60 p-2 rounded">
                  <p className="text-xs font-semibold text-gray-600">Dependencies</p>
                  <p className="text-sm">{milestone.dependencies}</p>
                </div>
                <div className="bg-white bg-opacity-60 p-2 rounded">
                  <p className="text-xs font-semibold text-gray-600">Key Risks</p>
                  <p className="text-sm">{milestone.risks}</p>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const FinancialManagement = () => {
  const budget = [
    {
      category: 'Venue & Facilities',
      estimated: '¥200,000 - ¥300,000',
      priority: 'Critical',
      items: [
        'Venue rental (2 days + setup)',
        'Equipment rental (AV, translation)',
        'Facility management fees',
        'Parking allocation'
      ]
    },
    {
      category: 'Speaker & Guest Management',
      estimated: '¥300,000 - ¥500,000',
      priority: 'Critical',
      items: [
        'Speaker honorariums (20+ speakers)',
        'International flights',
        'Hotel accommodations (3-4 nights)',
        'Local transportation',
        'Meals and per diems'
      ]
    },
    {
      category: 'Marketing & PR',
      estimated: '¥80,000 - ¥150,000',
      priority: 'High',
      items: [
        'Press release distribution',
        'Media partnerships',
        'Digital advertising',
        'Social media promotion',
        'Content creation'
      ]
    },
    {
      category: 'Event Materials & Production',
      estimated: '¥100,000 - ¥180,000',
      priority: 'High',
      items: [
        'Stage/backdrop design and installation',
        'Signage and wayfinding',
        'Printed materials (programs, badges)',
        'Work uniforms',
        'Photography/videography services'
      ]
    },
    {
      category: 'Catering & Hospitality',
      estimated: '¥60,000 - ¥100,000',
      priority: 'Medium',
      items: [
        'VIP lunches (3 tables)',
        'Speaker/staff meals',
        'Coffee/tea service',
        'Water and refreshments'
      ]
    },
    {
      category: 'Technology & Digital',
      estimated: '¥50,000 - ¥80,000',
      priority: 'High',
      items: [
        'Registration system development',
        'Website updates',
        'Livestreaming setup',
        'Network connectivity',
        'Digital certificates'
      ]
    },
    {
      category: 'Insurance & Contingency',
      estimated: '¥50,000 - ¥100,000',
      priority: 'Medium',
      items: [
        'Event liability insurance',
        'Participant accident insurance',
        'Contingency reserve (10-15%)'
      ]
    },
    {
      category: 'Exhibition & Sponsorship',
      estimated: '¥30,000 - ¥50,000',
      priority: 'Low',
      items: [
        'Exhibition setup (scaled down to 6)',
        'Sponsor fulfillment',
        'Partner materials'
      ]
    }
  ];

  const revenue = [
    { source: 'Ticket Sales - VIP', units: '100', price: '¥500-800', estimated: '¥50,000 - ¥80,000' },
    { source: 'Ticket Sales - General (2-day)', units: '600', price: '¥200-400', estimated: '¥120,000 - ¥240,000' },
    { source: 'Ticket Sales - Students', units: '400', price: '¥99-199', estimated: '¥40,000 - ¥80,000' },
    { source: 'Sponsorships', units: '5-7', price: 'Various', estimated: '¥200,000 - ¥400,000' },
    { source: 'Livestream/Recording', units: '-', price: '¥48', estimated: '¥20,000 - ¥50,000' }
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">Financial Management Plan</h2>
      
      <div className="grid md:grid-cols-3 gap-4 mb-6">
        <div className="bg-blue-100 p-4 rounded-lg border border-blue-300">
          <p className="text-sm text-blue-700 font-semibold">Estimated Budget</p>
          <p className="text-2xl font-bold text-blue-900 mt-1">¥870K - ¥1.46M</p>
        </div>
        <div className="bg-green-100 p-4 rounded-lg border border-green-300">
          <p className="text-sm text-green-700 font-semibold">Projected Revenue</p>
          <p className="text-2xl font-bold text-green-900 mt-1">¥430K - ¥850K</p>
        </div>
        <div className="bg-orange-100 p-4 rounded-lg border border-orange-300">
          <p className="text-sm text-orange-700 font-semibold">Net Position</p>
          <p className="text-2xl font-bold text-orange-900 mt-1">-¥440K to -¥610K</p>
          <p className="text-xs text-orange-700 mt-1">Requires subsidy/additional sponsorship</p>
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-xl font-semibold text-gray-800">Budget Breakdown</h3>
        {budget.map((item, idx) => (
          <div key={idx} className="border rounded-lg overflow-hidden">
            <div className="bg-gray-100 p-3 flex justify-between items-center">
              <div className="flex items-center gap-3">
                <h4 className="font-bold text-gray-800">{item.category}</h4>
                <span className={`text-xs px-2 py-1 rounded ${
                  item.priority === 'Critical' ? 'bg-red-200 text-red-800' :
                  item.priority === 'High' ? 'bg-orange-200 text-orange-800' :
                  'bg-yellow-200 text-yellow-800'
                }`}>
                  {item.priority}
                </span>
              </div>
              <p className="font-bold text-gray-800">{item.estimated}</p>
            </div>
            <div className="p-3">
              <ul className="text-sm space-y-1">
                {item.items.map((subItem, subIdx) => (
                  <li key={subIdx}>• {subItem}</li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6">
        <h3 className="text-xl font-semibold text-gray-800 mb-4">Revenue Sources</h3>
        <div className="overflow-x-auto">
          <table className="w-full border rounded-lg overflow-hidden">
            <thead className="bg-green-600 text-white">
              <tr>
                <th className="p-3 text-left">Revenue Source</th>
                <th className="p-3 text-left">Units</th>
                <th className="p-3 text-left">Price</th>
                <th className="p-3 text-left">Estimated Revenue</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {revenue.map((item, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="p-3">{item.source}</td>
                  <td className="p-3">{item.units}</td>
                  <td className="p-3">{item.price}</td>
                  <td className="p-3 font-semibold">{item.estimated}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="bg-purple-50 p-4 rounded-lg border border-purple-300 mt-6">
        <h4 className="font-semibold text-purple-800 mb-3">Financial Controls</h4>
        <ul className="text-sm space-y-2">
          <li>• <strong>Approval Authority:</strong> Expenditures over ¥10,000 require Tim's approval</li>
          <li>• <strong>Payment Terms:</strong> 50% advance for speakers, balance upon completion</li>
          <li>• <strong>Tracking:</strong> Weekly budget vs. actual reporting to CGGE leadership</li>
          <li>• <strong>Procurement:</strong> Minimum 2 quotes required for purchases over ¥5,000</li>
          <li>• <strong>Contingency:</strong> 10-15% reserve for unforeseen expenses</li>
          <li>• <strong>Currency:</strong> Lock in exchange rates early for international payments</li>
        </ul>
      </div>

      <div className="bg-red-50 p-4 rounded-lg border border-red-300 mt-4">
        <h4 className="font-semibold text-red-800 mb-2">Financial Risks</h4>
        <ul className="text-sm space-y-1">
          <li>• Currency fluctuations affecting international speaker costs</li>
          <li>• Lower than expected ticket sales</li>
          <li>• Sponsor commitment delays or cancellations</li>
          <li>• Venue cost overruns</li>
          <li>• Last-minute speaker cancellations requiring replacement costs</li>
        </ul>
      </div>
    </div>
  );
};

const RiskManagement = () => {
  const risks = [
    {
      id: 'R001',
      risk: 'Venue approval delays - Three venue options still under consideration',
      category: 'Venue',
      probability: 'High',
      impact: 'Critical',
      score: 20,
      mitigation: [
        'Pursue all three venues in parallel (力合, 黄院, 清华)',
        'Schedule decision meetings by Nov 8',
        'Have backup venues identified (保税区)',
        'Daily follow-up with venue contacts',
        'Prepare venue-agnostic materials where possible'
      ],
      contingency: 'If no venue by Nov 10, escalate to executive level and consider event postponement',
      owner: 'Tim/Penny'
    },
    {
      id: 'R002',
      risk: 'International speaker visa rejections or delays',
      category: 'Travel',
      probability: 'Medium',
      impact: 'High',
      score: 15,
      mitigation: [
        'Issue invitation letters immediately',
        'Collect passport copies by Nov 30',
        'Provide comprehensive support documentation',
        'Monitor visa-free policy eligibility',
        'Have backup local speakers identified'
      ],
      contingency: 'Enable virtual presentations for speakers unable to obtain visas',
      owner: 'Tim'
    },
    {
      id: 'R003',
      risk: 'Content compliance review failures',
      category: 'Content',
      probability: 'Medium',
      impact: 'High',
      score: 15,
      mitigation: [
        'Provide clear content guidelines to speakers',
        'Review presentations by Nov 30',
        'Have compliance officer review all materials',
        'Build buffer time for revisions',
        'Pre-screen sensitive topics'
      ],
      contingency: 'Have alternative presentations ready; speakers can pivot to pre-approved topics',
      owner: 'Compliance Team'
    },
    {
      id: 'R004',
      risk: 'Low exhibitor participation (currently only 6 confirmed)',
      category: 'Exhibition',
      probability: 'High',
      impact: 'Medium',
      score: 12,
      mitigation: [
        'Scale down exhibition expectations',
        'Cancel unified booth design (COMPLETED)',
        'Simplify setup for 6 exhibitors',
        'Reallocate exhibition budget to other areas',
        'Focus on quality over quantity'
      ],
      contingency: 'Consider converting exhibition space to additional networking area',
      owner: 'Ivan/徐思奇'
    },
    {
      id: 'R005',
      risk: 'CGGE communication gaps affecting coordination',
      category: 'Coordination',
      probability: 'High',
      impact: 'Medium',
      score: 12,
      mitigation: [
        'Establish daily check-in calls',
        'Create shared tracking dashboard',
        'Designate single point of contact',
        'Document all decisions in writing',
        'Escalate blockers within 24 hours'
      ],
      contingency: 'Executive steering committee to resolve critical coordination issues',
      owner: 'Tim'
    },
    {
      id: 'R006',
      risk: 'Translation equipment technical failures',
      category: 'Technical',
      probability: 'Medium',
      impact: 'High',
      score: 15,
      mitigation: [
        'Complete CPII site survey and testing',
        'Test all equipment during setup (Nov 11-13)',
        'Have backup human interpreters',
        'IT support team on standby',
        'Test during rehearsals'
      ],
      contingency: 'Use human interpreters; distribute handheld translation devices',
      owner: 'Ivan'
    },
    {
      id: 'R007',
      risk: 'Speaker late cancellations or no-shows',
      category: 'Speaker',
      probability: 'Low',
      impact: 'High',
      score: 10,
      mitigation: [
        'Signed contracts with cancellation terms',
        'Regular confirmation communications',
        'Track flight confirmations',
        'Have backup speakers identified',
        'Build flexible agenda'
      ],
      contingency: 'Substitute with backup speakers; extend Q&A sessions; panel discussions',
      owner: '周玉花'
    },
    {
      id: 'R008',
      risk: 'Lower than expected student attendance',
      category: 'Attendance',
      probability: 'Medium',
      impact: 'Medium',
      score: 9,
      mitigation: [
        'Distribute tickets through 22+ schools',
        'Offer attractive pricing (¥19.9-99)',
        'Engage student organizations',
        'Coordinate with professors',
        'Promote through student channels'
      ],
      contingency: 'Open unsold student tickets to general public closer to event',
      owner: 'Sean/Celia/Tim/Sabrina'
    },
    {
      id: 'R009',
      risk: 'Budget overruns in speaker/venue costs',
      category: 'Financial',
      probability: 'Medium',
      impact: 'Medium',
      score: 9,
      mitigation: [
        'Lock in contracts early',
        'Weekly budget tracking',
        'Require approval for overages',
        'Negotiate fixed rates',
        'Maintain 10-15% contingency'
      ],
      contingency: 'Secure additional sponsorship; reduce non-critical expenses',
      owner: 'Tim'
    },
    {
      id: 'R010',
      risk: 'COVID-19 or health emergency during event',
      category: 'Health',
      probability: 'Low',
      impact: 'Very High',
      score: 15,
      mitigation: [
        'Health screening procedures',
        'Medical team on-site',
        'Emergency contacts established',
        'Insurance coverage',
        'Evacuation plan prepared'
      ],
      contingency: 'Hybrid format with virtual attendance; event postponement if required',
      owner: 'All/Medical Team'
    }
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">Risk Management Register</h2>
      
      <div className="bg-blue-50 p-4 rounded-lg mb-6">
        <h3 className="font-semibold text-blue-900 mb-3">Risk Scoring Matrix</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
          <div className="bg-purple-200 p-2 rounded text-center">
            <p className="font-bold">Critical (16-25)</p>
            <p className="text-xs">Immediate action</p>
          </div>
          <div className="bg-red-200 p-2 rounded text-center">
            <p className="font-bold">High (10-15)</p>
            <p className="text-xs">Priority attention</p>
          </div>
          <div className="bg-orange-200 p-2 rounded text-center">
            <p className="font-bold">Medium (5-9)</p>
            <p className="text-xs">Monitor closely</p>
          </div>
          <div className="bg-yellow-200 p-2 rounded text-center">
            <p className="font-bold">Low (1-4)</p>
            <p className="text-xs">Accept risk</p>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {risks.sort((a, b) => b.score - a.score).map((risk, idx) => (
          <div key={idx} className={`border-l-4 rounded-lg p-4 ${
            risk.score >= 16 ? 'bg-purple-50 border-purple-600' :
            risk.score >= 10 ? 'bg-red-50 border-red-500' :
            risk.score >= 5 ? 'bg-orange-50 border-orange-500' :
            'bg-yellow-50 border-yellow-500'
          }`}>
            <div className="flex justify-between items-start mb-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-mono bg-white px-2 py-1 rounded">{risk.id}</span>
                  <span className="text-xs bg-white px-2 py-1 rounded font-semibold">{risk.category}</span>
                  <span className="text-xs bg-white px-2 py-1 rounded">Score: {risk.score}</span>
                </div>
                <h4 className="font-bold text-gray-800 text-base mt-2">{risk.risk}</h4>
              </div>
            </div>
            
            <div className="grid md:grid-cols-2 gap-2 mb-3 text-sm">
              <div className="bg-white bg-opacity-60 p-2 rounded">
                <span className="font-semibold">Probability:</span> {risk.probability}
              </div>
              <div className="bg-white bg-opacity-60 p-2 rounded">
                <span className="font-semibold">Impact:</span> {risk.impact}
              </div>
            </div>

            <div className="space-y-3">
              <div>
                <p className="text-sm font-semibold text-gray-700 mb-1">Mitigation Strategies:</p>
                <ul className="text-sm space-y-1">
                  {risk.mitigation.map((item, mIdx) => (
                    <li key={mIdx} className="flex items-start">
                      <span className="mr-2">→</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
              
              <div className="bg-white bg-opacity-80 p-3 rounded">
                <p className="text-sm font-semibold text-gray-700 mb-1">Contingency Plan:</p>
                <p className="text-sm">{risk.contingency}</p>
              </div>

              <div className="text-sm">
                <span className="font-semibold">Risk Owner:</span> {risk.owner}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-red-100 p-4 rounded-lg border border-red-300 mt-6">
        <h4 className="font-semibold text-red-800 mb-3">Emergency Response Protocol</h4>
        <div className="space-y-2 text-sm">
          <p><strong>Emergency Coordinator:</strong> Tim Tan</p>
          <p><strong>Contact:</strong> +86 13692149164 (China/WeChat) | +852 64074182 (HK/WhatsApp)</p>
          <p><strong>Email:</strong> tim.tan@cgge.media</p>
          <p className="mt-3"><strong>Escalation:</strong> Minor issues → Project Manager → Program Director → Executive Team → Crisis Management</p>
          <p className="mt-2"><strong>Critical Risks Requiring Immediate Escalation:</strong> Venue cancellation, multiple speaker cancellations, major health/safety incidents, severe weather, government restrictions</p>
        </div>
      </div>
    </div>
  );
};

const QualityManagement = () => {
  const qualityStandards = [
    {
      area: 'Speaker Experience',
      standards: [
        { criterion: 'Clear communication', target: 'Weekly updates, 24hr response time', measure: 'Response time tracking' },
        { criterion: 'Travel arrangements', target: '100% confirmed 2 weeks before event', measure: 'Confirmation rate' },
        { criterion: 'Speaker handbook', target: 'Distributed by Nov 7', measure: 'Distribution date' },
        { criterion: 'On-site support', target: 'Dedicated liaison per speaker', measure: 'Speaker satisfaction survey' }
      ]
    },
    {
      area: 'Content Quality',
      standards: [
        { criterion: 'Presentation review', target: '100% reviewed by Nov 30', measure: 'Review completion rate' },
        { criterion: 'Compliance check', target: '0 compliance violations', measure: 'Compliance audit' },
        { criterion: 'Technical quality', target: 'All files tested pre-event', measure: 'Technical test results' },
        { criterion: 'Translation accuracy', target: '>95% accuracy rating', measure: 'Attendee feedback' }
      ]
    },
    {
      area: 'Attendee Experience',
      standards: [
        { criterion: 'Registration process', target: '<3 minutes average', measure: 'System analytics' },
        { criterion: 'Session start times', target: '100% on-time starts', measure: 'Session log' },
        { criterion: 'Audio/visual quality', target: '0 major technical issues', measure: 'Incident log' },
        { criterion: 'Overall satisfaction', target: '>4.0/5.0 rating', measure: 'Post-event survey' }
      ]
    },
    {
      area: 'Event Operations',
      standards: [
        { criterion: 'Setup completion', target: '24 hours before event', measure: 'Setup checklist' },
        { criterion: 'Staff readiness', target: '100% trained by Dec 11', measure: 'Training attendance' },
        { criterion: 'Equipment functionality', target: '0 critical failures', measure: 'Equipment test log' },
        { criterion: 'Safety compliance', target: '100% procedures followed', measure: 'Safety audit' }
      ]
    }
  ];

  const qualityProcesses = [
    {
      phase: 'Planning',
      activities: [
        'Define quality standards and metrics',
        'Establish approval workflows',
        'Create checklists and templates',
        'Assign quality responsibilities'
      ]
    },
    {
      phase: 'Execution',
      activities: [
        'Daily quality checks',
        'Material proofreading (multiple rounds)',
        'Technical testing and rehearsals',
        'Stakeholder review and approval'
      ]
    },
    {
      phase: 'Monitoring',
      activities: [
        'Real-time incident tracking',
        'Session quality monitoring',
        'Attendee feedback collection',
        'Performance metric tracking'
      ]
    },
    {
      phase: 'Review',
      activities: [
        'Post-event surveys',
        'Lessons learned workshop',
        'Quality metrics analysis',
        'Improvement recommendations'
      ]
    }
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">Quality Management Plan</h2>
      
      <div className="bg-green-50 p-4 rounded-lg border border-green-300 mb-6">
        <h3 className="font-semibold text-green-900 mb-2">Quality Objectives</h3>
        <ul className="text-sm space-y-1">
          <li>• Deliver world-class speaker and attendee experience</li>
          <li>• Ensure 100% content compliance with government standards</li>
          <li>• Maintain zero critical technical failures</li>
          <li>• Achieve &gt;4.0/5.0 overall satisfaction rating</li>
          <li>• Complete all deliverables on time and to specification</li>
        </ul>
      </div>

      <div className="space-y-4">
        <h3 className="text-xl font-semibold text-gray-800">Quality Standards by Area</h3>
        {qualityStandards.map((area, idx) => (
          <div key={idx} className="border rounded-lg overflow-hidden">
            <div className="bg-blue-600 text-white p-3">
              <h4 className="font-bold">{area.area}</h4>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-100">
                  <tr>
                    <th className="p-3 text-left text-sm font-semibold">Quality Criterion</th>
                    <th className="p-3 text-left text-sm font-semibold">Target Standard</th>
                    <th className="p-3 text-left text-sm font-semibold">Measurement Method</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {area.standards.map((std, stdIdx) => (
                    <tr key={stdIdx} className="hover:bg-gray-50">
                      <td className="p-3 text-sm font-medium">{std.criterion}</td>
                      <td className="p-3 text-sm">{std.target}</td>
                      <td className="p-3 text-sm text-gray-600">{std.measure}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6">
        <h3 className="text-xl font-semibold text-gray-800 mb-4">Quality Assurance Processes</h3>
        <div className="grid md:grid-cols-2 gap-4">
          {qualityProcesses.map((process, idx) => (
            <div key={idx} className="border rounded-lg p-4">
              <h4 className="font-bold text-blue-700 mb-3">{process.phase} Phase</h4>
              <ul className="text-sm space-y-2">
                {process.activities.map((activity, actIdx) => (
                  <li key={actIdx} className="flex items-start">
                    <CheckCircle size={16} className="mr-2 mt-0.5 text-green-600 flex-shrink-0" />
                    <span>{activity}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-6 space-y-4">
        <h3 className="text-xl font-semibold text-gray-800">Quality Control Checkpoints</h3>
        
        <div className="grid md:grid-cols-3 gap-4">
          <div className="bg-purple-50 p-4 rounded-lg border border-purple-300">
            <h4 className="font-bold text-purple-900 mb-3">Pre-Event Checkpoints</h4>
            <ul className="text-sm space-y-2">
              <li>✓ Speaker contracts signed</li>
              <li>✓ Content reviewed for compliance</li>
              <li>✓ Materials proofread (3 rounds)</li>
              <li>✓ Equipment tested</li>
              <li>✓ Staff trained</li>
              <li>✓ Rehearsals completed</li>
            </ul>
          </div>
          
          <div className="bg-orange-50 p-4 rounded-lg border border-orange-300">
            <h4 className="font-bold text-orange-900 mb-3">During Event Checkpoints</h4>
            <ul className="text-sm space-y-2">
              <li>✓ Session start time adherence</li>
              <li>✓ Audio/visual quality checks</li>
              <li>✓ Translation service monitoring</li>
              <li>✓ Attendee flow management</li>
              <li>✓ Incident tracking</li>
              <li>✓ Real-time feedback collection</li>
            </ul>
          </div>
          
          <div className="bg-teal-50 p-4 rounded-lg border border-teal-300">
            <h4 className="font-bold text-teal-900 mb-3">Post-Event Checkpoints</h4>
            <ul className="text-sm space-y-2">
              <li>✓ Survey distribution</li>
              <li>✓ Satisfaction score analysis</li>
              <li>✓ Incident review</li>
              <li>✓ Deliverable verification</li>
              <li>✓ Lessons learned capture</li>
              <li>✓ Quality report completion</li>
            </ul>
          </div>
        </div>
      </div>

      <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-300 mt-6">
        <h4 className="font-semibold text-yellow-900 mb-3">Quality Roles & Responsibilities</h4>
        <div className="grid md:grid-cols-2 gap-3 text-sm">
          <div>
            <p><strong>Quality Manager:</strong> Timothy/Milne/Cloudy</p>
            <p className="text-gray-700">Overall quality oversight, material proofreading</p>
          </div>
          <div>
            <p><strong>Compliance Officer:</strong> TBD</p>
            <p className="text-gray-700">Content review, government compliance</p>
          </div>
          <div>
            <p><strong>Technical QA:</strong> Ivan/Adrian</p>
            <p className="text-gray-700">Equipment testing, technical standards</p>
          </div>
          <div>
            <p><strong>Operations QA:</strong> Jacky</p>
            <p className="text-gray-700">Process adherence, workflow monitoring</p>
          </div>
        </div>
      </div>
    </div>
  );
};

const ResourceEstimation = () => {
  const teams = [
    {
      team: 'Guest Management Team',
      lead: '周玉花',
      size: '7 members',
      roles: [
        { role: 'Team Lead', name: '周玉花', allocation: 'Full-time Nov-Dec' },
        { role: 'Guest Invitation & Speeches', name: 'Fannie, 郑东晨, Yolanda', allocation: '50% Nov-Dec' },
        { role: 'On-site Coordination', name: 'Lily, Heidi, 浩敏', allocation: 'Full-time Dec 12-14' },
        { role: 'Guest Escorts', name: 'Sophia, Catina, Fanny, Sidne', allocation: 'Full-time Dec 11-15' }
      ]
    },
    {
      team: 'Event Operations Team',
      lead: '林冬洁',
      size: '9 members',
      roles: [
        { role: 'Team Lead', name: '林冬洁', allocation: 'Full-time Nov-Dec' },
        { role: 'Materials Coordinator', name: '童丽云, Bonnie, Yoyo', allocation: '75% Nov-Dec' },
        { role: 'Host', name: 'Tracy', allocation: '50% Nov-Dec' },
        { role: 'Equipment', name: '杨鹏, 陈泳成', allocation: 'Full-time Dec 11-14' },
        { role: 'On-site Management', name: '温炬章, 陈经纬, 徐靖波', allocation: 'Full-time Dec 12-14' }
      ]
    },
    {
      team: 'Registration & Information',
      lead: '陈晓敏, Emily',
      size: '5 members',
      roles: [
        { role: 'Coordinators', name: '陈晓敏, Emily', allocation: 'Full-time Dec 12-14' },
        { role: 'Support Staff', name: '陈姗姗, 李姿瑜, 邬佩芸, 彭思萱, 柯蔓妮', allocation: 'Full-time Dec 13-14' }
      ]
    },
    {
      team: 'Photography & Videography',
      lead: 'Molly, 杨静怡',
      size: '5 members',
      roles: [
        { role: 'Coordinators', name: 'Molly, 杨静怡', allocation: 'Full-time Dec 13-14' },
        { role: 'Photographers', name: '高菲, 林佳仪, 吕柏诗', allocation: 'Full-time Dec 13-14' },
        { role: 'Professional Photographers', name: 'External (PR)', allocation: '1-2 per day' }
      ]
    },
    {
      team: 'Training Program Team',
      lead: 'Catina/Ivan',
      size: '8+ members',
      roles: [
        { role: 'Program Lead', name: 'Catina', allocation: 'Full-time Nov-Dec' },
        { role: 'Technical Coordinator', name: 'Ivan', allocation: 'Full-time Nov-Dec' },
        { role: 'Consultation Desk', name: '林承燊, 曾桂心, 杨德兴', allocation: 'Full-time Dec 13-14' },
        { role: 'Classroom Support', name: '雷子翰, 吉美晴, 曾桂心', allocation: 'Full-time Dec 13-14' },
        { role: 'Mobile Support', name: '陈小娟, Farren', allocation: 'Full-time Dec 13-14' }
      ]
    },
    {
      team: 'Exhibition Team',
      lead: '徐思奇',
      size: '5 members',
      roles: [
        { role: 'Team Lead', name: '徐思奇', allocation: 'Full-time Nov-Dec' },
        { role: 'Support Staff', name: '高菲, 林佳仪, 吕柏诗, 童丽云, 温炬章, 陈经纬', allocation: 'Part-time Dec 12-14' }
      ]
    },
    {
      team: 'Logistics Team',
      lead: '谭海秀',
      size: '3 members',
      roles: [
        { role: 'Team Lead', name: '谭海秀', allocation: 'Full-time Nov-Dec' },
        { role: 'Support Staff', name: 'Yoyo, 徐靖波', allocation: 'Full-time Nov-Dec' }
      ]
    },
    {
      team: 'Procurement Team',
      lead: 'Lily',
      size: '4 members',
      roles: [
        { role: 'Team Lead', name: 'Lily', allocation: 'Full-time Nov-Dec' },
        { role: 'Procurement', name: '李娟娟, 李思颖, 杨德兴', allocation: '50% Nov-Dec' }
      ]
    },
    {
      team: 'Data & Registration',
      lead: 'Lily',
      size: '2 members',
      roles: [
        { role: 'Team Lead', name: 'Lily', allocation: 'Part-time ongoing' },
        { role: 'Support', name: '陈晓敏', allocation: 'Part-time ongoing' }
      ]
    }
  ];

  const externalResources = [
    { category: 'Venues', resource: 'Venue rental (清华/力合/黄院)', quantity: '2 days + setup', timing: 'Dec 11-14' },
    { category: 'Technical', resource: 'AV equipment rental', quantity: 'Multiple rooms', timing: 'Dec 11-14' },
    { category: 'Technical', resource: 'Translation equipment (CPII)', quantity: '4 rooms', timing: 'Dec 13-14' },
    { category: 'Services', resource: 'Professional photography', quantity: '2-3 photographers', timing: 'Dec 13-14' },
    { category: 'Services', resource: 'Catering services', quantity: '900 people', timing: 'Dec 13-14' },
    { category: 'Services', resource: 'Livestreaming services', quantity: '2 days', timing: 'Dec 13-14' },
    { category: 'Transportation', resource: 'Guest shuttle buses', quantity: '2-3 vehicles', timing: 'Dec 12-15' },
    { category: 'Transportation', resource: 'Airport transfers', quantity: 'As needed', timing: 'Dec 11-15' },
    { category: 'Accommodation', resource: 'Hotel rooms', quantity: '20+ rooms', timing: 'Dec 12-14' },
    { category: 'Materials', resource: 'Printing services', quantity: 'Various materials', timing: 'Nov-Dec' },
    { category: 'Materials', resource: 'Installation services', quantity: 'Backdrops, signage', timing: 'Dec 11-12' }
  ];

  const resourceEstimate = [
    { resource: 'Project Management', hours: 400, people: 2, period: 'Nov-Dec' },
    { resource: 'Event Coordination', hours: 800, people: 10, period: 'Nov-Dec' },
    { resource: 'Content & Speaker Management', hours: 300, people: 5, period: 'Nov-Dec' },
    { resource: 'Marketing & PR', hours: 200, people: 3, period: 'Nov-Dec' },
    { resource: 'Technical Setup', hours: 250, people: 3, period: 'Nov 11-Dec 14' },
    { resource: 'On-site Operations', hours: 600, people: 40, period: 'Dec 12-14' },
    { resource: 'Post-Event', hours: 100, people: 5, period: 'Dec 15-30' }
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">Resource Estimation & Allocation</h2>
      
      <div className="grid md:grid-cols-4 gap-4 mb-6">
        <div className="bg-blue-100 p-4 rounded-lg border border-blue-300">
          <p className="text-sm text-blue-700 font-semibold">Total Team Members</p>
          <p className="text-3xl font-bold text-blue-900 mt-1">&gt;50+</p>
        </div>
        <div className="bg-green-100 p-4 rounded-lg border border-green-300">
          <p className="text-sm text-green-700 font-semibold">Operational Teams</p>
          <p className="text-3xl font-bold text-green-900 mt-1">9</p>
        </div>
        <div className="bg-purple-100 p-4 rounded-lg border border-purple-300">
          <p className="text-sm text-purple-700 font-semibold">Estimated Hours</p>
          <p className="text-3xl font-bold text-purple-900 mt-1">2,650+</p>
        </div>
        <div className="bg-orange-100 p-4 rounded-lg border border-orange-300">
          <p className="text-sm text-orange-700 font-semibold">Peak Capacity</p>
          <p className="text-3xl font-bold text-orange-900 mt-1">Dec 13-14</p>
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-xl font-semibold text-gray-800">Team Structure & Allocation</h3>
        {teams.map((team, idx) => (
          <div key={idx} className="border rounded-lg overflow-hidden">
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-3">
              <div className="flex justify-between items-center">
                <div>
                  <h4 className="font-bold text-lg">{team.team}</h4>
                  <p className="text-sm opacity-90">Lead: {team.lead} | Size: {team.size}</p>
                </div>
              </div>
            </div>
            <div className="divide-y">
              {team.roles.map((role, roleIdx) => (
                <div key={roleIdx} className="p-3 hover:bg-gray-50 grid md:grid-cols-3 gap-2">
                  <div className="font-medium text-gray-800">{role.role}</div>
                  <div className="text-gray-600">{role.name}</div>
                  <div className="text-sm text-orange-600 font-semibold">{role.allocation}</div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6">
        <h3 className="text-xl font-semibold text-gray-800 mb-4">External Resources Required</h3>
        <div className="overflow-x-auto">
          <table className="w-full border rounded-lg overflow-hidden">
            <thead className="bg-green-600 text-white">
              <tr>
                <th className="p-3 text-left">Category</th>
                <th className="p-3 text-left">Resource</th>
                <th className="p-3 text-left">Quantity</th>
                <th className="p-3 text-left">Timing</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {externalResources.map((item, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="p-3 font-semibold text-blue-700">{item.category}</td>
                  <td className="p-3">{item.resource}</td>
                  <td className="p-3">{item.quantity}</td>
                  <td className="p-3 text-sm text-orange-600">{item.timing}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="mt-6">
        <h3 className="text-xl font-semibold text-gray-800 mb-4">Resource Hour Estimates</h3>
        <div className="overflow-x-auto">
          <table className="w-full border rounded-lg overflow-hidden">
            <thead className="bg-purple-600 text-white">
              <tr>
                <th className="p-3 text-left">Resource Type</th>
                <th className="p-3 text-left">Estimated Hours</th>
                <th className="p-3 text-left">People</th>
                <th className="p-3 text-left">Period</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {resourceEstimate.map((item, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="p-3 font-medium">{item.resource}</td>
                  <td className="p-3 font-bold text-blue-700">{item.hours}h</td>
                  <td className="p-3">{item.people}</td>
                  <td className="p-3 text-sm text-gray-600">{item.period}</td>
                </tr>
              ))}
              <tr className="bg-gray-100 font-bold">
                <td className="p-3">TOTAL</td>
                <td className="p-3 text-blue-900">2,650+ hours</td>
                <td className="p-3">-</td>
                <td className="p-3">-</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-300 mt-6">
        <h4 className="font-semibold text-yellow-900 mb-3">Resource Management Strategy</h4>
        <ul className="text-sm space-y-2">
          <li>• <strong>Phased Allocation:</strong> Ramp up resources as event approaches</li>
          <li>• <strong>Peak Period:</strong> Maximum 40+ staff on-site Dec 13-14</li>
          <li>• <strong>Cross-Training:</strong> Staff trained for multiple roles for flexibility</li>
          <li>• <strong>Buffer Capacity:</strong> Floater team members for unexpected needs</li>
          <li>• <strong>Vendor Management:</strong> Early booking of critical external resources</li>
          <li>• <strong>Daily Check-ins:</strong> Resource utilization reviewed daily during peak periods</li>
        </ul>
      </div>

      <div className="bg-blue-50 p-4 rounded-lg border border-blue-300 mt-4">
        <h4 className="font-semibold text-blue-900 mb-3">Key Resource Dependencies</h4>
        <ul className="text-sm space-y-1">
          <li>• Venue confirmation blocks all physical setup activities</li>
          <li>• Speaker confirmations drive travel and accommodation bookings</li>
          <li>• Content approval gates printing and material production</li>
          <li>• Equipment availability determines technical capability</li>
          <li>• Staff availability impacts operational capacity during event</li>
        </ul>
      </div>
    </div>
  );
};

export default IAICCProjectPlan;
