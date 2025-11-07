
import React from 'react';

import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';

import IAICCProjectPlan from './pages/iaicc-2025-project-plan';

import { Calendar, Home } from 'lucide-react';

 

function App() {

  return (

    <Router>

      <div className="min-h-screen bg-gray-50">

        <nav className="bg-white shadow-md sticky top-0 z-50">

          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

            <div className="flex justify-between items-center h-16">

              <div className="flex items-center">

                <Link to="/" className="flex items-center space-x-2 text-xl font-bold text-blue-600 hover:text-blue-700">

                  <Calendar className="h-6 w-6" />

                  <span>IAICC 2025 Project Management</span>

                </Link>

              </div>

              <div className="flex items-center space-x-4">

                <Link

                  to="/"

                  className="flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-gray-100"

                >

                  <Home className="h-4 w-4" />

                  <span>Dashboard</span>

                </Link>

              </div>

            </div>

          </div>

        </nav>

 

        <main>

          <Routes>

            <Route path="/" element={<IAICCProjectPlan />} />

            <Route path="/project" element={<IAICCProjectPlan />} />

          </Routes>

        </main>

      </div>

    </Router>

  );

}

 

export default App;

