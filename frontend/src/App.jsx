import React, { useState } from 'react';
import RubiksSolver from './components/RubiksSolver';
import SudokuSolver from './components/SudokuSolver';

// --- Global App Layout ---
const appStyle = {
  minHeight: '100vh', width: '100%',
  backgroundColor: '#111827', // Dark gray/black
  color: '#e5e7eb',
  fontFamily: '"Inter", sans-serif',
  display: 'flex', flexDirection: 'column', alignItems: 'center',
  background: 'linear-gradient(to bottom right, #111827, #1f2937)'
};

const headerStyle = {
  padding: '40px 20px', textAlign: 'center'
};

const titleStyle = {
  fontSize: '3rem', fontWeight: '800', lineHeight: '1',
  background: 'linear-gradient(to right, #60a5fa, #a78bfa, #f472b6)',
  WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
  marginBottom: '10px'
};

const gridStyle = {
  display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '30px',
  maxWidth: '800px', width: '100%', padding: '20px'
};

const cardButtonStyle = {
  backgroundColor: '#1f2937', borderRadius: '16px', padding: '30px',
  display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
  cursor: 'pointer', transition: 'transform 0.2s, box-shadow 0.2s',
  border: '1px solid #374151',
  boxShadow: '0 4px 6px rgba(0, 0, 0, 0.3)'
};

function App() {
  const [view, setView] = useState('home'); // 'home', 'rubiks', 'sudoku'

  return (
    <div style={appStyle}>
      {view === 'home' && (
        <>
          <header style={headerStyle}>
            <h1 style={titleStyle}>Puzzle Vision</h1>
            <p style={{ color: '#9ca3af', fontSize: '1.2rem' }}>AI-Powered AR Solver Suite</p>
          </header>

          <main style={gridStyle}>
            {/* Rubik's Card */}
            <div
              style={cardButtonStyle}
              onClick={() => setView('rubiks')}
              onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-5px)'; e.currentTarget.style.boxShadow = '0 10px 20px rgba(59, 130, 246, 0.2)'; }}
              onMouseLeave={e => { e.currentTarget.style.transform = 'none'; e.currentTarget.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.3)'; }}
            >
              <div style={{ fontSize: '4rem', marginBottom: '20px' }}>🎲</div>
              <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '10px', color: '#fff' }}>Rubik's Cube</h2>
              <p style={{ color: '#9ca3af', textAlign: 'center' }}>Scan faces, detect colors, and get a step-by-step 3D solution.</p>
              <div style={{ marginTop: '20px', color: '#60a5fa', fontWeight: 'bold' }}>Launch Solver →</div>
            </div>

            {/* Sudoku Card */}
            <div
              style={cardButtonStyle}
              onClick={() => setView('sudoku')}
              onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-5px)'; e.currentTarget.style.boxShadow = '0 10px 20px rgba(244, 114, 182, 0.2)'; }}
              onMouseLeave={e => { e.currentTarget.style.transform = 'none'; e.currentTarget.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.3)'; }}
            >
              <div style={{ fontSize: '4rem', marginBottom: '20px' }}>🧩</div>
              <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '10px', color: '#fff' }}>Sudoku</h2>
              <p style={{ color: '#9ca3af', textAlign: 'center' }}>Instant digit recognition and solving overlay for any grid.</p>
              <div style={{ marginTop: '20px', color: '#f472b6', fontWeight: 'bold' }}>Launch Solver →</div>
            </div>
          </main>

          <footer style={{ marginTop: 'auto', padding: '20px', color: '#4b5563', fontSize: '0.9rem' }}>
            © 2025 Antigravity AI
          </footer>
        </>
      )}

      {view === 'rubiks' && (
        <div style={{ padding: '20px', width: '100%', display: 'flex', justifyContent: 'center' }}>
          <RubiksSolver onBack={() => setView('home')} />
        </div>
      )}

      {view === 'sudoku' && (
        <div style={{ padding: '20px', width: '100%', display: 'flex', justifyContent: 'center' }}>
          <SudokuSolver onBack={() => setView('home')} />
        </div>
      )}
    </div>
  );
}

export default App;
