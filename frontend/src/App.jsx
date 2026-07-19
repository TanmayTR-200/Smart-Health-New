import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import PHCDetail from './pages/PHCDetail';
import Recommendations from './pages/Recommendations';
import Alerts from './pages/Alerts';
import Simulation from './pages/Simulation';
import Navbar from './components/Navbar';
import { LanguageProvider } from './contexts/LanguageContext';

function App() {
  return (
    <LanguageProvider>
      <Router>
        <div className="app-bg min-h-screen">
          <Navbar />
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/phc/:id/:name?" element={<PHCDetail />} />
            <Route path="/redistribution" element={<Recommendations />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/simulation" element={<Simulation />} />
          </Routes>
        </div>
      </Router>
    </LanguageProvider>
  );
}

export default App;
